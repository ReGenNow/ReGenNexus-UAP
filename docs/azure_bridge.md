# Azure Bridge Documentation

This document provides detailed information about using the Azure Bridge component in ReGenNexus Core to integrate with Azure IoT services.

## Overview

The Azure Bridge is a standalone component that enables ReGenNexus Core to communicate with Azure IoT Hub and other Azure services. It provides a simple, secure way to connect your devices and applications to the Azure cloud.

## Features

- **IoT Hub Connectivity**: Connect devices to Azure IoT Hub
- **Device Twin Support**: Synchronize device properties with Azure
- **Direct Method Handling**: Respond to commands from the cloud
- **Message Routing**: Send and receive messages between devices and the cloud
- **Secure Authentication**: Support for SAS tokens and X.509 certificates

## Prerequisites

Before using the Azure Bridge, ensure you have:

1. An Azure account with an active subscription
2. An Azure IoT Hub instance
3. ReGenNexus Core installed
4. Python 3.8 or higher

## Installation

The Azure Bridge is included with ReGenNexus Core. To use it, you'll need to install the Azure IoT SDK:

```bash
pip install azure-iot-device
```

## Basic Usage

### Initializing the Azure Bridge

```python
import asyncio
from regennexus.bridges.azure_bridge import AzureBridge
from regennexus.protocol.client import UAP_Client

async def main():
    # Create an Azure bridge with a connection string
    connection_string = "HostName=your-hub.azure-devices.net;DeviceId=your-device;SharedAccessKey=your-key"
    azure_bridge = AzureBridge(connection_string=connection_string)
    
    # Initialize the bridge
    await azure_bridge.initialize()
    
    # Create a ReGenNexus client
    client = UAP_Client(entity_id="azure_agent", registry_url="localhost:8000")
    
    # Register the bridge with the client
    client.register_bridge(azure_bridge)
    
    # Connect to the registry
    await client.connect()
    
    # Keep the client running
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Using X.509 Certificate Authentication

```python
# Create an Azure bridge with X.509 certificate authentication
azure_bridge = AzureBridge(
    hostname="your-hub.azure-devices.net",
    device_id="your-device",
    x509_cert_file="device_cert.pem",
    x509_key_file="device_key.pem"
)
```

## Sending Telemetry

### Basic Telemetry

```python
# Send telemetry data to Azure IoT Hub
await client.execute_bridge_action(
    bridge_id="azure_bridge",
    action="send_telemetry",
    parameters={
        "data": {
            "temperature": 25.6,
            "humidity": 60.2,
            "pressure": 1013.25
        }
    }
)
```

### Batched Telemetry

```python
# Send batched telemetry data
await client.execute_bridge_action(
    bridge_id="azure_bridge",
    action="send_batch_telemetry",
    parameters={
        "messages": [
            {"temperature": 25.6, "timestamp": "2025-04-09T12:00:00Z"},
            {"temperature": 25.7, "timestamp": "2025-04-09T12:01:00Z"},
            {"temperature": 25.8, "timestamp": "2025-04-09T12:02:00Z"}
        ]
    }
)
```

## Device Twin

### Getting Device Twin

```python
# Get the device twin
twin = await client.execute_bridge_action(
    bridge_id="azure_bridge",
    action="get_twin"
)

print(f"Reported properties: {twin['reported_properties']}")
print(f"Desired properties: {twin['desired_properties']}")
```

### Updating Reported Properties

```python
# Update reported properties
await client.execute_bridge_action(
    bridge_id="azure_bridge",
    action="update_reported_properties",
    parameters={
        "properties": {
            "firmware_version": "1.2.3",
            "location": {
                "latitude": 47.63962,
                "longitude": -122.12781
            },
            "last_maintenance": "2025-03-15T14:30:00Z"
        }
    }
)
```

### Handling Desired Property Changes

```python
# Register a handler for desired property changes
@client.message_handler(intent="azure_desired_properties")
async def handle_desired_properties(message):
    properties = message.payload
    print(f"Received desired properties: {properties}")
    
    # Process the properties
    if "led_state" in properties:
        # Update LED state
        led_state = properties["led_state"]
        # ...
        
        # Update reported properties to acknowledge the change
        await client.execute_bridge_action(
            bridge_id="azure_bridge",
            action="update_reported_properties",
            parameters={
                "properties": {
                    "led_state": led_state,
                    "led_state_updated": "2025-04-09T16:30:00Z"
                }
            }
        )
```

## Direct Methods

### Registering Direct Method Handlers

```python
# Register a handler for direct methods
@client.message_handler(intent="azure_direct_method")
async def handle_direct_method(message):
    method_name = message.payload["method_name"]
    payload = message.payload["payload"]
    request_id = message.payload["request_id"]
    
    print(f"Received direct method: {method_name}")
    print(f"Payload: {payload}")
    
    # Process the method
    if method_name == "reboot":
        # Perform reboot operation
        # ...
        
        # Send response
        await client.execute_bridge_action(
            bridge_id="azure_bridge",
            action="respond_to_method",
            parameters={
                "request_id": request_id,
                "response": {
                    "status": 200,
                    "payload": {
                        "message": "Reboot initiated",
                        "estimated_time": 30
                    }
                }
            }
        )
    else:
        # Method not supported
        await client.execute_bridge_action(
            bridge_id="azure_bridge",
            action="respond_to_method",
            parameters={
                "request_id": request_id,
                "response": {
                    "status": 404,
                    "payload": {
                        "message": f"Method {method_name} not supported"
                    }
                }
            }
        )
