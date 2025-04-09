"""
ReGenNexus Core - IoT Plugin

This module provides IoT device integration for the ReGenNexus Core.
It supports MQTT, HTTP, and other standard IoT protocols.
"""

import asyncio
import logging
import json
import os
import time
import aiohttp
import ssl
from typing import Dict, Any, List, Optional, Callable, Union

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import base plugin class
from .base import DevicePlugin

class IoTPlugin(DevicePlugin):
    """IoT plugin for ReGenNexus Core."""
    
    def __init__(self, entity_id: str, protocol=None):
        """
        Initialize the IoT plugin.
        
        Args:
            entity_id: Unique identifier for this device entity
            protocol: Optional protocol instance for message handling
        """
        super().__init__(entity_id, 'iot', protocol)
        self.mqtt_client = None
        self.http_session = None
        self.mqtt_connected = False
        self.mqtt_subscriptions = {}
        self.mqtt_task = None
    
    async def initialize(self) -> bool:
        """
        Initialize the IoT plugin.
        
        Returns:
            Boolean indicating success
        """
        try:
            # Initialize HTTP session
            self.http_session = aiohttp.ClientSession()
            
            # Add capabilities
            self.capabilities.extend([
                'iot.mqtt.connect',
                'iot.mqtt.publish',
                'iot.mqtt.subscribe',
                'iot.http.get',
                'iot.http.post',
                'iot.http.put',
                'iot.http.delete'
            ])
            
            # Register command handlers
            self.register_command_handler('iot.mqtt.connect', self._handle_mqtt_connect)
            self.register_command_handler('iot.mqtt.publish', self._handle_mqtt_publish)
            self.register_command_handler('iot.mqtt.subscribe', self._handle_mqtt_subscribe)
            self.register_command_handler('iot.http.get', self._handle_http_get)
            self.register_command_handler('iot.http.post', self._handle_http_post)
            self.register_command_handler('iot.http.put', self._handle_http_put)
            self.register_command_handler('iot.http.delete', self._handle_http_delete)
            
            # Update metadata
            self.metadata.update({
                'device_type': 'iot',
                'mqtt_connected': self.mqtt_connected
            })
            
            # Initialize base plugin
            await super().initialize()
            
            logger.info(f"Initialized IoT plugin: {self.entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing IoT plugin: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """
        Shut down the IoT plugin.
        
        Returns:
            Boolean indicating success
        """
        try:
            # Disconnect MQTT
            if self.mqtt_client and self.mqtt_connected:
                try:
                    # Stop MQTT task
                    if self.mqtt_task:
                        self.mqtt_task.cancel()
                        try:
                            await self.mqtt_task
                        except asyncio.CancelledError:
                            pass
                        self.mqtt_task = None
                    
                    # Disconnect MQTT client
                    await self.mqtt_client.disconnect()
                    self.mqtt_connected = False
                except:
                    pass
            
            # Close HTTP session
            if self.http_session:
                await self.http_session.close()
                self.http_session = None
            
            # Shut down base plugin
            await super().shutdown()
            
            logger.info(f"Shut down IoT plugin: {self.entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error shutting down IoT plugin: {e}")
            return False
    
    async def _handle_mqtt_connect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MQTT connect command.
        
        Args:
            params: Command parameters (broker, port, username, password, client_id)
            
        Returns:
            Connection result
        """
        try:
            # Check if already connected
            if self.mqtt_connected:
                return {
                    'success': True,
                    'message': "Already connected to MQTT broker"
                }
            
            # Get parameters
            broker = params.get('broker')
            port = params.get('port', 1883)
            username = params.get('username')
            password = params.get('password')
            client_id = params.get('client_id', f"regennexus-{self.entity_id}")
            use_tls = params.get('use_tls', False)
            
            if not broker:
                return {
                    'success': False,
                    'error': "Missing broker parameter"
                }
            
            # Import MQTT client
            try:
                import asyncio_mqtt
            except ImportError:
                return {
                    'success': False,
                    'error': "asyncio_mqtt module not installed"
                }
            
            # Set up TLS if needed
            tls_context = None
            if use_tls:
                tls_context = ssl.create_default_context()
            
            # Connect to MQTT broker
            try:
                self.mqtt_client = asyncio_mqtt.Client(
                    hostname=broker,
                    port=port,
                    username=username,
                    password=password,
                    client_id=client_id,
                    tls_context=tls_context
                )
                await self.mqtt_client.connect()
                self.mqtt_connected = True
                
                # Start MQTT task
                self.mqtt_task = asyncio.create_task(self._mqtt_loop())
                
                # Update metadata
                self.metadata.update({
                    'mqtt_connected': True,
                    'mqtt_broker': broker,
                    'mqtt_port': port
                })
                
                logger.info(f"Connected to MQTT broker: {broker}:{port}")
                
                return {
                    'success': True,
                    'broker': broker,
                    'port': port,
                    'client_id': client_id
                }
                
            except Exception as e:
                logger.error(f"Error connecting to MQTT broker: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }
            
        except Exception as e:
            logger.error(f"Error handling MQTT connect: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _mqtt_loop(self) -> None:
        """MQTT message loop."""
        try:
            async with self.mqtt_client.filtered_messages('#') as messages:
                await self.mqtt_client.subscribe('#')
                async for message in messages:
                    topic = message.topic.value
                    payload = message.payload.decode()
                    
                    logger.debug(f"Received MQTT message: {topic} - {payload}")
                    
                    # Try to parse payload as JSON
                    try:
                        payload_data = json.loads(payload)
                    except json.JSONDecodeError:
                        payload_data = payload
                    
                    # Emit event
                    await self.emit_event('iot.mqtt.message', {
                        'topic': topic,
                        'payload': payload_data
                    })
                    
                    # Call subscribed handlers
                    if topic in self.mqtt_subscriptions:
                        for handler in self.mqtt_subscriptions[topic]:
                            try:
                                await handler(topic, payload_data)
                            except Exception as e:
                                logger.error(f"Error in MQTT handler: {e}")
                    
        except asyncio.CancelledError:
            # Task was cancelled, exit
            pass
            
        except Exception as e:
            logger.error(f"Error in MQTT loop: {e}")
            self.mqtt_connected = False
            self.metadata.update({
                'mqtt_connected': False
            })
    
    async def _handle_mqtt_publish(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MQTT publish command.
        
        Args:
            params: Command parameters (topic, payload, qos, retain)
            
        Returns:
            Publish result
        """
        try:
            # Check if connected
            if not self.mqtt_connected or not self.mqtt_client:
                return {
                    'success': False,
                    'error': "Not connected to MQTT broker"
                }
            
            # Get parameters
            topic = params.get('topic')
            payload = params.get('payload')
            qos = params.get('qos', 0)
            retain = params.get('retain', False)
            
            if not topic or payload is None:
                return {
                    'success': False,
                    'error': "Missing topic or payload parameter"
                }
            
            # Convert payload to JSON string if it's a dict
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            
            # Publish message
            await self.mqtt_client.publish(
                topic=topic,
                payload=payload,
                qos=qos,
                retain=retain
            )
            
            logger.debug(f"Published MQTT message: {topic} - {payload}")
            
            return {
                'success': True,
                'topic': topic,
                'qos': qos,
                'retain': retain
            }
            
        except Exception as e:
            logger.error(f"Error handling MQTT publish: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_mqtt_subscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MQTT subscribe command.
        
        Args:
            params: Command parameters (topic, qos)
            
        Returns:
            Subscribe result
        """
        try:
            # Check if connected
            if not self.mqtt_connected or not self.mqtt_client:
                return {
                    'success': False,
                    'error': "Not connected to MQTT broker"
                }
            
            # Get parameters
            topic = params.get('topic')
            qos = params.get('qos', 0)
            
            if not topic:
                return {
                    'success': False,
                    'error': "Missing topic parameter"
                }
            
            # Subscribe to topic
            await self.mqtt_client.subscribe(
                topic=topic,
                qos=qos
            )
            
            logger.debug(f"Subscribed to MQTT topic: {topic}")
            
            return {
                'success': True,
                'topic': topic,
                'qos': qos
            }
            
        except Exception as e:
            logger.error(f"Error handling MQTT subscribe: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_http_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle HTTP GET command.
        
        Args:
            params: Command parameters (url, headers, params)
            
        Returns:
            HTTP response
        """
        try:
            # Check if HTTP session is available
            if not self.http_session:
                return {
                    'success': False,
                    'error': "HTTP session not available"
                }
            
            # Get parameters
            url = params.get('url')
            headers = params.get('headers', {})
            query_params = params.get('params', {})
            
            if not url:
                return {
                    'success': False,
                    'error': "Missing url parameter"
                }
            
            # Send GET request
            async with self.http_session.get(
                url=url,
                headers=headers,
                params=query_params
            ) as response:
                status = response.status
                
                # Get response content
                try:
                    content = await response.json()
                except:
                    content = await response.text()
                
                logger.debug(f"HTTP GET response: {status} - {url}")
                
                return {
                    'success': status < 400,
                    'status': status,
                    'url': url,
                    'content': content,
                    'headers': dict(response.headers)
                }
            
        except Exception as e:
            logger.error(f"Error handling HTTP GET: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_http_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle HTTP POST command.
        
        Args:
            params: Command parameters (url, headers, data, json)
            
        Returns:
            HTTP response
        """
        try:
            # Check if HTTP session is available
            if not self.http_session:
                return {
                    'success': False,
                    'error': "HTTP session not available"
                }
            
            # Get parameters
            url = params.get('url')
            headers = params.get('headers', {})
            data = params.get('data')
            json_data = params.get('json')
            
            if not url:
                return {
                    'success': False,
                    'error': "Missing url parameter"
                }
            
            # Send POST request
            async with self.http_session.post(
                url=url,
                headers=headers,
                data=data,
                json=json_data
            ) as response:
                status = response.status
                
                # Get response content
                try:
                    content = await response.json()
                except:
                    content = await response.text()
                
                logger.debug(f"HTTP POST response: {status} - {url}")
                
                return {
                    'success': status < 400,
                    'status': status,
                    'url': url,
                    'content': content,
                    'headers': dict(response.headers)
                }
            
        except Exception as e:
            logger.error(f"Error handling HTTP POST: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_http_put(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle HTTP PUT command.
        
        Args:
            params: Command parameters (url, headers, data, json)
            
        Returns:
            HTTP response
        """
        try:
            # Check if HTTP session is available
            if not self.http_session:
                return {
                    'success': False,
                    'error': "HTTP session not available"
                }
            
            # Get parameters
            url = params.get('url')
            headers = params.get('headers', {})
            data = params.get('data')
            json_data = params.get('json')
            
            if not url:
                return {
                    'success': False,
                    'error': "Missing url parameter"
                }
            
            # Send PUT request
            async with self.http_session.put(
                url=url,
                headers=headers,
                data=data,
                json=json_data
            ) as response:
                status = response.status
                
                # Get response content
                try:
                    content = await response.json()
                except:
                    content = await response.text()
                
                logger.debug(f"HTTP PUT response: {status} - {url}")
                
                return {
                    'success': status < 400,
                    'status': status,
                    'url': url,
                    'content': content,
                    'headers': dict(response.headers)
                }
            
        except Exception as e:
            logger.error(f"Error handling HTTP PUT: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_http_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle HTTP DELETE command.
        
        Args:
            params: Command parameters (url, headers)
            
        Returns:
            HTTP response
        """
        try:
            # Check if HTTP session is available
            if not self.http_session:
                return {
                    'success': False,
                    'error': "HTTP session not available"
                }
            
            # Get parameters
            url = params.get('url')
            headers = params.get('headers', {})
            
            if not url:
                return {
                    'success': False,
                    'error': "Missing url parameter"
                }
            
            # Send DELETE request
            async with self.http_session.delete(
                url=url,
                headers=headers
            ) as response:
                status = response.status
                
                # Get response content
                try:
                    content = await response.json()
                except:
                    content = await response.text()
                
                logger.debug(f"HTTP DELETE response: {status} - {url}")
                
                return {
                    'success': status < 400,
                    'status': status,
                    'url': url,
                    'content': content,
                    'headers': dict(response.headers)
                }
            
        except Exception as e:
            logger.error(f"Error handling HTTP DELETE: {e}")
            return {
                'success': False,
                'error': str(e)
            }
