"""
ReGenNexus Core - Security Example

This example demonstrates the enhanced security features of ReGenNexus Core.
It shows how to use ECDH-384 encryption, certificate-based authentication, and policy-based access control.
"""

import asyncio
import json
import time
import logging
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import ReGenNexus Core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.security.security import SecurityManager
from src.security.auth import CertificateManager
from src.security.policy import PolicyManager
from src.protocol.protocol_core import UAP_Protocol
from src.registry.registry import Registry

async def demonstrate_key_exchange():
    """Demonstrate ECDH key exchange between two entities."""
    logger.info("Demonstrating ECDH key exchange...")
    
    # Generate key pairs for two entities
    alice_private = ec.generate_private_key(ec.SECP384R1())
    alice_public = alice_private.public_key()
    
    bob_private = ec.generate_private_key(ec.SECP384R1())
    bob_public = bob_private.public_key()
    
    # Serialize public keys (for demonstration)
    alice_public_bytes = alice_public.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    bob_public_bytes = bob_public.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    logger.info("Key pairs generated")
    logger.info(f"Alice's public key: {alice_public_bytes.decode('utf-8')[:64]}...")
    logger.info(f"Bob's public key: {bob_public_bytes.decode('utf-8')[:64]}...")
    
    # Perform key exchange
    logger.info("Performing key exchange...")
    
    # Alice derives shared key using Bob's public key
    alice_shared_key = alice_private.exchange(ec.ECDH(), bob_public)
    
    # Bob derives shared key using Alice's public key
    bob_shared_key = bob_private.exchange(ec.ECDH(), alice_public)
    
    # Derive final symmetric keys using HKDF
    alice_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'handshake data'
    ).derive(alice_shared_key)
    
    bob_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'handshake data'
    ).derive(bob_shared_key)
    
    # Check if keys match
    keys_match = alice_key == bob_key
    
    logger.info(f"Alice's derived key: {alice_key.hex()}")
    logger.info(f"Bob's derived key: {bob_key.hex()}")
    logger.info(f"Keys match: {keys_match}")
    
    return alice_key, bob_key, keys_match

async def demonstrate_certificate_auth(cert_manager):
    """Demonstrate certificate-based authentication."""
    logger.info("Demonstrating certificate-based authentication...")
    
    # Create certificates for two entities
    entity1_id = "entity1"
    entity2_id = "entity2"
    
    # Generate certificates
    entity1_cert = await cert_manager.create_self_signed_cert(
        entity_id=entity1_id,
        common_name="Entity One",
        organization="ReGenNexus Demo",
        validity_days=30
    )
    
    entity2_cert = await cert_manager.create_self_signed_cert(
        entity_id=entity2_id,
        common_name="Entity Two",
        organization="ReGenNexus Demo",
        validity_days=30
    )
    
    logger.info(f"Created certificate for {entity1_id}")
    logger.info(f"Created certificate for {entity2_id}")
    
    # Verify certificates
    entity1_valid = await cert_manager.verify_certificate(
        entity_id=entity1_id,
        certificate=entity1_cert['certificate']
    )
    
    entity2_valid = await cert_manager.verify_certificate(
        entity_id=entity2_id,
        certificate=entity2_cert['certificate']
    )
    
    logger.info(f"Entity1 certificate valid: {entity1_valid}")
    logger.info(f"Entity2 certificate valid: {entity2_valid}")
    
    # Simulate authentication
    logger.info("Simulating authentication flow...")
    
    # Entity1 sends a challenge to Entity2
    challenge = os.urandom(32)
    logger.info(f"Entity1 sends challenge: {challenge.hex()[:16]}...")
    
    # Entity2 signs the challenge with its private key
    signature = await cert_manager.sign_data(
        entity_id=entity2_id,
        data=challenge
    )
    logger.info(f"Entity2 signs challenge: {signature.hex()[:16]}...")
    
    # Entity1 verifies the signature using Entity2's certificate
    signature_valid = await cert_manager.verify_signature(
        entity_id=entity2_id,
        certificate=entity2_cert['certificate'],
        data=challenge,
        signature=signature
    )
    
    logger.info(f"Signature verification result: {signature_valid}")
    
    return entity1_cert, entity2_cert, signature_valid

