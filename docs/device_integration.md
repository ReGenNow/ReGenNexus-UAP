# Device Integration Guide

This document provides detailed information about integrating various devices with ReGenNexus Core.

## Supported Devices

ReGenNexus Core supports the following device types:

1. **Raspberry Pi** - All models including Pi 4, Pi 3, Pi Zero, and Pi Pico
2. **Arduino** - Arduino Uno, Mega, Nano, and compatible boards
3. **NVIDIA Jetson** - Jetson Nano, Orin Nano, and AGX series
4. **ESP32** - ESP32 and ESP8266 microcontrollers
5. **Generic IoT Devices** - Devices supporting MQTT, HTTP, or other standard protocols

## Device Plugin Architecture

ReGenNexus Core uses a plugin architecture for device integration:

```
src/plugins/
├── base.py           # Base plugin interface
├── raspberry_pi.py   # Raspberry Pi support
├── arduino.py        # Arduino support
├── jetson.py         # Jetson support
├── esp32.py          # ESP32 support
└── iot.py            # Generic IoT device support
```

Each plugin implements the base `Plugin` interface and provides device-specific functionality.

## Raspberry Pi Integration

### Basic Setup

```python
from regennexus.plugins.raspberry_pi import RaspberryPiPlugin
from regennexus.protocol.client import UAP_Client

# Create a Raspberry Pi plugin
rpi_plugin = RaspberryPiPlugin()

# Create a client
client = UAP_Client(entity_id="rpi_agent", registry_url="localhost:8000")

# Register the plugin with the client
client.register_plugin(rpi_plugin)

# Connect to the registry
await client.connect()
```

### GPIO Control

```python
# Set a GPIO pin as output
await client.execute_plugin_action(
    plugin_id="raspberry_pi",
    action="setup_gpio",
    parameters={"pin": 18, "mode": "OUTPUT"}
)

# Set the pin high
await client.execute_plugin_action(
    plugin_id="raspberry_pi",
    action="write_gpio",
    parameters={"pin": 18, "value": 1}
)

# Read a GPIO pin
result = await client.execute_plugin_action(
    plugin_id="raspberry_pi",
    action="read_gpio",
    parameters={"pin": 17}
)
print(f"Pin 17 value: {result['value']}")
```

### Camera Access

```python
# Capture an image
result = await client.execute_plugin_action(
    plugin_id="raspberry_pi",
    action="capture_image",
    parameters={"resolution": (1280, 720), "format": "jpeg"}
)

# Save the image
with open("captured_image.jpg", "wb") as f:
    f.write(result["image_data"])
```

### Sensor Integration

```python
# Read from a DHT22 temperature/humidity sensor
result = await client.execute_plugin_action(
    plugin_id="raspberry_pi",
    action="read_dht22",
    parameters={"pin": 4}
)
print(f"Temperature: {result['temperature']}°C, Humidity: {result['humidity']}%")
```

## Arduino Integration

### Serial Communication

```python
from regennexus.plugins.arduino import ArduinoPlugin

# Create an Arduino plugin
arduino_plugin = ArduinoPlugin(port="/dev/ttyUSB0", baud_rate=9600)

# Register the plugin with a client
client.register_plugin(arduino_plugin)

# Send a command to the Arduino
await client.execute_plugin_action(
    plugin_id="arduino",
    action="send_command",
    parameters={"command": "LED_ON"}
)

# Read data from the Arduino
result = await client.execute_plugin_action(
    plugin_id="arduino",
    action="read_data"
)
print(f"Received: {result['data']}")
```

### Pin Control

```python
# Set a pin mode
await client.execute_plugin_action(
    plugin_id="arduino",
    action="set_pin_mode",
    parameters={"pin": 13, "mode": "OUTPUT"}
)

# Write to a digital pin
await client.execute_plugin_action(
    plugin_id="arduino",
    action="digital_write",
    parameters={"pin": 13, "value": 1}
)

# Read from an analog pin
result = await client.execute_plugin_action(
    plugin_id="arduino",
    action="analog_read",
    parameters={"pin": "A0"}
)
print(f"Analog value: {result['value']}")
```

## NVIDIA Jetson Integration

### Basic Setup

```python
from regennexus.plugins.jetson import JetsonPlugin

# Create a Jetson plugin
jetson_plugin = JetsonPlugin()

# Register the plugin with a client
client.register_plugin(jetson_plugin)
```

### Camera Access

```python
# Capture a video frame
result = await client.execute_plugin_action(
    plugin_id="jetson",
    action="capture_frame",
    parameters={"camera_id": 0, "width": 1280, "height": 720}
)

# Process the frame with CUDA acceleration
processed_frame = await client.execute_plugin_action(
    plugin_id="jetson",
    action="cuda_process",
    parameters={
        "frame": result["frame"],
        "operation": "edge_detection"
    }
)

# Save the processed frame
with open("processed_frame.jpg", "wb") as f:
    f.write(processed_frame["data"])
```