```

## Cloud-to-Device Messages

### Receiving Cloud-to-Device Messages

```python
# Register a handler for cloud-to-device messages
@client.message_handler(intent="azure_c2d_message")
async def handle_c2d_message(message):
    c2d_message = message.payload
    print(f"Received cloud-to-device message: {c2d_message['data']}")
    print(f"Properties: {c2d_message['properties']}")
    
    # Process the message
    # ...
    
    # Complete the message (acknowledge receipt)
    await client.execute_bridge_action(
        bridge_id="azure_bridge",
        action="complete_message",
        parameters={
            "message_id": c2d_message["message_id"]
        }
    )
```

## File Upload

### Uploading Files to Azure Storage

```python
# Upload a file to Azure Storage via IoT Hub
result = await client.execute_bridge_action(
    bridge_id="azure_bridge",
    action="upload_file",
    parameters={
        "file_path": "/path/to/data.csv",
        "content_type": "text/csv"
    }
)

print(f"File uploaded: {result['success']}")
print(f"Blob URI: {result['blob_uri']}")
```

## Advanced Features

### Device Provisioning Service Integration

```python
# Create an Azure bridge with DPS
azure_bridge = AzureBridge(
    provisioning=True,
    id_scope="0ne00000000",
    registration_id="my-device",
    symmetric_key="your-symmetric-key"
)

# Or with X.509 certificates
azure_bridge = AzureBridge(
    provisioning=True,
    id_scope="0ne00000000",
    registration_id="my-device",
    x509_cert_file="device_cert.pem",
    x509_key_file="device_key.pem"
)
```

### Edge Module Communication

```python
# Create an Azure bridge for an IoT Edge module
azure_bridge = AzureBridge(
    edge_module=True,
    connection_string="HostName=your-hub.azure-devices.net;DeviceId=your-edge-device;ModuleId=your-module;SharedAccessKey=your-key"
)

# Send a message to another module
await client.execute_bridge_action(
    bridge_id="azure_bridge",
    action="send_module_message",
    parameters={
        "target_module": "filterModule",
        "data": {
            "sensor_reading": 25.6
        }
    }
)
```

### Digital Twins Integration

```python
# Update a digital twin
await client.execute_bridge_action(
    bridge_id="azure_bridge",
    action="update_digital_twin",
    parameters={
        "properties": {
            "temperature": 25.6,
            "humidity": 60.2
        }
    }
)
```

## Configuration Options

The Azure Bridge supports various configuration options:

```python
# Full configuration example
azure_bridge = AzureBridge(
    # Connection options (choose one)
    connection_string="your-connection-string",  # Option 1
    hostname="your-hub.azure-devices.net",       # Option 2 (with device_id and auth)
    device_id="your-device",
    
    # Authentication options (choose one if using hostname)
    sas_key="your-sas-key",                      # Option A
    x509_cert_file="device_cert.pem",            # Option B
    x509_key_file="device_key.pem",
    
    # DPS options
    provisioning=False,                          # Use DPS for provisioning
    id_scope="0ne00000000",                      # Required for DPS
    registration_id="my-device",                 # Required for DPS
    
    # IoT Edge options
    edge_module=False,                           # Is this an Edge module
    module_id="your-module",                     # Required for Edge modules
    
    # Protocol options
    protocol="mqtt",                             # mqtt, mqtt_ws, amqp, amqp_ws
    
    # Message options
    model_id="dtmi:com:example:Thermostat;1",    # DTDL model ID for PnP
    content_type="application/json",             # Default content type
    content_encoding="utf-8",                    # Default encoding
    
    # Retry options
    retry_total=3,                               # Total retry attempts
    retry_backoff_factor=0.5,                    # Backoff factor
    
    # Misc options
    connect_timeout=30,                          # Connection timeout (seconds)
    keep_alive=60                                # Keep-alive interval (seconds)
)
```

## Best Practices

1. **Security**
   - Use X.509 certificates for production environments
   - Rotate SAS keys regularly
   - Store credentials securely

2. **Reliability**
   - Implement proper error handling
   - Use retry logic for transient failures
   - Monitor connection status

3. **Performance**
   - Batch telemetry messages when possible
   - Use appropriate message properties
   - Optimize message size

4. **Device Twin**
   - Keep reported properties up to date
   - Handle desired property changes promptly
   - Use version information for synchronization

5. **Direct Methods**
   - Respond to method requests quickly
   - Use appropriate status codes
   - Include detailed information in responses

## Troubleshooting

### Common Issues

1. **Connection Problems**
   - Verify connection string or credentials
   - Check network connectivity
   - Ensure the device is registered in IoT Hub

2. **Authentication Failures**
   - Check SAS token expiration
   - Verify certificate validity
   - Ensure the device ID matches

3. **Message Delivery Issues**
   - Check message size limits
   - Verify message format
   - Monitor IoT Hub quotas and throttling

### Debugging Tools

```python
# Enable debug logging
await client.execute_bridge_action(
    bridge_id="azure_bridge",
    action="set_log_level",
    parameters={"level": "debug"}
)

# Get bridge status
status = await client.execute_bridge_action(
    bridge_id="azure_bridge",
    action="get_status"
)
print(f"Bridge status: {status}")

# Test connectivity
test_result = await client.execute_bridge_action(
    bridge_id="azure_bridge",
    action="test_connectivity"
)
print(f"Connectivity test: {test_result}")
```
