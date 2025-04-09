# ReGenNexus Core Addons

This package contains additional files and enhancements for the ReGenNexus Core Universal Agent Protocol.

## Contents

### Source Files

- **Protocol Enhancements**
  - `src/protocol/client.py` - Enhanced client implementation
  - `src/protocol/message.py` - Message definition with improved security

- **Security Enhancements**
  - `src/security/crypto.py` - ECDH-384 encryption implementation
  - `src/security/auth.py` - Certificate-based authentication
  - `src/security/policy.py` - Policy-based access control
  - `src/security/security.py` - Security manager implementation

- **Device Plugins**
  - `src/plugins/base.py` - Base plugin interface
  - `src/plugins/raspberry_pi.py` - Raspberry Pi support
  - `src/plugins/arduino.py` - Arduino support
  - `src/plugins/iot.py` - IoT device support
  - `src/plugins/jetson.py` - NVIDIA Jetson support

### Examples

- **Device Integration**
  - `examples/device_integration/jetson_nano_camera.py` - Jetson Nano camera example
  - `examples/device_integration/jetson_orin_ai.py` - Jetson Orin AI example
  - `examples/device_integration/raspberry_pi_gpio.py` - Raspberry Pi GPIO example
  - `examples/device_integration/raspberry_pi_pico.py` - Raspberry Pi Pico example

- **ROS Integration**
  - `examples/ros_integration/ros2_bridge_example.py` - ROS 2 bridge example

- **Security Examples**
  - `examples/security/security_example.py` - Security implementation example

- **Jupyter Notebooks**
  - `examples/binder/basic_demo.ipynb` - Basic protocol demonstration
  - `examples/binder/security_demo.ipynb` - Security features demonstration

### Configuration

- `requirements.txt` - Updated dependencies
- `setup.py` - Package installation script

## Installation

To install these addons, copy the files to the corresponding directories in your ReGenNexus Core installation.

## Documentation

For detailed documentation on these enhancements, please refer to the ReGenNexus Core documentation.
