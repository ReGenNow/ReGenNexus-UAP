"""
ReGenNexus Core - Cryptography Module

This module provides cryptographic functions for the ReGenNexus Core security system.
It implements ECDH-384 for key exchange and AES-256-GCM for symmetric encryption.
"""

import os
import base64
import json
import logging
from typing import Dict, Any, Tuple, Optional, Union, List

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CryptoManager:
    """Cryptography manager for ReGenNexus Core."""
    
    def __init__(self):
        """Initialize the crypto manager."""
        self.private_keys = {}  # entity_id -> private_key
        self.public_keys = {}   # entity_id -> public_key
        self.shared_keys = {}   # (local_id, remote_id) -> shared_key
    
    async def generate_keypair(self, entity_id: str) -> Tuple[bytes, bytes]:
        """
        Generate an ECDH key pair for an entity.
        
        Args:
            entity_id: Entity ID to generate keys for
            
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        try:
            # Generate private key using P-384 curve
            private_key = ec.generate_private_key(
                ec.SECP384R1(),
                backend=default_backend()
            )
            
            # Get public key
            public_key = private_key.public_key()
            
            # Serialize keys to PEM format
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Store keys
            self.private_keys[entity_id] = private_key
            self.public_keys[entity_id] = public_key
            
            logger.debug(f"Generated key pair for {entity_id}")
            return private_pem, public_pem
            
        except Exception as e:
            logger.error(f"Error generating key pair: {e}")
            raise
    
    async def import_keypair(self, entity_id: str, private_key_pem: bytes, 
                           public_key_pem: Optional[bytes] = None) -> bool:
        """
        Import an existing key pair for an entity.
        
        Args:
            entity_id: Entity ID to import keys for
            private_key_pem: Private key in PEM format
            public_key_pem: Optional public key in PEM format (derived from private key if not provided)
            
        Returns:
            Boolean indicating success
        """
        try:
            # Load private key
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=default_backend()
            )
            
            # Get or load public key
            if public_key_pem:
                public_key = serialization.load_pem_public_key(
                    public_key_pem,
                    backend=default_backend()
                )
            else:
                public_key = private_key.public_key()
            
            # Store keys
            self.private_keys[entity_id] = private_key
            self.public_keys[entity_id] = public_key
            
            logger.debug(f"Imported key pair for {entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing key pair: {e}")
            return False
    
    async def import_public_key(self, entity_id: str, public_key_pem: bytes) -> bool:
        """
        Import a public key for an entity.
        
        Args:
            entity_id: Entity ID to import key for
            public_key_pem: Public key in PEM format
            
        Returns:
            Boolean indicating success
        """
        try:
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=default_backend()
            )
            
            # Store key
            self.public_keys[entity_id] = public_key
            
            logger.debug(f"Imported public key for {entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing public key: {e}")
            return False
    
    async def derive_shared_key(self, local_id: str, remote_id: str) -> Optional[bytes]:
        """
        Derive a shared key between two entities.
        
        Args:
            local_id: Local entity ID
            remote_id: Remote entity ID
            
        Returns:
            Derived shared key or None if error
        """
        try:
            # Check if we already have a shared key
            key_pair = (local_id, remote_id)
            if key_pair in self.shared_keys:
                return self.shared_keys[key_pair]
            
            # Check if we have the necessary keys
            if local_id not in self.private_keys:
                logger.error(f"No private key for {local_id}")
                return None
                
            if remote_id not in self.public_keys:
                logger.error(f"No public key for {remote_id}")
                return None
            
            # Get keys
            private_key = self.private_keys[local_id]
            public_key = self.public_keys[remote_id]
            
            # Derive shared key
            shared_secret = private_key.exchange(ec.ECDH(), public_key)
            
            # Derive key using HKDF
            derived_key = HKDF(
                algorithm=hashes.SHA384(),
                length=32,  # 256 bits for AES-256
                salt=None,
                info=b'ReGenNexus-ECDH-Key'
            ).derive(shared_secret)
            
            # Store shared key
            self.shared_keys[key_pair] = derived_key
            
            logger.debug(f"Derived shared key between {local_id} and {remote_id}")
            return derived_key
            
        except Exception as e:
            logger.error(f"Error deriving shared key: {e}")
            return None
    
    async def encrypt(self, plaintext: Union[str, bytes], key: bytes) -> Optional[Dict[str, str]]:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            plaintext: Data to encrypt (string or bytes)
            key: Encryption key (32 bytes)
            
        Returns:
            Dictionary with 'ciphertext', 'nonce', and 'tag' (all base64 encoded) or None if error
        """
        try:
            # Convert plaintext to bytes if it's a string
            if isinstance(plaintext, str):
                plaintext = plaintext.encode('utf-8')
            
            # Generate a random 96-bit nonce
            nonce = os.urandom(12)
            
            # Create AES-GCM cipher
            cipher = AESGCM(key)
            
            # Encrypt data
            ciphertext = cipher.encrypt(nonce, plaintext, None)
            
            # Encode as base64 for storage/transmission
            result = {
                'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
                'nonce': base64.b64encode(nonce).decode('utf-8')
            }
            
            logger.debug(f"Encrypted {len(plaintext)} bytes")
            return result
            
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return None
    
    async def decrypt(self, encrypted_data: Dict[str, str], key: bytes) -> Optional[bytes]:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            encrypted_data: Dictionary with 'ciphertext' and 'nonce' (base64 encoded)
            key: Decryption key (32 bytes)
            
        Returns:
            Decrypted data as bytes or None if error
        """
        try:
            # Decode base64 data
            ciphertext = base64.b64decode(encrypted_data['ciphertext'])
            nonce = base64.b64decode(encrypted_data['nonce'])
            
            # Create AES-GCM cipher
            cipher = AESGCM(key)
            
            # Decrypt data
            plaintext = cipher.decrypt(nonce, ciphertext, None)
            
            logger.debug(f"Decrypted {len(plaintext)} bytes")
            return plaintext
            
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return None
    
    async def encrypt_message(self, sender_id: str, recipient_id: str, 
                            message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt a message for secure transmission.
        
        Args:
            sender_id: Sender entity ID
            recipient_id: Recipient entity ID
            message: Message to encrypt
            
        Returns:
            Encrypted message
        """
        try:
            # Derive shared key
            shared_key = await self.derive_shared_key(sender_id, recipient_id)
            if not shared_key:
                raise ValueError(f"Could not derive shared key between {sender_id} and {recipient_id}")
            
            # Convert message to JSON
            message_json = json.dumps(message)
            
            # Encrypt message
            encrypted_data = await self.encrypt(message_json, shared_key)
            if not encrypted_data:
                raise ValueError("Could not encrypt message")
            
            # Create encrypted message
            encrypted_message = {
                'sender': sender_id,
                'recipient': recipient_id,
                'encrypted': True,
                'ciphertext': encrypted_data['ciphertext'],
                'nonce': encrypted_data['nonce'],
                'id': message.get('id', ''),
                'timestamp': message.get('timestamp', 0)
            }
            
            logger.debug(f"Encrypted message from {sender_id} to {recipient_id}")
            return encrypted_message
            
        except Exception as e:
            logger.error(f"Error encrypting message: {e}")
            # Return original message if encryption fails
            return message
    
    async def decrypt_message(self, recipient_id: str, 
                            encrypted_message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Decrypt an encrypted message.
        
        Args:
            recipient_id: Recipient entity ID
            encrypted_message: Encrypted message
            
        Returns:
            Decrypted message or None if error
        """
        try:
            # Check if message is encrypted
            if not encrypted_message.get('encrypted', False):
                return encrypted_message
            
            # Get sender ID
            sender_id = encrypted_message.get('sender', '')
            if not sender_id:
                raise ValueError("Encrypted message has no sender")
            
            # Derive shared key
            shared_key = await self.derive_shared_key(recipient_id, sender_id)
            if not shared_key:
                raise ValueError(f"Could not derive shared key between {recipient_id} and {sender_id}")
            
            # Extract encrypted data
            encrypted_data = {
                'ciphertext': encrypted_message.get('ciphertext', ''),
                'nonce': encrypted_message.get('nonce', '')
            }
            
            # Decrypt message
            decrypted_json = await self.decrypt(encrypted_data, shared_key)
            if not decrypted_json:
                raise ValueError("Could not decrypt message")
            
            # Parse JSON
            decrypted_message = json.loads(decrypted_json)
            
            logger.debug(f"Decrypted message from {sender_id} to {recipient_id}")
            return decrypted_message
            
        except Exception as e:
            logger.error(f"Error decrypting message: {e}")
            return None
    
    async def sign_data(self, entity_id: str, data: Union[str, bytes]) -> Optional[bytes]:
        """
        Sign data using the entity's private key.
        
        Args:
            entity_id: Entity ID to sign with
            data: Data to sign (string or bytes)
            
        Returns:
            Signature as bytes or None if error
        """
        try:
            # Convert data to bytes if it's a string
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Check if we have the private key
            if entity_id not in self.private_keys:
                logger.error(f"No private key for {entity_id}")
                return None
            
            # Get private key
            private_key = self.private_keys[entity_id]
            
            # Sign data
            signature = private_key.sign(
                data,
                ec.ECDSA(hashes.SHA384())
            )
            
            logger.debug(f"Signed {len(data)} bytes with {entity_id}'s key")
            return signature
            
        except Exception as e:
            logger.error(f"Error signing data: {e}")
            return None
    
    async def verify_signature(self, entity_id: str, data: Union[str, bytes], 
                             signature: bytes) -> bool:
        """
        Verify a signature using the entity's public key.
        
        Args:
            entity_id: Entity ID to verify with
            data: Data that was signed (string or bytes)
            signature: Signature to verify
            
        Returns:
            Boolean indicating whether the signature is valid
        """
        try:
            # Convert data to bytes if it's a string
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Check if we have the public key
            if entity_id not in self.public_keys:
                logger.error(f"No public key for {entity_id}")
                return False
            
            # Get public key
            public_key = self.public_keys[entity_id]
            
            # Verify signature
            public_key.verify(
                signature,
                data,
                ec.ECDSA(hashes.SHA384())
            )
            
            logger.debug(f"Verified signature from {entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
