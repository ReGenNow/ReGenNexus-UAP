# Getting Started with ReGenNexus Core

This guide will help you get started with the ReGenNexus Universal Agent Protocol (UAP) Core. The Core version provides the essential protocol features needed to build communication systems between digital entities.

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install from Source
```bash
# Clone the repository
git clone https://github.com/ReGenNow/ReGenNexus.git
cd ReGenNexus

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Docker Installation
For containerized deployment, see the [Docker Deployment Guide](deployment/docker_core.md).

## Core Concepts

### 1. Messages
Messages are the fundamental unit of communication in ReGenNexus UAP. Each message contains:
- Sender and recipient identifiers
- Content payload (text or structured data)
- Intent (purpose of the message)
- Context identifier (conversation grouping)

### 2. Entities
Entities are the participants in the communication system. Each entity:
- Has a unique identifier
- Can process incoming messages
- Can generate response messages
- Implements application-specific logic

### 3. Registry
The registry manages all entities in the system:
- Keeps track of available entities
- Routes messages to the correct recipients
- Handles entity registration and discovery

### 4. Context
The context manager maintains conversation state:
- Groups related messages together
- Provides conversation history
- Manages conversation lifecycle

## Quick Start Example

Here's a simple example to get you started:

```python
import asyncio
from regennexus.protocol.protocol_core import Message, Entity
from regennexus.registry.registry import Registry
from regennexus.context.context_manager import ContextManager

# Create a simple entity
class SimpleEntity(Entity):
    def __init__(self, entity_id, name):
        super().__init__(entity_id)
        self.name = name
        
    async def process_message(self, message, context):
        print(f"{self.name} received: {message.content}")
        return Message(
            sender_id=self.id,
            recipient_id=message.sender_id,
            content=f"Response from {self.name}",
            intent="response",
            context_id=message.context_id
        )

async def main():
    # Create registry and context manager
    registry = Registry()
    context_manager = ContextManager()
    
    # Create and register entities
    entity_a = SimpleEntity("entity-a", "Entity A")
    entity_b = SimpleEntity("entity-b", "Entity B")
    await registry.register_entity(entity_a)
    await registry.register_entity(entity_b)
    
    # Create context
    context = await context_manager.create_context()
    
    # Send a message
    message = Message(
        sender_id=entity_a.id,
        recipient_id=entity_b.id,
        content="Hello from Entity A!",
        intent="greeting",
        context_id=context.id
    )
    
    # Route the message
    response = await registry.route_message(message)
    if response:
        await registry.route_message(response)

if __name__ == "__main__":
    asyncio.run(main())
```

## Learning More

To deepen your understanding of the ReGenNexus UAP Core:

1. **Explore the Examples**: The `examples/` directory contains several working examples:
   - `simple_connection/protocol_basics_tutorial.py`: Step-by-step introduction to core concepts
   - `multi_agent/multi_entity_communication.py`: Multiple entity communication
   - `patterns/event_driven_example.py`: Event-driven communication patterns
   - `security/basic_security_example.py`: Authentication and encryption features

2. **Read the Documentation**: The `docs/` directory contains detailed documentation:
   - `core_protocol.md`: Detailed protocol specification
   - `deployment/docker_core.md`: Docker deployment guide

3. **Contribute**: See the `CONTRIBUTING.md` file for guidelines on contributing to the project.

## Future Extensions

The ReGenNexus UAP Core is designed to be extensible. Future premium extensions will include:
- Connection Manager for application integration
- Device Detection Framework for hardware discovery
- LLM Integration for intelligent adapter generation

These premium features will build upon the core protocol while maintaining compatibility.