async def demonstrate_policy_enforcement(policy_manager):
    """Demonstrate policy-based access control."""
    logger.info("Demonstrating policy-based access control...")
    
    # Create entities
    admin_id = "admin_entity"
    user_id = "user_entity"
    guest_id = "guest_entity"
    
    # Create resource
    resource_id = "protected_resource"
    
    # Define policies
    admin_policy = {
        "effect": "allow",
        "actions": ["read", "write", "delete"],
        "resources": [resource_id],
        "conditions": {}
    }
    
    user_policy = {
        "effect": "allow",
        "actions": ["read", "write"],
        "resources": [resource_id],
        "conditions": {}
    }
    
    guest_policy = {
        "effect": "allow",
        "actions": ["read"],
        "resources": [resource_id],
        "conditions": {}
    }
    
    # Set policies
    await policy_manager.set_policy(admin_id, "admin_policy", admin_policy)
    await policy_manager.set_policy(user_id, "user_policy", user_policy)
    await policy_manager.set_policy(guest_id, "guest_policy", guest_policy)
    
    logger.info("Policies set for all entities")
    
    # Check permissions
    admin_read = await policy_manager.check_permission(admin_id, "read", resource_id)
    admin_write = await policy_manager.check_permission(admin_id, "write", resource_id)
    admin_delete = await policy_manager.check_permission(admin_id, "delete", resource_id)
    
    user_read = await policy_manager.check_permission(user_id, "read", resource_id)
    user_write = await policy_manager.check_permission(user_id, "write", resource_id)
    user_delete = await policy_manager.check_permission(user_id, "delete", resource_id)
    
    guest_read = await policy_manager.check_permission(guest_id, "read", resource_id)
    guest_write = await policy_manager.check_permission(guest_id, "write", resource_id)
    guest_delete = await policy_manager.check_permission(guest_id, "delete", resource_id)
    
    logger.info("Permission check results:")
    logger.info(f"Admin - Read: {admin_read}, Write: {admin_write}, Delete: {admin_delete}")
    logger.info(f"User - Read: {user_read}, Write: {user_write}, Delete: {user_delete}")
    logger.info(f"Guest - Read: {guest_read}, Write: {guest_write}, Delete: {guest_delete}")
    
    # Simulate access attempts
    logger.info("Simulating access attempts...")
    
    # Admin attempts
    admin_read_result = await policy_manager.authorize(admin_id, "read", resource_id)
    admin_write_result = await policy_manager.authorize(admin_id, "write", resource_id)
    admin_delete_result = await policy_manager.authorize(admin_id, "delete", resource_id)
    
    # User attempts
    user_read_result = await policy_manager.authorize(user_id, "read", resource_id)
    user_write_result = await policy_manager.authorize(user_id, "write", resource_id)
    user_delete_result = await policy_manager.authorize(user_id, "delete", resource_id)
    
    # Guest attempts
    guest_read_result = await policy_manager.authorize(guest_id, "read", resource_id)
    guest_write_result = await policy_manager.authorize(guest_id, "write", resource_id)
    guest_delete_result = await policy_manager.authorize(guest_id, "delete", resource_id)
    
    logger.info("Access attempt results:")
    logger.info(f"Admin - Read: {admin_read_result}, Write: {admin_write_result}, Delete: {admin_delete_result}")
    logger.info(f"User - Read: {user_read_result}, Write: {user_write_result}, Delete: {user_delete_result}")
    logger.info(f"Guest - Read: {guest_read_result}, Write: {guest_write_result}, Delete: {guest_delete_result}")
    
    return {
        "admin": {"read": admin_read_result, "write": admin_write_result, "delete": admin_delete_result},
        "user": {"read": user_read_result, "write": user_write_result, "delete": user_delete_result},
        "guest": {"read": guest_read_result, "write": guest_write_result, "delete": guest_delete_result}
    }

