"""
Basic Security Example - Authentication and Encryption
This example demonstrates the core security features of the ReGenNexus UAP
without any LLM integration. It shows how to:
1. Set up authentication for entities
2. Implement encrypted communication
3. Handle security credentials
4. Manage secure connections between entities

This example focuses on the security aspects of the protocol that are
essential for production deployments.
"""

import asyncio
import json
from regennexus.protocol.protocol_core import Message, Entity, Intent
from regennexus.registry.registry import Registry
from regennexus.context.context_manager import ContextManager
from regennexus.security.security_manager import SecurityManager, AuthenticationError

# Create a secure entity that requires authentication
class SecureEntity(Entity):
    def __init__(self, entity_id, name, security_manager):
        super().__init__(entity_id)
        self.name = name
        self.security_manager = security_manager
        self.authorized_entities = set()
        
    async def process_message(self, message, context):
        """Process an incoming message with security checks"""
        # First verify the message is from an authenticated source
        try:
            # This will raise an exception if authentication fails
            self.security_manager.authenticate_message(message)
            print(f"{self.name} received authenticated message from {message.sender_id}")
            
            # Handle authentication requests
            if message.intent == "security.authenticate":
                credentials = message.content.get("credentials", {})
                success = await self._authenticate_entity(message.sender_id, credentials)
                
                return Message(
                    sender_id=self.id,
                    recipient_id=message.sender_id,
                    content={"success": success},
                    intent="security.authenticate.response",
                    context_id=message.context_id
                )
            
            # For all other intents, check if the sender is authorized
            if message.sender_id not in self.authorized_entities:
                print(f"Unauthorized access attempt from {message.sender_id}")
                return Message(
                    sender_id=self.id,
                    recipient_id=message.sender_id,
                    content={"error": "Unauthorized access"},
                    intent="security.error",
                    context_id=message.context_id
                )
            
            # Process normal messages from authorized entities
            if message.intent == "query.data":
                # Decrypt the content if it's encrypted
                decrypted_content = self.security_manager.decrypt_content(message.content)
                
                # Create a response with sensitive data
                sensitive_data = {
                    "user_id": "user123",
                    "access_level": "admin",
                    "api_key": "sk_test_abcdefghijklmnopqrstuvwxyz"
                }
                
                # Encrypt the response content
                encrypted_content = self.security_manager.encrypt_content(sensitive_data)
                
                return Message(
                    sender_id=self.id,
                    recipient_id=message.sender_id,
                    content=encrypted_content,
                    intent="response.data",
                    context_id=message.context_id
                )
            
        except AuthenticationError as e:
            print(f"Authentication error: {str(e)}")
            return Message(
                sender_id=self.id,
                recipient_id=message.sender_id,
                content={"error": str(e)},
                intent="security.error",
                context_id=message.context_id
            )
        
        return None
    
    async def _authenticate_entity(self, entity_id, credentials):
        """Authenticate an entity based on credentials"""
        # In a real implementation, this would validate against a secure store
        # For this example, we'll use a simple check
        if credentials.get("api_key") == "valid_api_key_123":
            self.authorized_entities.add(entity_id)
            print(f"Entity {entity_id} successfully authenticated")
            return True
        return False