### AI Inference

```python
# Load a TensorRT model
await client.execute_plugin_action(
    plugin_id="jetson",
    action="load_model",
    parameters={"model_path": "/path/to/model.trt"}
)

# Run inference on an image
result = await client.execute_plugin_action(
    plugin_id="jetson",
    action="run_inference",
    parameters={"image_path": "/path/to/image.jpg"}
)

# Process the results
for detection in result["detections"]:
    print(f"Detected {detection['class']} with confidence {detection['confidence']}")
```

## ESP32 Integration

### WiFi Configuration

```python
from regennexus.plugins.esp32 import ESP32Plugin

# Create an ESP32 plugin
esp32_plugin = ESP32Plugin(port="/dev/ttyUSB1", baud_rate=115200)

# Register the plugin with a client
client.register_plugin(esp32_plugin)

# Configure WiFi
await client.execute_plugin_action(
    plugin_id="esp32",
    action="configure_wifi",
    parameters={"ssid": "MyNetwork", "password": "MyPassword"}
)
```

### Sensor Reading

```python
# Read from a BME280 sensor
result = await client.execute_plugin_action(
    plugin_id="esp32",
    action="read_bme280"
)
print(f"Temperature: {result['temperature']}°C")
print(f"Humidity: {result['humidity']}%")
print(f"Pressure: {result['pressure']} hPa")
```

### Deep Sleep Management

```python
# Put the ESP32 into deep sleep
await client.execute_plugin_action(
    plugin_id="esp32",
    action="deep_sleep",
    parameters={"sleep_time": 60}  # seconds
)
```

## Generic IoT Device Integration

### MQTT Device

```python
from regennexus.plugins.iot import MQTTDevicePlugin

# Create an MQTT device plugin
mqtt_plugin = MQTTDevicePlugin(
    broker="mqtt.example.com",
    port=1883,
    client_id="regennexus_client"
)

# Register the plugin with a client
client.register_plugin(mqtt_plugin)

# Subscribe to a topic
await client.execute_plugin_action(
    plugin_id="mqtt_device",
    action="subscribe",
    parameters={"topic": "sensors/temperature"}
)

# Publish to a topic
await client.execute_plugin_action(
    plugin_id="mqtt_device",
    action="publish",
    parameters={
        "topic": "actuators/light",
        "message": "ON",
        "qos": 1
    }
)
```

### HTTP Device

```python
from regennexus.plugins.iot import HTTPDevicePlugin

# Create an HTTP device plugin
http_plugin = HTTPDevicePlugin(base_url="http://device.local")

# Register the plugin with a client
client.register_plugin(http_plugin)

# Send a GET request
result = await client.execute_plugin_action(
    plugin_id="http_device",
    action="get",
    parameters={"endpoint": "/status"}
)
print(f"Device status: {result['response']}")

# Send a POST request
result = await client.execute_plugin_action(
    plugin_id="http_device",
    action="post",
    parameters={
        "endpoint": "/control",
        "data": {"command": "power", "value": "on"}
    }
)
```

## Creating Custom Device Plugins

You can create custom plugins for your specific devices by extending the base `Plugin` class:

```python
from regennexus.plugins.base import Plugin

class MyCustomDevicePlugin(Plugin):
    def __init__(self, device_path):
        super().__init__(plugin_id="my_custom_device")
        self.device_path = device_path
        
    async def initialize(self):
        # Initialize your device
        self.device = await self._connect_to_device(self.device_path)
        return True
        
    async def execute_action(self, action, parameters=None):
        if action == "custom_action":
            # Implement your custom action
            result = await self._perform_custom_action(parameters)
            return {"status": "success", "data": result}
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
    async def shutdown(self):
        # Clean up resources
        await self.device.close()
        return True
        
    async def _connect_to_device(self, path):
        # Implement device connection logic
        pass
        
    async def _perform_custom_action(self, parameters):
        # Implement custom action logic
        pass
```

## Best Practices

1. **Error Handling**
   - Always implement proper error handling in device plugins
   - Return meaningful error messages
   - Implement reconnection logic for network devices

2. **Resource Management**
   - Release resources in the `shutdown` method
   - Use context managers for resource acquisition
   - Implement timeouts for device operations

3. **Security**
   - Validate all input parameters
   - Use secure communication protocols
   - Implement access control for sensitive operations

4. **Performance**
   - Use asynchronous I/O for device communication
   - Implement caching for frequently accessed data
   - Optimize resource usage for constrained devices

5. **Compatibility**
   - Test with multiple device versions
   - Document hardware requirements
   - Provide fallback mechanisms for missing features
