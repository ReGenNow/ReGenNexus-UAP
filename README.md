# ReGenNexus Core - Universal Agent Protocol

ReGenNexus Core is an open-source implementation of the Universal Agent Protocol (UAP) developed by ReGen Designs LLC. It provides a standardized communication framework for digital entities to interact seamlessly.

## Core Features

- **Message Protocol**: Standardized message format for entity communication
- **Entity Registry**: Discovery and registration system for digital entities
- **Context Management**: Conversation state and history tracking
- **Basic Security**: Authentication and encryption for secure communication

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/ReGenNow/ReGenNexus.git
cd ReGenNexus

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Quick Example

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

## Documentation

- [Getting Started Guide](docs/getting_started.md)
- [Core Protocol Documentation](docs/core_protocol.md)
- [API Reference](docs/api_reference.md)
- [Containerization Guide](docs/containerization.md)

## Examples

The `examples/` directory contains several examples demonstrating different aspects of the protocol:

- **Simple Connection**: Basic protocol usage and tutorial
- **Multi-Agent**: Communication between multiple entities
- **Patterns**: Event-driven communication patterns
- **Security**: Authentication and encryption features

## Docker Support

ReGenNexus Core includes Docker support for easy deployment:

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.core.yml up
```

See the [Containerization Guide](docs/containerization.md) for more details.

## Contributing

We welcome contributions to the ReGenNexus Core! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the development roadmap and future plans.

## License

ReGenNexus Core is released under the MIT License. See [LICENSE](LICENSE) for details.

## About ReGen Designs LLC

ReGen Designs LLC is focused on creating next-generation communication protocols for digital entities. The ReGenNexus project aims to establish a universal standard for agent communication.
