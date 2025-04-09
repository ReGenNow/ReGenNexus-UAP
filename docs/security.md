# Security Guide

This document provides detailed information about the security features in ReGenNexus Core and how to implement them in your applications.

## Security Architecture

ReGenNexus Core implements a comprehensive security architecture with the following components:

1. **ECDH-384 Encryption** - Elliptic Curve Diffie-Hellman key exchange with the P-384 curve
2. **AES-256-GCM** - Authenticated encryption for message payloads
3. **Certificate-Based Authentication** - Entity verification using X.509 certificates
4. **Policy-Based Access Control** - Fine-grained permission management
5. **Secure Key Management** - Comprehensive key lifecycle management

## Encryption

ReGenNexus Core uses ECDH-384 for key exchange and AES-256-GCM for symmetric encryption of message payloads.

### Generating Keys

```python
from regennexus.security.crypto import generate_keypair

# Generate a new ECDH-384 keypair
private_key, public_key = generate_keypair()

# Save the keys for future use
with open("private_key.pem", "w") as f:
    f.write(private_key)
    
with open("public_key.pem", "w") as f:
    f.write(public_key)
```

### Encrypting and Decrypting Data

```python
from regennexus.security.crypto import encrypt, decrypt

# Encrypt data using the recipient's public key
encrypted_data = encrypt("Sensitive information", recipient_public_key)

# Decrypt data using your private key
decrypted_data = decrypt(encrypted_data, private_key)
```

## Authentication

ReGenNexus Core uses certificate-based authentication to verify entity identities.

### Creating Certificates

```python
from regennexus.security.auth import create_certificate

# Create a certificate for your entity
certificate = create_certificate(
    entity_id="my_agent",
    public_key=public_key,
    valid_days=365
)

# Save the certificate for future use
with open("certificate.pem", "w") as f:
    f.write(certificate)
```

### Verifying Certificates

```python
from regennexus.security.auth import verify_certificate

# Verify a certificate
cert_info = verify_certificate(certificate)
if cert_info:
    print(f"Certificate is valid for entity: {cert_info['entity_id']}")
    print(f"Valid until: {cert_info['valid_until']}")
else:
    print("Certificate is invalid")
```

## Access Control

ReGenNexus Core implements policy-based access control to manage permissions.

### Creating Policies

```python
from regennexus.security.policy import Policy, Permission

# Create a policy for an entity
policy = Policy(entity_id="my_agent")

# Add permissions to the policy
policy.add_permission(Permission(
    resource="device:light",
    action="control",
    effect="allow"
))

policy.add_permission(Permission(
    resource="device:camera",
    action="view",
    effect="allow"
))

# Save the policy
policy.save("my_agent_policy.json")
```

### Checking Permissions

```python
from regennexus.security.policy import PolicyManager

# Create a policy manager
policy_manager = PolicyManager()

# Load policies
policy_manager.load_policy("my_agent_policy.json")

# Check if an action is allowed
if policy_manager.is_allowed("my_agent", "device:light", "control"):
    print("Action is allowed")
else:
    print("Action is denied")
```

## Secure Client Configuration

To create a fully secure client, combine all security features:

```python
from regennexus.protocol.client import UAP_Client
from regennexus.security.crypto import generate_keypair
from regennexus.security.auth import create_certificate
from regennexus.security.policy import Policy, Permission

# Generate keys
private_key, public_key = generate_keypair()

# Create a certificate
certificate = create_certificate(
    entity_id="my_agent",
    public_key=public_key,
    valid_days=365
)

# Create a policy
policy = Policy(entity_id="my_agent")
policy.add_permission(Permission(
    resource="device:*",
    action="*",
    effect="allow"
))

# Create a secure client
secure_client = UAP_Client(
    entity_id="my_agent",
    registry_url="localhost:8000",
    private_key=private_key,
    certificate=certificate,
    policy=policy
)

# Connect securely
await secure_client.connect()
```

## Security Best Practices

1. **Key Management**
   - Store private keys securely, never expose them
   - Rotate keys periodically (recommended: every 90 days)
   - Use a secure key storage solution for production

2. **Certificate Management**
   - Verify certificates before trusting entities
   - Implement certificate revocation checks
   - Use short-lived certificates for sensitive operations

3. **Policy Management**
   - Follow the principle of least privilege
   - Regularly audit and update policies
   - Use specific resources and actions instead of wildcards

4. **Secure Communication**
   - Always use encrypted connections
   - Verify the identity of communication partners
   - Implement message integrity checks

5. **Secure Deployment**
   - Use secure environment variables for sensitive information
   - Implement network segmentation
   - Regularly update dependencies

## Advanced Security Features

### Post-Quantum Readiness

ReGenNexus Core includes experimental support for post-quantum cryptography:

```python
from regennexus.security.crypto import generate_hybrid_keypair

# Generate a hybrid keypair (ECDH + Kyber)
private_key, public_key = generate_hybrid_keypair()
```

### Hardware Security Module Integration

For production environments, ReGenNexus Core supports integration with hardware security modules:

```python
from regennexus.security.crypto import HSMKeyManager

# Initialize HSM key manager
hsm = HSMKeyManager(hsm_provider="pkcs11", slot_id=0)

# Generate keys in HSM
key_id = hsm.generate_key()

# Create a client using HSM keys
secure_client = UAP_Client(
    entity_id="my_agent",
    registry_url="localhost:8000",
    hsm=hsm,
    key_id=key_id
)
```

## Security Troubleshooting

### Common Issues

1. **Certificate Validation Failures**
   - Check certificate expiration date
   - Verify the certificate chain
   - Ensure the entity ID matches

2. **Encryption Failures**
   - Verify the public key format
   - Check for key compatibility
   - Ensure the data is properly formatted

3. **Permission Denied Errors**
   - Check policy definitions
   - Verify the entity ID in the request
   - Ensure the policy is loaded correctly

### Debugging Security Issues

ReGenNexus Core includes security debugging tools:

```python
from regennexus.security.debug import SecurityDebugger

# Create a security debugger
debugger = SecurityDebugger(verbose=True)

# Test a security operation
result = debugger.test_encryption(
    data="Test message",
    public_key=public_key,
    private_key=private_key
)

print(result.success)  # True if successful
print(result.details)  # Detailed information about the operation
```
