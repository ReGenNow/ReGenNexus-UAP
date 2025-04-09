"""
ReGenNexus Core - Authentication Module

This module implements authentication features for ReGenNexus Core,
providing certificate-based and token-based authentication mechanisms.
"""

import os
import time
import uuid
import json
import base64
import logging
from typing import Dict, Tuple, Optional, Any, List
from datetime import datetime, timedelta
from Crypto.PublicKey import RSA, ECC
from Crypto.Hash import SHA384
from Crypto.Signature import DSS, pkcs1_15
from Crypto.Random import get_random_bytes

logger = logging.getLogger(__name__)

class AuthenticationManager:
    """
    Manages authentication for ReGenNexus Core.
    
    Provides certificate-based and token-based authentication mechanisms.
    """
    
    def __init__(self):
        """Initialize the authentication manager."""
        self.revoked_tokens = set()
        self.revoked_certificates = set()
        self._ca_cert = None
        self._ca_key = None
    
    async def setup_certificate_authority(self) -> Tuple[str, str]:
        """
        Set up a certificate authority for issuing certificates.
        
        Returns:
            Tuple of (ca_cert_pem, ca_private_key_pem)
        """
        # Generate a new ECC key pair for the CA
        ca_key = ECC.generate(curve='P-384')
        
        # Create a self-signed certificate
        ca_cert = {
            "version": 1,
            "serial_number": 1,
            "issuer": "ReGenNexus Core CA",
            "subject": "ReGenNexus Core CA",
            "not_before": int(time.time()),
            "not_after": int(time.time() + 365 * 24 * 60 * 60),  # Valid for 1 year
            "public_key": ca_key.public_key().export_key(format='PEM').decode('utf-8'),
            "extensions": {
                "basic_constraints": {
                    "ca": True,
                    "path_length": 0
                },
                "key_usage": ["cert_sign", "crl_sign"]
            }
        }
        
        # Sign the certificate with the CA key
        cert_data = json.dumps(ca_cert).encode('utf-8')
        h = SHA384.new(cert_data)
        signer = DSS.new(ca_key, 'fips-186-3')
        signature = signer.sign(h)
        
        # Add the signature to the certificate
        ca_cert["signature"] = signature.hex()
        ca_cert["signature_algorithm"] = "ecdsa-with-SHA384"
        
        # Convert to PEM format
        ca_cert_pem = "-----BEGIN CERTIFICATE-----\n"
        ca_cert_pem += base64.b64encode(json.dumps(ca_cert).encode('utf-8')).decode('utf-8')
        ca_cert_pem += "\n-----END CERTIFICATE-----"
        
        ca_key_pem = ca_key.export_key(format='PEM').decode('utf-8')
        
        # Store the CA certificate and key
        self._ca_cert = ca_cert_pem
        self._ca_key = ca_key_pem
        
        return ca_cert_pem, ca_key_pem
    
    async def issue_entity_certificate(self, entity_id: str, entity_public_key: bytes,
                                      ca_cert_pem: str, ca_private_key_pem: str) -> str:
        """
        Issue a certificate for an entity.
        
        Args:
            entity_id: Identifier of the entity
            entity_public_key: Public key of the entity
            ca_cert_pem: CA certificate in PEM format
            ca_private_key_pem: CA private key in PEM format
            
        Returns:
            Entity certificate in PEM format
        """
        # Import the CA key
        ca_key = ECC.import_key(ca_private_key_pem)
        
        # Parse the CA certificate
        ca_cert_data = base64.b64decode(ca_cert_pem.split("-----BEGIN CERTIFICATE-----\n")[1].split("\n-----END CERTIFICATE-----")[0])
        ca_cert = json.loads(ca_cert_data)
        
        # Create a certificate for the entity
        entity_cert = {
            "version": 1,
            "serial_number": int(time.time()),
            "issuer": ca_cert["subject"],
            "subject": f"entity:{entity_id}",
            "not_before": int(time.time()),
            "not_after": int(time.time() + 30 * 24 * 60 * 60),  # Valid for 30 days
            "public_key": base64.b64encode(entity_public_key).decode('utf-8'),
            "extensions": {
                "basic_constraints": {
                    "ca": False
                },
                "key_usage": ["digital_signature", "key_encipherment"],
                "entity_id": entity_id
            }
        }
        
        # Sign the certificate with the CA key
        cert_data = json.dumps(entity_cert).encode('utf-8')
        h = SHA384.new(cert_data)
        signer = DSS.new(ca_key, 'fips-186-3')
        signature = signer.sign(h)
        
        # Add the signature to the certificate
        entity_cert["signature"] = signature.hex()
        entity_cert["signature_algorithm"] = "ecdsa-with-SHA384"
        
        # Convert to PEM format
        entity_cert_pem = "-----BEGIN CERTIFICATE-----\n"
        entity_cert_pem += base64.b64encode(json.dumps(entity_cert).encode('utf-8')).decode('utf-8')
        entity_cert_pem += "\n-----END CERTIFICATE-----"
        
        return entity_cert_pem
    
    async def verify_entity_certificate(self, cert_pem: str, ca_cert_pem: str) -> bool:
        """
        Verify an entity certificate.
        
        Args:
            cert_pem: Entity certificate in PEM format
            ca_cert_pem: CA certificate in PEM format
            
        Returns:
            True if the certificate is valid, False otherwise
        """
        try:
            # Parse the certificates
            cert_data = base64.b64decode(cert_pem.split("-----BEGIN CERTIFICATE-----\n")[1].split("\n-----END CERTIFICATE-----")[0])
            cert = json.loads(cert_data)
            
            ca_cert_data = base64.b64decode(ca_cert_pem.split("-----BEGIN CERTIFICATE-----\n")[1].split("\n-----END CERTIFICATE-----")[0])
            ca_cert = json.loads(ca_cert_data)
            
            # Check if the certificate is revoked
            if cert["serial_number"] in self.revoked_certificates:
                logger.warning(f"Certificate {cert['serial_number']} is revoked")
                return False
            
            # Check the validity period
            current_time = int(time.time())
            if current_time < cert["not_before"] or current_time > cert["not_after"]:
                logger.warning(f"Certificate {cert['serial_number']} is not valid at the current time")
                return False
            
            # Check the issuer
            if cert["issuer"] != ca_cert["subject"]:
                logger.warning(f"Certificate {cert['serial_number']} has invalid issuer")
                return False
            
            # Verify the signature
            signature = bytes.fromhex(cert["signature"])
            cert_copy = cert.copy()
            del cert_copy["signature"]
            del cert_copy["signature_algorithm"]
            
            cert_data = json.dumps(cert_copy).encode('utf-8')
            h = SHA384.new(cert_data)
            
            ca_public_key = ECC.import_key(ca_cert["public_key"])
            verifier = DSS.new(ca_public_key, 'fips-186-3')
            
            try:
                verifier.verify(h, signature)
                return True
            except ValueError:
                logger.warning(f"Certificate {cert['serial_number']} has invalid signature")
                return False
            
        except Exception as e:
            logger.error(f"Error verifying certificate: {e}")
            return False
    
    async def verify_entity_authentication(self, entity_id: str, cert: str, public_key: bytes) -> bool:
        """
        Verify entity authentication.
        
        Args:
            entity_id: Identifier of the entity
            cert: Entity certificate
            public_key: Public key of the entity
            
        Returns:
            True if authentication is successful, False otherwise
        """
        if not self._ca_cert:
            logger.error("CA certificate not set up")
            return False
        
        # Verify the certificate
        if not await self.verify_entity_certificate(cert, self._ca_cert):
            return False
        
        # Parse the certificate
        cert_data = base64.b64decode(cert.split("-----BEGIN CERTIFICATE-----\n")[1].split("\n-----END CERTIFICATE-----")[0])
        cert_obj = json.loads(cert_data)
        
        # Check the entity ID
        if cert_obj["extensions"].get("entity_id") != entity_id:
            logger.warning(f"Certificate entity ID mismatch: {cert_obj['extensions'].get('entity_id')} != {entity_id}")
            return False
        
        # Check the public key
        cert_public_key = base64.b64decode(cert_obj["public_key"])
        if cert_public_key != public_key:
            logger.warning("Certificate public key mismatch")
            return False
        
        return True
    
    async def generate_token(self, entity_id: str, expiration_hours: int = 24,
                           claims: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate an authentication token.
        
        Args:
            entity_id: Identifier of the entity
            expiration_hours: Token validity in hours
            claims: Additional claims to include in the token
            
        Returns:
            Authentication token
        """
        token_id = str(uuid.uuid4())
        expiration = int(time.time() + expiration_hours * 3600)
        
        token_data = {
            "token_id": token_id,
            "entity_id": entity_id,
            "exp": expiration,
            "iat": int(time.time()),
            "claims": claims or {}
        }
        
        # Sign the token if we have a CA key
        if self._ca_key:
            ca_key = ECC.import_key(self._ca_key)
            token_bytes = json.dumps(token_data).encode('utf-8')
            h = SHA384.new(token_bytes)
            signer = DSS.new(ca_key, 'fips-186-3')
            signature = signer.sign(h)
            token_data["signature"] = signature.hex()
        
        # Encode the token
        token = base64.b64encode(json.dumps(token_data).encode('utf-8')).decode('utf-8')
        return token
    
    async def validate_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an authentication token.
        
        Args:
            token: Authentication token
            
        Returns:
            Tuple of (is_valid, entity_id)
        """
        try:
            # Decode the token
            token_data = json.loads(base64.b64decode(token).decode('utf-8'))
            
            # Check if the token is revoked
            if token_data["token_id"] in self.revoked_tokens:
                logger.warning(f"Token {token_data['token_id']} is revoked")
                return False, None
            
            # Check the expiration
            if token_data["exp"] < int(time.time()):
                logger.warning(f"Token {token_data['token_id']} is expired")
                return False, None
            
            # Verify the signature if present
            if "signature" in token_data and self._ca_cert:
                signature = bytes.fromhex(token_data["signature"])
                token_copy = token_data.copy()
                del token_copy["signature"]
                
                token_bytes = json.dumps(token_copy).encode('utf-8')
                h = SHA384.new(token_bytes)
                
                ca_cert_data = base64.b64decode(self._ca_cert.split("-----BEGIN CERTIFICATE-----\n")[1].split("\n-----END CERTIFICATE-----")[0])
                ca_cert = json.loads(ca_cert_data)
                ca_public_key = ECC.import_key(ca_cert["public_key"])
                
                verifier = DSS.new(ca_public_key, 'fips-186-3')
                try:
                    verifier.verify(h, signature)
                except ValueError:
                    logger.warning(f"Token {token_data['token_id']} has invalid signature")
                    return False, None
            
            return True, token_data["entity_id"]
            
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return False, None
    
    async def revoke_token(self, token_id: str):
        """
        Revoke an authentication token.
        
        Args:
            token_id: Identifier of the token to revoke
        """
        self.revoked_tokens.add(token_id)
        logger.info(f"Token {token_id} revoked")
    
    async def revoke_certificate(self, serial_number: int):
        """
        Revoke a certificate.
        
        Args:
            serial_number: Serial number of the certificate to revoke
        """
        self.revoked_certificates.add(serial_number)
        logger.info(f"Certificate {serial_number} revoked")