async def demonstrate_secure_messaging(security_manager, cert_manager):
    """Demonstrate end-to-end encrypted messaging."""
    logger.info("Demonstrating end-to-end encrypted messaging...")
    
    # Create entities
    sender_id = "sender_entity"
    recipient_id = "recipient_entity"
    
    # Generate certificates for both entities
    sender_cert = await cert_manager.create_self_signed_cert(
        entity_id=sender_id,
        common_name="Sender Entity",
        organization="ReGenNexus Demo",
        validity_days=30
    )
    
    recipient_cert = await cert_manager.create_self_signed_cert(
        entity_id=recipient_id,
        common_name="Recipient Entity",
        organization="ReGenNexus Demo",
        validity_days=30
    )
    
    logger.info(f"Created certificates for {sender_id} and {recipient_id}")
    
    # Create a message
    original_message = {
        "sender": sender_id,
        "recipient": recipient_id,
        "intent": "secure_message",
        "payload": {
            "message": "This is a secret message!",
            "timestamp": time.time()
        }
    }
    
    logger.info(f"Original message: {json.dumps(original_message)}")
    
    # Encrypt the message
    encrypted_message = await security_manager.encrypt_message(
        sender_id=sender_id,
        recipient_id=recipient_id,
        message=original_message
    )
    
    logger.info(f"Encrypted message: {json.dumps(encrypted_message)}")
    
    # Decrypt the message
    decrypted_message = await security_manager.decrypt_message(
        recipient_id=recipient_id,
        encrypted_message=encrypted_message
    )
    
    logger.info(f"Decrypted message: {json.dumps(decrypted_message)}")
    
    # Verify the message integrity
    message_valid = (json.dumps(original_message, sort_keys=True) == 
                     json.dumps(decrypted_message, sort_keys=True))
    
    logger.info(f"Message integrity valid: {message_valid}")
    
    return original_message, encrypted_message, decrypted_message, message_valid

async def main():
    """Main function to demonstrate security features."""
    logger.info("Starting security example")
    
    # Initialize security components
    security_manager = SecurityManager()
    cert_manager = CertificateManager()
    policy_manager = PolicyManager()
    
    await security_manager.initialize()
    await cert_manager.initialize()
    await policy_manager.initialize()
    
    logger.info("Security components initialized")
    
    try:
        # Demonstrate ECDH key exchange
        logger.info("\n=== ECDH Key Exchange ===")
        alice_key, bob_key, keys_match = await demonstrate_key_exchange()
        
        # Demonstrate certificate-based authentication
        logger.info("\n=== Certificate-Based Authentication ===")
        entity1_cert, entity2_cert, signature_valid = await demonstrate_certificate_auth(cert_manager)
        
        # Demonstrate policy-based access control
        logger.info("\n=== Policy-Based Access Control ===")
        policy_results = await demonstrate_policy_enforcement(policy_manager)
        
        # Demonstrate secure messaging
        logger.info("\n=== End-to-End Encrypted Messaging ===")
        original_msg, encrypted_msg, decrypted_msg, msg_valid = await demonstrate_secure_messaging(
            security_manager, cert_manager
        )
        
        # Summary
        logger.info("\n=== Security Demo Summary ===")
        logger.info(f"ECDH Key Exchange: {'Success' if keys_match else 'Failed'}")
        logger.info(f"Certificate Authentication: {'Success' if signature_valid else 'Failed'}")
        logger.info(f"Policy Enforcement: {'Success' if policy_results['admin']['delete'] and not policy_results['guest']['write'] else 'Failed'}")
        logger.info(f"Secure Messaging: {'Success' if msg_valid else 'Failed'}")
        
    finally:
        # Clean up
        await security_manager.shutdown()
        await cert_manager.shutdown()
        await policy_manager.shutdown()
        logger.info("Security components shut down")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
