# ReGenNexus Core - Containerization Guide

This guide explains how to use the Docker container capabilities of ReGenNexus Core UAP.

## Container Overview

The ReGenNexus Core container provides a ready-to-use environment with all core protocol components:
- Protocol message handling
- Entity registry
- Context management
- Basic security features

The container is designed to be lightweight and focused on the core protocol functionality without premium features.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) (optional, but recommended)

## Quick Start

The easiest way to get started with ReGenNexus Core in a container:

```bash
# Clone the repository
git clone https://github.com/ReGenNow/ReGenNexus.git
cd ReGenNexus

# Build and run with Docker Compose
docker-compose -f docker-compose.core.yml up
```

This will build the container and run the basic protocol example.

## Running Different Examples

The container includes several examples that demonstrate different aspects of the core protocol:

```bash
# Run the protocol basics tutorial
docker-compose -f docker-compose.core.yml run --rm regennexus-core python examples/simple_connection/protocol_basics_tutorial.py

# Run the multi-entity communication example
docker-compose -f docker-compose.core.yml run --rm regennexus-core python examples/multi_agent/multi_entity_communication.py

# Run the event-driven example
docker-compose -f docker-compose.core.yml run --rm regennexus-core python examples/patterns/event_driven_example.py

# Run the security example
docker-compose -f docker-compose.core.yml run --rm regennexus-core python examples/security/basic_security_example.py
```

## Using Your Own Code

You can mount your own code into the container:

```bash
# Mount your code directory and run your script
docker-compose -f docker-compose.core.yml run --rm \
  -v $(pwd)/my_code:/app/my_code \
  regennexus-core python /app/my_code/my_script.py
```

## Building Without Docker Compose

If you prefer to use Docker directly:

```bash
# Build the image
docker build -f Dockerfile.core -t regennexus-core .

# Run a container
docker run -it --rm regennexus-core
```

## Customizing the Container

### Modifying the Dockerfile

You can create your own Dockerfile based on the provided Dockerfile.core:

```dockerfile
FROM regennexus-core:latest

# Add your custom dependencies
RUN pip install your-package

# Copy your application code
COPY your_app /app/your_app

# Set your entrypoint
CMD ["python", "/app/your_app/main.py"]
```

### Creating a Custom Docker Compose File

You can create a custom Docker Compose file for your specific needs:

```yaml
version: '3'
services:
  my-regennexus-app:
    build:
      context: .
      dockerfile: Dockerfile.core
    volumes:
      - ./my_app:/app/my_app
    environment:
      - PYTHONPATH=/app
      - MY_ENV_VAR=value
    command: python my_app/main.py
```

## Container Structure

The container includes:

- `/app/regennexus/protocol`: Core protocol implementation
- `/app/regennexus/registry`: Entity registry system
- `/app/regennexus/context`: Context management
- `/app/regennexus/security`: Basic security features
- `/app/examples`: Example implementations

## Troubleshooting

If you encounter issues:

1. Ensure Docker is properly installed and running
2. Verify that you have the latest version of the code
3. Check container logs with `docker logs <container_id>`
4. Make sure your Python code is compatible with the container environment

## Next Steps

After getting the container running:

1. Explore the examples to understand the protocol
2. Try modifying the examples to fit your use case
3. Develop your own entities that use the protocol
4. Contribute improvements to the core protocol
