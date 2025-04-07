# API Reference

This document provides a reference for the core API components of the ReGenNexus Universal Agent Protocol (UAP).

## Protocol Core

### Message

The `Message` class represents a communication unit between entities.

```python
class Message:
    def __init__(self, sender_id, recipient_id, content, intent, context_id=None):
        """
        Create a new message.
        
        Args:
            sender_id (str): Identifier of the sending entity
            recipient_id (str): Identifier of the receiving entity
            content (Union[str, dict]): The payload of the message
            intent (str): The purpose or type of the message
            context_id (str, optional): Identifier for the conversation context
        """
```

#### Properties:
- `message_id`: Unique identifier for the message
- `sender_id`: Identifier of the sending entity
- `recipient_id`: Identifier of the receiving entity
- `content`: The payload of the message (string or dictionary)
- `intent`: The purpose or type of the message
- `context_id`: Identifier for the conversation context
- `timestamp`: When the message was created

### Entity

The `Entity` class is an abstract base class for all entities in the system.

```python
class Entity:
    def __init__(self, entity_id):
        """
        Create a new entity.
        
        Args:
            entity_id (str): Unique identifier for this entity
        """
    
    async def process_message(self, message, context):
        """
        Process an incoming message and optionally return a response.
        
        Args:
            message (Message): The incoming message
            context (Context): The conversation context
            
        Returns:
            Optional[Message]: A response message or None
        """
```

## Registry

### Registry

The `Registry` class manages entity registration and message routing.

```python
class Registry:
    async def register_entity(self, entity):
        """
        Register an entity with the registry.
        
        Args:
            entity (Entity): The entity to register
        """
    
    async def unregister_entity(self, entity_id):
        """
        Unregister an entity from the registry.
        
        Args:
            entity_id (str): The ID of the entity to unregister
        """
    
    async def list_entities(self):
        """
        List all registered entities.
        
        Returns:
            List[str]: List of entity IDs
        """
    
    async def route_message(self, message):
        """
        Route a message to its recipient.
        
        Args:
            message (Message): The message to route
            
        Returns:
            Optional[Message]: A response message if one is generated
        """
```

## Context Management

### ContextManager

The `ContextManager` class manages conversation contexts.

```python
class ContextManager:
    async def create_context(self):
        """
        Create a new conversation context.
        
        Returns:
            Context: A new context object
        """
    
    async def get_context(self, context_id):
        """
        Retrieve a context by ID.
        
        Args:
            context_id (str): The ID of the context to retrieve
            
        Returns:
            Context: The requested context
        """
    
    async def add_message_to_context(self, message):
        """
        Add a message to a context.
        
        Args:
            message (Message): The message to add
        """
```

### Context

The `Context` class represents a conversation context.

```python
class Context:
    def __init__(self, context_id):
        """
        Create a new context.
        
        Args:
            context_id (str): Unique identifier for this context
        """
```

#### Properties:
- `context_id`: Unique identifier for the context
- `messages`: List of messages in this context
- `metadata`: Dictionary of metadata associated with this context
- `created_at`: When the context was created

## Security

### SecurityManager

The `SecurityManager` class provides security features for the protocol.

```python
class SecurityManager:
    def __init__(self, entity_id, private_key=None, public_key=None):
        """
        Create a new security manager.
        
        Args:
            entity_id (str): The entity this security manager belongs to
            private_key (str, optional): Private key for signing/encryption
            public_key (str, optional): Public key for verification/decryption
        """
    
    def sign_message(self, message):
        """
        Sign a message before sending.
        
        Args:
            message (Message): The message to sign
        """
    
    def authenticate_message(self, message):
        """
        Verify the authenticity of a message.
        
        Args:
            message (Message): The message to verify
            
        Raises:
            AuthenticationError: If authentication fails
        """
    
    def encrypt_content(self, content):
        """
        Encrypt message content.
        
        Args:
            content (Union[str, dict]): Content to encrypt
            
        Returns:
            dict: Encrypted content
        """
    
    def decrypt_content(self, encrypted_content):
        """
        Decrypt message content.
        
        Args:
            encrypted_content (dict): Encrypted content
            
        Returns:
            Union[str, dict]: Decrypted content
        """
```

## Error Handling

### Common Exceptions

- `ProtocolError`: Base class for all protocol errors
- `AuthenticationError`: Raised when message authentication fails
- `RoutingError`: Raised when a message cannot be routed
- `ContextError`: Raised when a context operation fails
