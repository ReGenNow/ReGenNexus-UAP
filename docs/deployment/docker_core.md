# Docker Deployment Guide for ReGenNexus Core

This guide explains how to deploy the ReGenNexus UAP Core using Docker containers.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system
- Basic familiarity with command line operations

## Quick Start

The easiest way to get started with ReGenNexus UAP Core in a container is to use Docker Compose:

```bash
# Clone the repository
git clone https://github.com/ReGenNow/ReGenNexus.git
cd ReGenNexus

# Build and run the container
docker-compose -f docker-compose.core.yml up
```

This will build the container and run the basic protocol example.

## Running Different Examples

You can modify the `docker-compose.core.yml` file to run different examples:

```yaml
version: '3'

services:
  regennexus-core:
    build:
      context: .
      dockerfile: Dockerfile.core
    volumes:
      - ./examples:/app/examples
    environment:
      - PYTHONPATH=/app
    command: python examples/multi_agent/multi_entity_communication.py
```

## Building the Container Manually

If you prefer to build and run the container manually:

```bash
# Build the container
docker build -f Dockerfile.core -t regennexus-core .

# Run the container
docker run -it --rm regennexus-core
```

## Customizing the Container

You can customize the container by:

1. Modifying the Dockerfile.core file
2. Creating your own docker-compose file
3. Mounting your own examples or code

Example of running with your own code:

```bash
docker run -it --rm -v $(pwd)/my_examples:/app/my_examples regennexus-core python /app/my_examples/my_script.py
```

## Container Structure

The container includes:

- Core protocol components (protocol, registry, context, security)
- Example code
- Python dependencies

It does not include premium features such as:
- LLM integration
- Connection Manager
- Device Detection Framework

## Troubleshooting

If you encounter issues:

1. Ensure Docker is properly installed and running
2. Check that ports are not already in use
3. Verify that you have the latest version of the code
4. Check logs with `docker logs <container_id>`

## Next Steps

After getting the container running:

1. Explore the examples to understand the protocol
2. Try modifying the examples to fit your use case
3. Develop your own entities that use the protocol
4. Contribute improvements to the core protocol
