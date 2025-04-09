# Docker Deployment Guide

This guide explains how to deploy ReGenNexus Core using Docker containers.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system
- Git (to clone the repository)

## Quick Start

The easiest way to get started with ReGenNexus Core in Docker is to use Docker Compose:

```bash
# Clone the repository
git clone https://github.com/ReGenNow/ReGenNexus.git
cd ReGenNexus

# Start the containers
docker-compose up -d
```

This will start the ReGenNexus Core server and a demo client.

## Configuration

### Environment Variables

The following environment variables can be set in the `docker-compose.yml` file:

- `REGENNEXUS_SECURITY_LEVEL`: Security level (1=basic, 2=enhanced, 3=maximum)
- `REGENNEXUS_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Volumes

The Docker Compose configuration mounts two volumes:

- `./data`: For persistent data storage
- `./config`: For configuration files

## Building Custom Images

### Building the Core Image

```bash
docker build -t regennexus-core:custom .
```

### Building the Demo Client

```bash
cd examples/simple_connection
docker build -t regennexus-demo-client:custom -f Dockerfile.client .
```

## Running Without Docker Compose

If you prefer to run the containers manually:

```bash
# Create a network
docker network create regennexus-network

# Run the core server
docker run -d --name regennexus-core \
  --network regennexus-network \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -e REGENNEXUS_SECURITY_LEVEL=2 \
  regennexus-core:0.1.1

# Run the demo client
docker run -d --name regennexus-demo-client \
  --network regennexus-network \
  -e REGENNEXUS_SERVER=regennexus-core:8000 \
  regennexus-demo-client:0.1.1
```

## Using with ROS

To use ReGenNexus Core with ROS in Docker, you'll need to build a custom image that includes ROS:

```dockerfile
FROM ros:humble

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Install the package in development mode
RUN pip3 install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV REGENNEXUS_SECURITY_LEVEL=2

# Command to run the application
CMD ["python3", "-m", "regennexus.server"]
```

## Using with Jetson Devices

For Jetson devices, you can use the NVIDIA L4T base image:

```dockerfile
FROM nvcr.io/nvidia/l4t-base:r32.7.1

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Install the package in development mode
RUN pip3 install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV REGENNEXUS_SECURITY_LEVEL=2

# Command to run the application
CMD ["python3", "-m", "regennexus.server"]
```

## Troubleshooting

### Container Won't Start

Check the logs:

```bash
docker logs regennexus-core
```

### Network Issues

Make sure the containers are on the same network:

```bash
docker network inspect regennexus-network
```

### Permission Issues

If you encounter permission issues with mounted volumes, check the ownership:

```bash
ls -la data config
```

You may need to adjust permissions:

```bash
chmod -R 777 data config
```

## Security Considerations

- The default configuration uses a non-root user inside the container
- Sensitive data should be stored in Docker secrets or environment variables
- Consider using a reverse proxy with TLS for production deployments
