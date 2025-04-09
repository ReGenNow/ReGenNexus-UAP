"""
ReGenNexus Core - Raspberry Pi Plugin

This module provides Raspberry Pi integration for the ReGenNexus Core.
It supports GPIO, camera, and sensor functionality.
"""

import asyncio
import logging
import json
import os
import time
from typing import Dict, Any, List, Optional, Callable, Union

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import base plugin class
from .base import DevicePlugin

class RaspberryPiPlugin(DevicePlugin):
    """Raspberry Pi plugin for ReGenNexus Core."""
    
    def __init__(self, entity_id: str, protocol=None):
        """
        Initialize the Raspberry Pi plugin.
        
        Args:
            entity_id: Unique identifier for this device entity
            protocol: Optional protocol instance for message handling
        """
        super().__init__(entity_id, 'raspberry_pi', protocol)
        self.gpio_state = {}
        self.camera_active = False
        self.sensors = {}
        self.gpio_module = None
        self.camera_module = None
    
    async def initialize(self) -> bool:
        """
        Initialize the Raspberry Pi plugin.
        
        Returns:
            Boolean indicating success
        """
        try:
            # Try to import Raspberry Pi specific modules
            try:
                # Import GPIO module
                import RPi.GPIO as GPIO
                self.gpio_module = GPIO
                self.gpio_module.setmode(GPIO.BCM)
                logger.info("Initialized Raspberry Pi GPIO module")
                
                # Add GPIO capabilities
                self.capabilities.extend([
                    'gpio.read',
                    'gpio.write',
                    'gpio.pwm'
                ])
            except ImportError:
                logger.warning("RPi.GPIO module not available, GPIO functionality disabled")
            
            try:
                # Import camera module
                import picamera
                self.camera_module = picamera
                logger.info("Initialized Raspberry Pi camera module")
                
                # Add camera capabilities
                self.capabilities.extend([
                    'camera.capture',
                    'camera.record',
                    'camera.stream'
                ])
            except ImportError:
                logger.warning("picamera module not available, camera functionality disabled")
            
            # Register command handlers
            self.register_command_handler('gpio.read', self._handle_gpio_read)
            self.register_command_handler('gpio.write', self._handle_gpio_write)
            self.register_command_handler('gpio.pwm', self._handle_gpio_pwm)
            self.register_command_handler('camera.capture', self._handle_camera_capture)
            self.register_command_handler('camera.record', self._handle_camera_record)
            self.register_command_handler('camera.stream', self._handle_camera_stream)
            self.register_command_handler('sensor.read', self._handle_sensor_read)
            
            # Update metadata
            self.metadata.update({
                'device_type': 'raspberry_pi',
                'gpio_available': self.gpio_module is not None,
                'camera_available': self.camera_module is not None,
                'model': self._get_pi_model()
            })
            
            # Initialize base plugin
            await super().initialize()
            
            logger.info(f"Initialized Raspberry Pi plugin: {self.entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Raspberry Pi plugin: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """
        Shut down the Raspberry Pi plugin.
        
        Returns:
            Boolean indicating success
        """
        try:
            # Clean up GPIO
            if self.gpio_module:
                self.gpio_module.cleanup()
            
            # Clean up camera
            if self.camera_active and self.camera_module:
                try:
                    # Close any active camera
                    self.camera.close()
                    self.camera_active = False
                except:
                    pass
            
            # Shut down base plugin
            await super().shutdown()
            
            logger.info(f"Shut down Raspberry Pi plugin: {self.entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error shutting down Raspberry Pi plugin: {e}")
            return False
    
    def _get_pi_model(self) -> str:
        """
        Get the Raspberry Pi model information.
        
        Returns:
            Model information string
        """
        try:
            # Try to read model from /proc/device-tree/model
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    return f.read().strip('\0')
            
            # Fallback to CPU info
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Model'):
                        return line.split(':', 1)[1].strip()
            
            return "Unknown Raspberry Pi"
            
        except Exception as e:
            logger.error(f"Error getting Pi model: {e}")
            return "Unknown Raspberry Pi"
    
    async def _handle_gpio_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GPIO read command.
        
        Args:
            params: Command parameters (pin)
            
        Returns:
            GPIO state
        """
        try:
            # Check if GPIO is available
            if not self.gpio_module:
                return {
                    'success': False,
                    'error': "GPIO module not available"
                }
            
            # Get pin number
            pin = params.get('pin')
            if pin is None:
                return {
                    'success': False,
                    'error': "Missing pin parameter"
                }
            
            # Set up pin as input if not already
            if pin not in self.gpio_state:
                self.gpio_module.setup(pin, self.gpio_module.IN)
                self.gpio_state[pin] = {
                    'mode': 'input',
                    'value': None
                }
            
            # Read pin
            value = self.gpio_module.input(pin)
            self.gpio_state[pin]['value'] = value
            
            return {
                'success': True,
                'pin': pin,
                'value': value
            }
            
        except Exception as e:
            logger.error(f"Error reading GPIO: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_gpio_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GPIO write command.
        
        Args:
            params: Command parameters (pin, value)
            
        Returns:
            Command result
        """
        try:
            # Check if GPIO is available
            if not self.gpio_module:
                return {
                    'success': False,
                    'error': "GPIO module not available"
                }
            
            # Get parameters
            pin = params.get('pin')
            value = params.get('value')
            if pin is None or value is None:
                return {
                    'success': False,
                    'error': "Missing pin or value parameter"
                }
            
            # Set up pin as output
            self.gpio_module.setup(pin, self.gpio_module.OUT)
            
            # Write value
            self.gpio_module.output(pin, value)
            
            # Update state
            self.gpio_state[pin] = {
                'mode': 'output',
                'value': value
            }
            
            return {
                'success': True,
                'pin': pin,
                'value': value
            }
            
        except Exception as e:
            logger.error(f"Error writing GPIO: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_gpio_pwm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GPIO PWM command.
        
        Args:
            params: Command parameters (pin, frequency, duty_cycle)
            
        Returns:
            Command result
        """
        try:
            # Check if GPIO is available
            if not self.gpio_module:
                return {
                    'success': False,
                    'error': "GPIO module not available"
                }
            
            # Get parameters
            pin = params.get('pin')
            frequency = params.get('frequency', 1000)
            duty_cycle = params.get('duty_cycle', 50)
            
            if pin is None:
                return {
                    'success': False,
                    'error': "Missing pin parameter"
                }
            
            # Set up pin as output
            self.gpio_module.setup(pin, self.gpio_module.OUT)
            
            # Create PWM instance
            pwm = self.gpio_module.PWM(pin, frequency)
            
            # Start PWM
            pwm.start(duty_cycle)
            
            # Update state
            self.gpio_state[pin] = {
                'mode': 'pwm',
                'frequency': frequency,
                'duty_cycle': duty_cycle,
                'pwm': pwm
            }
            
            return {
                'success': True,
                'pin': pin,
                'frequency': frequency,
                'duty_cycle': duty_cycle
            }
            
        except Exception as e:
            logger.error(f"Error setting up PWM: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_camera_capture(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle camera capture command.
        
        Args:
            params: Command parameters (path, resolution)
            
        Returns:
            Command result
        """
        try:
            # Check if camera is available
            if not self.camera_module:
                return {
                    'success': False,
                    'error': "Camera module not available"
                }
            
            # Get parameters
            path = params.get('path', f'/tmp/capture_{int(time.time())}.jpg')
            resolution = params.get('resolution', (1280, 720))
            
            # Initialize camera if not active
            if not self.camera_active:
                self.camera = self.camera_module.PiCamera()
                self.camera_active = True
            
            # Set resolution
            self.camera.resolution = resolution
            
            # Capture image
            self.camera.capture(path)
            
            return {
                'success': True,
                'path': path,
                'resolution': resolution
            }
            
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_camera_record(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle camera record command.
        
        Args:
            params: Command parameters (path, duration, resolution)
            
        Returns:
            Command result
        """
        try:
            # Check if camera is available
            if not self.camera_module:
                return {
                    'success': False,
                    'error': "Camera module not available"
                }
            
            # Get parameters
            path = params.get('path', f'/tmp/video_{int(time.time())}.h264')
            duration = params.get('duration', 10)  # seconds
            resolution = params.get('resolution', (1280, 720))
            
            # Initialize camera if not active
            if not self.camera_active:
                self.camera = self.camera_module.PiCamera()
                self.camera_active = True
            
            # Set resolution
            self.camera.resolution = resolution
            
            # Start recording
            self.camera.start_recording(path)
            
            # Wait for specified duration
            await asyncio.sleep(duration)
            
            # Stop recording
            self.camera.stop_recording()
            
            return {
                'success': True,
                'path': path,
                'duration': duration,
                'resolution': resolution
            }
            
        except Exception as e:
            logger.error(f"Error recording video: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_camera_stream(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle camera stream command.
        
        Args:
            params: Command parameters (port, resolution)
            
        Returns:
            Command result
        """
        try:
            # Check if camera is available
            if not self.camera_module:
                return {
                    'success': False,
                    'error': "Camera module not available"
                }
            
            # Get parameters
            port = params.get('port', 8000)
            resolution = params.get('resolution', (640, 480))
            
            # This is a simplified implementation
            # In a real implementation, this would set up a streaming server
            
            return {
                'success': True,
                'message': "Streaming not implemented in this version",
                'port': port,
                'resolution': resolution
            }
            
        except Exception as e:
            logger.error(f"Error streaming video: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_sensor_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle sensor read command.
        
        Args:
            params: Command parameters (sensor_type)
            
        Returns:
            Sensor data
        """
        try:
            # Get sensor type
            sensor_type = params.get('sensor_type')
            if not sensor_type:
                return {
                    'success': False,
                    'error': "Missing sensor_type parameter"
                }
            
            # Check if sensor is registered
            if sensor_type not in self.sensors:
                return {
                    'success': False,
                    'error': f"Sensor {sensor_type} not registered"
                }
            
            # Read sensor data
            sensor = self.sensors[sensor_type]
            data = await sensor['read_func']()
            
            return {
                'success': True,
                'sensor_type': sensor_type,
                'data': data
            }
            
        except Exception as e:
            logger.error(f"Error reading sensor: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def register_sensor(self, sensor_type: str, read_func: Callable) -> bool:
        """
        Register a sensor with the plugin.
        
        Args:
            sensor_type: Type of sensor
            read_func: Async function to read sensor data
            
        Returns:
            Boolean indicating success
        """
        try:
            # Register sensor
            self.sensors[sensor_type] = {
                'read_func': read_func
            }
            
            # Add to capabilities
            capability = f'sensor.{sensor_type}'
            if capability not in self.capabilities:
                self.capabilities.append(capability)
            
            logger.info(f"Registered sensor: {sensor_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering sensor: {e}")
            return False
