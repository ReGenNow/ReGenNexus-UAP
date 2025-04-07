"""
Registry Module

This module implements the entity registry for ReGenNexus UAP.
It provides functionality for registering entities and routing messages.
"""

import uuid
from typing import Dict, List, Optional, Any
from .protocol_core import Entity, Message


class Registry:
    """
    Registry for entities in the ReGenNexus protocol
    
    The registry manages all entities in the system and handles message routing.
    """
    
    def __init__(self):
        """Initialize a new registry"""
        self.entities: Dict[str, Entity] = {}
    
    async def register_entity(self, entity: Entity) -> bool:
        """
        Register an entity with the registry
        
        Args:
            entity: The entity to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        if entity.id in self.entities:
            return False
        
        self.entities[entity.id] = entity
        return True
    
    async def unregister_entity(self, entity_id: str) -> bool:
        """
        Unregister an entity from the registry
        
        Args:
            entity_id: ID of the entity to unregister
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if entity_id not in self.entities:
            return False
        
        del self.entities[entity_id]
        return True
    
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Get an entity by ID
        
        Args:
            entity_id: ID of the entity to retrieve
            
        Returns:
            The entity if found, None otherwise
        """
        return self.entities.get(entity_id)
    
    async def find_entities_by_capability(self, capability: str) -> List[Entity]:
        """
        Find entities with a specific capability
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of entities with the specified capability
        """
        return [
            entity for entity in self.entities.values()
            if entity.has_capability(capability)
        ]
    
    async def route_message(self, message: Message, context: Any = None) -> Optional[Message]:
        """
        Route a message to its recipient and process the response
        
        Args:
            message: The message to route
            context: Optional context information
            
        Returns:
            Response message if any, None otherwise
        """
        recipient = self.entities.get(message.recipient_id)
        if not recipient:
            return None
        
        return await recipient.process_message(message, context)
    
    def get_all_entities(self) -> List[Entity]:
        """
        Get all registered entities
        
        Returns:
            List of all entities in the registry
        """
        return list(self.entities.values())
