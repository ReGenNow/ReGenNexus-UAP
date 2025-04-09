"""
ReGenNexus Core - Plugin Base Interface

This module provides the base interface for device plugins in the ReGenNexus Core.
All device plugins should inherit from this base class.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Callable, Union

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DevicePlugin:
    """Base class for ReGenNexus device plugins."""
    
    def __init__(self, entity_id: str, device_type: str, protocol=None):
        """
        Initialize the device plugin.
        
        Args:
            entity_id: Unique identifier for this device entity
            device_type: Type of device (e.g., 'raspberry_pi', 'arduino', 'jetson')
            protocol: Optional protocol instance for message handling
        """
        self.entity_id = entity_id
        self.device_type = device_type
        self.protocol = protocol
        self.initialized = False
        self.capabilities = []
        self.metadata = {}
        self.command_handlers = {}
        self.event_listeners = {}
    
    async def initialize(self) -> bool:
        """
        Initialize the device plugin.
        
        Returns:
            Boolean indicating success
        """
        try:
            # Register basic capabilities
            self.capabilities = [
                'device',
                f'{self.device_type}',
                'status',
                'command'
            ]
            
            # Set basic metadata
            self.metadata = {
                'device_type': self.device_type,
                'version': '0.1.1',
                'status': 'initializing'
            }
            
            # Register command handlers
            self.register_command_handler('status', self._handle_status_command)
            self.register_command_handler('capabilities', self._handle_capabilities_command)
            
            # Register with protocol if available
            if self.protocol:
                # Register message handler
                self.protocol.register_message_handler(self.entity_id, self._handle_message)
                
                # Register entity with registry
                await self.protocol.registry.register_entity(
                    entity_id=self.entity_id,
                    entity_type='device',
                    capabilities=self.capabilities,
                    metadata=self.metadata
                )
            
            self.initialized = True
            self.metadata['status'] = 'ready'
            logger.info(f"Initialized {self.device_type} plugin: {self.entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing {self.device_type} plugin: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """
        Shut down the device plugin.
        
        Returns:
            Boolean indicating success
        """
        try:
            # Update status
            self.metadata['status'] = 'shutting_down'
            
            # Unregister from protocol if available
            if self.protocol:
                # Unregister message handler
                self.protocol.unregister_message_handler(self.entity_id, self._handle_message)
                
                # Unregister entity from registry
                await self.protocol.registry.unregister_entity(self.entity_id)
            
            self.initialized = False
            logger.info(f"Shut down {self.device_type} plugin: {self.entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error shutting down {self.device_type} plugin: {e}")
            return False
    
    def register_command_handler(self, command: str, handler: Callable) -> None:
        """
        Register a handler for a specific command.
        
        Args:
            command: Command name
            handler: Async function that takes command parameters and returns a result
        """
        self.command_handlers[command] = handler
        logger.debug(f"Registered handler for command: {command}")
        
        # Add to capabilities if not already present
        capability = f'command.{command}'
        if capability not in self.capabilities:
            self.capabilities.append(capability)
    
    def unregister_command_handler(self, command: str) -> bool:
        """
        Unregister a command handler.
        
        Args:
            command: Command name
            
        Returns:
            Boolean indicating success
        """
        if command in self.command_handlers:
            del self.command_handlers[command]
            logger.debug(f"Unregistered handler for command: {command}")
            
            # Remove from capabilities
            capability = f'command.{command}'
            if capability in self.capabilities:
                self.capabilities.remove(capability)
                
            return True
        return False
    
    def register_event_listener(self, event_type: str, listener: Callable) -> None:
        """
        Register a listener for a specific event type.
        
        Args:
            event_type: Event type
            listener: Async function that takes event data
        """
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
            
        self.event_listeners[event_type].append(listener)
        logger.debug(f"Registered listener for event: {event_type}")
        
        # Add to capabilities if not already present
        capability = f'event.{event_type}'
        if capability not in self.capabilities:
            self.capabilities.append(capability)
    
    def unregister_event_listener(self, event_type: str, listener: Callable) -> bool:
        """
        Unregister an event listener.
        
        Args:
            event_type: Event type
            listener: Listener function to unregister
            
        Returns:
            Boolean indicating success
        """
        if event_type in self.event_listeners and listener in self.event_listeners[event_type]:
            self.event_listeners[event_type].remove(listener)
            logger.debug(f"Unregistered listener for event: {event_type}")
            
            # Remove from capabilities if no more listeners
            if not self.event_listeners[event_type]:
                del self.event_listeners[event_type]
                capability = f'event.{event_type}'
                if capability in self.capabilities:
                    self.capabilities.remove(capability)
                    
            return True
        return False
    
    async def emit_event(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Emit an event to registered listeners and via protocol.
        
        Args:
            event_type: Event type
            event_data: Event data
            
        Returns:
            Boolean indicating success
        """
        try:
            # Call local listeners
            if event_type in self.event_listeners:
                for listener in self.event_listeners[event_type]:
                    try:
                        await listener(event_data)
                    except Exception as e:
                        logger.error(f"Error in event listener: {e}")
            
            # Send event via protocol if available
            if self.protocol:
                await self.protocol.send_message(
                    sender=self.entity_id,
                    recipient='*',  # Broadcast
                    intent=f'event.{event_type}',
                    payload=event_data
                )
            
            logger.debug(f"Emitted event: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error emitting event: {e}")
            return False
    
    async def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command on the device.
        
        Args:
            command: Command name
            params: Command parameters
            
        Returns:
            Command result
        """
        try:
            # Check if command is supported
            if command not in self.command_handlers:
                return {
                    'success': False,
                    'error': f"Unsupported command: {command}"
                }
            
            # Execute command
            handler = self.command_handlers[command]
            result = await handler(params)
            
            logger.debug(f"Executed command: {command}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle incoming messages from the protocol.
        
        Args:
            message: Message to handle
        """
        try:
            # Check if message is for this entity
            if message.get('recipient') != self.entity_id and message.get('recipient') != '*':
                return
            
            # Check intent
            intent = message.get('intent', '')
            
            # Handle command intent
            if intent == 'command':
                # Extract command and parameters
                command = message.get('payload', {}).get('command', '')
                params = message.get('payload', {}).get('params', {})
                
                # Execute command
                result = await self.execute_command(command, params)
                
                # Send response
                if self.protocol and message.get('recipient') != '*':
                    await self.protocol.send_message(
                        sender=self.entity_id,
                        recipient=message.get('sender'),
                        intent='command_result',
                        payload={
                            'command': command,
                            'result': result
                        }
                    )
            
            # Handle event subscription intent
            elif intent == 'subscribe':
                event_type = message.get('payload', {}).get('event_type', '')
                if event_type:
                    # Add capability if not already present
                    capability = f'event.{event_type}'
                    if capability not in self.capabilities:
                        self.capabilities.append(capability)
                    
                    # Send acknowledgment
                    if self.protocol and message.get('recipient') != '*':
                        await self.protocol.send_message(
                            sender=self.entity_id,
                            recipient=message.get('sender'),
                            intent='subscribe_ack',
                            payload={
                                'event_type': event_type,
                                'success': True
                            }
                        )
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _handle_status_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle status command.
        
        Args:
            params: Command parameters
            
        Returns:
            Status information
        """
        return {
            'success': True,
            'status': self.metadata.get('status', 'unknown'),
            'device_type': self.device_type,
            'entity_id': self.entity_id,
            'capabilities': self.capabilities,
            'metadata': self.metadata
        }
    
    async def _handle_capabilities_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle capabilities command.
        
        Args:
            params: Command parameters
            
        Returns:
            Capabilities information
        """
        return {
            'success': True,
            'capabilities': self.capabilities
        }
