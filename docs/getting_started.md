# Getting Started with ReGenNexus Core

This guide will help you get started with ReGenNexus Core, an open-source implementation of the Universal Agent Protocol (UAP) for seamless communication between digital entities.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

### Installing from GitHub

```bash
# Clone the repository
git clone https://github.com/ReGenNow/ReGenNexus.git
cd ReGenNexus

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Installing with pip

```bash
pip install regennexus
```

## Basic Usage

### Creating a Simple Client

```python
import asyncio
from regennexus.protocol.client import UAP_Client
from regennexus.protocol.message import UAP_Message

async def main():
    # Create a client
    client = UAP_Client(entity_id="my_agent", registry_url="localhost:8000")
    
    # Connect to the registry
    await client.connect()
    
    # Send a message
    message = UAP_Message(
        sender="my_agent",
        recipient="target_device",
        intent="command",
        payload={"action": "turn_on", "parameters": {"device": "light"}}
    )
    await client.send_message(message)
    
    # Keep the client running
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Handling Messages

```python
# Register a message handler
async def handle_message(message):
    print(f"Received message: {message.payload}")
    
    # Respond to the message
    if message.intent == "query":
        response = UAP_Message(
            sender=client.entity_id,
            recipient=message.sender,
            intent="response",
            payload={"status": "success", "data": {"temperature": 22.5}},
            context_id=message.context_id
        )
        await client.send_message(response)

client.register_message_handler(handle_message)
```

## Running the Registry Server

ReGenNexus Core includes a registry server that facilitates entity discovery and message routing:

```bash
# Start the registry server
python -m regennexus.registry.server --host 0.0.0.0 --port 8000
```

## Using Security Features

ReGenNexus Core includes robust security features:

```python
from regennexus.security.crypto import generate_keypair
from regennexus.security.auth import create_certificate

# Generate a keypair for secure communication
private_key, public_key = generate_keypair()

# Create a certificate for authentication
certificate = create_certificate(
    entity_id="my_agent",
    public_key=public_key,
    valid_days=365
)

# Create a secure client
secure_client = UAP_Client(
    entity_id="my_agent",
    registry_url="localhost:8000",
    private_key=private_key,
    certificate=certificate
)
```

## Working with Device Plugins

ReGenNexus Core includes plugins for various devices:

```python
from regennexus.plugins.raspberry_pi import RaspberryPiPlugin

# Create a Raspberry Pi plugin
rpi_plugin = RaspberryPiPlugin()

# Register the plugin with a client
client.register_plugin(rpi_plugin)

# Use the plugin
gpio_status = await client.execute_plugin_action(
    plugin_id="raspberry_pi",
    action="read_gpio",
    parameters={"pin": 18}
)
```

## Next Steps

- Explore the [examples directory](../examples/) for more detailed examples
- Read the [API Reference](api_reference.md) for detailed documentation
- Learn about [security features](security.md) for secure communication
- Discover [device integration](device_integration.md) capabilities
- Explore [ROS integration](ros_integration.md) for robotics applications
- Learn about the [Azure Bridge](azure_bridge.md) for cloud connectivity
