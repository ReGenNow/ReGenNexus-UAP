# Core Protocol Documentation

This document provides a simplified overview of the ReGenNexus Universal Adapter Protocol (UAP) core features, focusing on the essential components available in the open-source version.

## Overview

The ReGenNexus UAP is a communication protocol designed to enable seamless interaction between different digital entities. The core protocol provides the foundation for message exchange, entity registration, and context management.

## Core Components

### 1. Message Protocol

Messages are the fundamental unit of communication in ReGenNexus UAP. Each message contains:

- `sender_id`: Identifier of the sending entity
- `recipient_id`: Identifier of the receiving entity
- `content`: The payload of the message (can be text or structured data)
- `intent`: The purpose or type of the message
- `context_id`: Identifier for the conversation context
- `timestamp`: When the message was created

Example message creation:
```python
message = Message(
    sender_id="entity-a",
    recipient_id="entity-b",
    content="Hello, world!",
    intent="greeting",
    context_id="conversation-123"
)
```

### 2. Entity Registry

The registry manages all entities in the system and handles message routing:

- Register entities with the system
- Discover entities by capability or type
- Route messages between entities
- Maintain entity status information

Example entity registration:
```python
registry = Registry()
await registry.register_entity(my_entity)
```

### 3. Context Management

The context manager maintains conversation state:

- Create new conversation contexts
- Add messages to existing contexts
- Retrieve conversation history
- Manage context lifecycle

Example context usage:
```python
context_manager = ContextManager()
context = await context_manager.create_context()
conversation = await context_manager.get_context(context.id)
```

### 4. Basic Security

Core security features include:

- Message authentication
- Basic encryption
- Access control for entity registration

## Using the Core Protocol

The basic workflow for using the protocol:

1. Create entities that implement the `Entity` interface
2. Register entities with the registry
3. Create a context for the conversation
4. Send messages between entities
5. Process responses

See the examples directory for complete working examples.

## Future Capabilities

The core protocol is designed to be extensible. Future premium extensions will include:

- Connection Manager for application integration
- Device Detection Framework for hardware discovery
- LLM Integration for intelligent adapter generation

These premium features will build upon the core protocol while maintaining compatibility.

## Next Steps

- Explore the examples directory for working code
- Read the API reference for detailed specifications
- Join the community discussions to share your use cases
