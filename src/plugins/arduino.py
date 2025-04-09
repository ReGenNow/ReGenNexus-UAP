"""
ReGenNexus Core - Arduino Plugin

This module provides Arduino integration for the ReGenNexus Core.
It supports serial communication and pin control.
"""

import asyncio
import logging
import json
import os
import time
import serial
import serial.tools.list_ports
from typing import Dict, Any, List, Optional, Callable, Union

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import base plugin class
from .base import DevicePlugin

class ArduinoPlugin(DevicePlugin):
    """Arduino plugin for ReGenNexus Core."""
    
    def __init__(self, entity_id: str, port: Optional[str] = None, 
                 baud_rate: int = 9600, protocol=None):
        """
        Initialize the Arduino plugin.
        
        Args:
            entity_id: Unique identifier for this device entity
            port: Serial port (e.g., '/dev/ttyACM0', 'COM3')
            baud_rate: Serial baud rate
            protocol: Optional protocol instance for message handling
        """
        super().__init__(entity_id, 'arduino', protocol)
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
        self.connected = False
        self.read_task = None
        self.command_queue = asyncio.Queue()
        self.response_queue = asyncio.Queue()
    
    async def initialize(self) -> bool:
        """
        Initialize the Arduino plugin.
        
        Returns:
            Boolean indicating success
        """
        try:
            # Auto-detect port if not specified
            if not self.port:
                ports = list(serial.tools.list_ports.comports())
                for p in ports:
                    if 'Arduino' in p.description:
                        self.port = p.device
                        break
                
                if not self.port and ports:
                    # Just use the first available port
                    self.port = ports[0].device
            
            # Check if port is available
            if not self.port:
                logger.warning("No Arduino port found")
                self.metadata.update({
                    'status': 'no_port',
                    'port': None
                })
            else:
                # Connect to Arduino
                try:
                    self.serial = serial.Serial(self.port, self.baud_rate, timeout=1)
                    await asyncio.sleep(2)  # Wait for Arduino to reset
                    self.connected = True
                    
                    # Start read task
                    self.read_task = asyncio.create_task(self._read_serial())
                    
                    logger.info(f"Connected to Arduino on {self.port}")
                    self.metadata.update({
                        'status': 'connected',
                        'port': self.port,
                        'baud_rate': self.baud_rate
                    })
                except Exception as e:
                    logger.error(f"Error connecting to Arduino: {e}")
                    self.metadata.update({
                        'status': 'connection_error',
                        'port': self.port,
                        'error': str(e)
                    })
            
            # Add capabilities
            self.capabilities.extend([
                'arduino.digital_read',
                'arduino.digital_write',
                'arduino.analog_read',
                'arduino.analog_write',
                'arduino.send_command'
            ])
            
            # Register command handlers
            self.register_command_handler('arduino.digital_read', self._handle_digital_read)
            self.register_command_handler('arduino.digital_write', self._handle_digital_write)
            self.register_command_handler('arduino.analog_read', self._handle_analog_read)
            self.register_command_handler('arduino.analog_write', self._handle_analog_write)
            self.register_command_handler('arduino.send_command', self._handle_send_command)
            
            # Initialize base plugin
            await super().initialize()
            
            logger.info(f"Initialized Arduino plugin: {self.entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Arduino plugin: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """
        Shut down the Arduino plugin.
        
        Returns:
            Boolean indicating success
        """
        try:
            # Stop read task
            if self.read_task:
                self.read_task.cancel()
                try:
                    await self.read_task
                except asyncio.CancelledError:
                    pass
                self.read_task = None
            
            # Close serial connection
            if self.serial:
                self.serial.close()
                self.serial = None
                self.connected = False
            
            # Shut down base plugin
            await super().shutdown()
            
            logger.info(f"Shut down Arduino plugin: {self.entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error shutting down Arduino plugin: {e}")
            return False
    
    async def _read_serial(self) -> None:
        """Read data from the serial port."""
        try:
            while True:
                if self.serial and self.serial.in_waiting:
                    try:
                        line = self.serial.readline().decode('utf-8').strip()
                        if line:
                            logger.debug(f"Received from Arduino: {line}")
                            
                            # Try to parse as JSON
                            try:
                                data = json.loads(line)
                                
                                # Check if it's a response to a command
                                if 'response' in data:
                                    await self.response_queue.put(data)
                                
                                # Check if it's an event
                                elif 'event' in data:
                                    await self.emit_event('arduino', data)
                            except json.JSONDecodeError:
                                # Not JSON, treat as plain text
                                await self.emit_event('arduino.data', {
                                    'data': line
                                })
                    except Exception as e:
                        logger.error(f"Error reading from Arduino: {e}")
                
                await asyncio.sleep(0.01)
                
        except asyncio.CancelledError:
            # Task was cancelled, exit
            pass
            
        except Exception as e:
            logger.error(f"Error in serial read task: {e}")
    
    async def _send_command(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Send a command to the Arduino and wait for response.
        
        Args:
            command: Command string to send
            
        Returns:
            Response data or None if error
        """
        try:
            if not self.connected or not self.serial:
                raise ValueError("Not connected to Arduino")
            
            # Send command
            self.serial.write(f"{command}\n".encode('utf-8'))
            self.serial.flush()
            
            # Wait for response
            try:
                response = await asyncio.wait_for(self.response_queue.get(), timeout=5.0)
                return response
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for response to command: {command}")
                return None
            
        except Exception as e:
            logger.error(f"Error sending command to Arduino: {e}")
            return None
    
    async def _handle_digital_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle digital read command.
        
        Args:
            params: Command parameters (pin)
            
        Returns:
            Pin state
        """
        try:
            # Check if connected
            if not self.connected:
                return {
                    'success': False,
                    'error': "Not connected to Arduino"
                }
            
            # Get pin number
            pin = params.get('pin')
            if pin is None:
                return {
                    'success': False,
                    'error': "Missing pin parameter"
                }
            
            # Send command to Arduino
            command = f"DR {pin}"
            response = await self._send_command(command)
            
            if not response:
                return {
                    'success': False,
                    'error': "No response from Arduino"
                }
            
            return {
                'success': True,
                'pin': pin,
                'value': response.get('value', 0)
            }
            
        except Exception as e:
            logger.error(f"Error handling digital read: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_digital_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle digital write command.
        
        Args:
            params: Command parameters (pin, value)
            
        Returns:
            Command result
        """
        try:
            # Check if connected
            if not self.connected:
                return {
                    'success': False,
                    'error': "Not connected to Arduino"
                }
            
            # Get parameters
            pin = params.get('pin')
            value = params.get('value')
            if pin is None or value is None:
                return {
                    'success': False,
                    'error': "Missing pin or value parameter"
                }
            
            # Send command to Arduino
            command = f"DW {pin} {1 if value else 0}"
            response = await self._send_command(command)
            
            if not response:
                return {
                    'success': False,
                    'error': "No response from Arduino"
                }
            
            return {
                'success': True,
                'pin': pin,
                'value': value
            }
            
        except Exception as e:
            logger.error(f"Error handling digital write: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_analog_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle analog read command.
        
        Args:
            params: Command parameters (pin)
            
        Returns:
            Pin value
        """
        try:
            # Check if connected
            if not self.connected:
                return {
                    'success': False,
                    'error': "Not connected to Arduino"
                }
            
            # Get pin number
            pin = params.get('pin')
            if pin is None:
                return {
                    'success': False,
                    'error': "Missing pin parameter"
                }
            
            # Send command to Arduino
            command = f"AR {pin}"
            response = await self._send_command(command)
            
            if not response:
                return {
                    'success': False,
                    'error': "No response from Arduino"
                }
            
            return {
                'success': True,
                'pin': pin,
                'value': response.get('value', 0)
            }
            
        except Exception as e:
            logger.error(f"Error handling analog read: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_analog_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle analog write command.
        
        Args:
            params: Command parameters (pin, value)
            
        Returns:
            Command result
        """
        try:
            # Check if connected
            if not self.connected:
                return {
                    'success': False,
                    'error': "Not connected to Arduino"
                }
            
            # Get parameters
            pin = params.get('pin')
            value = params.get('value')
            if pin is None or value is None:
                return {
                    'success': False,
                    'error': "Missing pin or value parameter"
                }
            
            # Ensure value is in range 0-255
            value = max(0, min(255, int(value)))
            
            # Send command to Arduino
            command = f"AW {pin} {value}"
            response = await self._send_command(command)
            
            if not response:
                return {
                    'success': False,
                    'error': "No response from Arduino"
                }
            
            return {
                'success': True,
                'pin': pin,
                'value': value
            }
            
        except Exception as e:
            logger.error(f"Error handling analog write: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_send_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle send command.
        
        Args:
            params: Command parameters (command)
            
        Returns:
            Command result
        """
        try:
            # Check if connected
            if not self.connected:
                return {
                    'success': False,
                    'error': "Not connected to Arduino"
                }
            
            # Get command
            command = params.get('command')
            if not command:
                return {
                    'success': False,
                    'error': "Missing command parameter"
                }
            
            # Send command to Arduino
            response = await self._send_command(command)
            
            if not response:
                return {
                    'success': False,
                    'error': "No response from Arduino"
                }
            
            return {
                'success': True,
                'command': command,
                'response': response
            }
            
        except Exception as e:
            logger.error(f"Error handling send command: {e}")
            return {
                'success': False,
                'error': str(e)
            }