# Client entity that will communicate with the secure entity
class ClientEntity(Entity):
    def __init__(self, entity_id, name, security_manager, api_key=None):
        super().__init__(entity_id)
        self.name = name
        self.security_manager = security_manager
        self.api_key = api_key
        self.authenticated = False
        self.responses = []
        
    async def authenticate_with(self, secure_entity_id, registry, context_id):
        """Authenticate with a secure entity"""
        credentials = {"api_key": self.api_key} if self.api_key else {}
        
        auth_message = Message(
            sender_id=self.id,
            recipient_id=secure_entity_id,
            content={"credentials": credentials},
            intent="security.authenticate",
            context_id=context_id
        )
        
        # Sign the message before sending
        self.security_manager.sign_message(auth_message)
        
        response = await registry.route_message(auth_message)
        if response:
            self.responses.append(response)
            if response.content.get("success", False):
                self.authenticated = True
                print(f"{self.name} successfully authenticated with {secure_entity_id}")
            else:
                print(f"{self.name} failed to authenticate with {secure_entity_id}")
        
        return self.authenticated
    
    async def request_data(self, secure_entity_id, registry, context_id):
        """Request data from a secure entity"""
        if not self.authenticated:
            print(f"{self.name} is not authenticated, cannot request data")
            return False
        
        # Create a query with some parameters
        query_params = {"request_type": "user_data", "timestamp": 1617293932}
        
        # Encrypt the content
        encrypted_content = self.security_manager.encrypt_content(query_params)
        
        query_message = Message(
            sender_id=self.id,
            recipient_id=secure_entity_id,
            content=encrypted_content,
            intent="query.data",
            context_id=context_id
        )
        
        # Sign the message before sending
        self.security_manager.sign_message(query_message)
        
        response = await registry.route_message(query_message)
        if response:
            self.responses.append(response)
            
            if response.intent == "response.data":
                # Decrypt the response content
                try:
                    decrypted_content = self.security_manager.decrypt_content(response.content)
                    print(f"{self.name} received encrypted data:")
                    print(json.dumps(decrypted_content, indent=2))
                    return True
                except Exception as e:
                    print(f"Error decrypting content: {str(e)}")
            else:
                print(f"{self.name} received error: {response.content.get('error', 'Unknown error')}")
        
        return False
    
    async def process_message(self, message, context):
        """Process responses from the secure entity"""
        self.responses.append(message)
        return None

async def main():
    # Create security managers with encryption keys
    # In a real implementation, these would be securely stored and managed
    server_security = SecurityManager(
        entity_id="secure-server",
        private_key="server_private_key_123",
        public_key="server_public_key_456"
    )
    
    client_security = SecurityManager(
        entity_id="client-a",
        private_key="client_private_key_789",
        public_key="client_public_key_012"
    )
    
    # Exchange public keys (in a real system, this would use a secure key exchange protocol)
    server_security.add_public_key("client-a", client_security.public_key)
    client_security.add_public_key("secure-server", server_security.public_key)
    
    # Create ReGenNexus components
    registry = Registry()
    context_manager = ContextManager()
    
    # Create and register entities
    secure_server = SecureEntity("secure-server", "Secure Server", server_security)
    client_a = ClientEntity("client-a", "Client A", client_security, api_key="valid_api_key_123")
    client_b = ClientEntity("client-b", "Client B", client_security, api_key="invalid_key")
    
    await registry.register_entity(secure_server)
    await registry.register_entity(client_a)
    await registry.register_entity(client_b)
    
    # Create a context for our secure conversation
    context = await context_manager.create_context()
    
    print("\n=== Demonstrating Authentication ===")
    # Client A authenticates with valid credentials
    authenticated_a = await client_a.authenticate_with(secure_server.id, registry, context.id)
    
    # Client B tries to authenticate with invalid credentials
    authenticated_b = await client_b.authenticate_with(secure_server.id, registry, context.id)
    
    print("\n=== Demonstrating Secure Data Exchange ===")
    # Client A requests data (should succeed)
    if authenticated_a:
        await client_a.request_data(secure_server.id, registry, context.id)
    
    # Client B requests data (should fail due to authentication)
    if not authenticated_b:
        print("\nClient B attempting to access data without proper authentication...")
        await client_b.request_data(secure_server.id, registry, context.id)
    
    # Print conversation history
    conversation = await context_manager.get_context(context.id)
    print("\n=== Secure Conversation History ===")
    for i, msg in enumerate(conversation.messages):
        print(f"Message {i+1}: {msg.intent} from {msg.sender_id} to {msg.recipient_id}")

if __name__ == "__main__":
    asyncio.run(main())
