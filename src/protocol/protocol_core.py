"""
Protocol Core Module

This module implements the core protocol functionality for ReGenNexus UAP.
It provides the basic message structure, entity interface, and intent definitions.
"""

import uuid
import time
from typing import Dict, Any, Optional, List


class Intent:
    """Defines standard message intents for the protocol"""
    
    # Basic communication intents
    GREETING = "greeting"
    QUERY = "query"
    RESPONSE = "response"
    ERROR = "error"
    
    # Status intents
    STATUS_REQUEST = "status.request"
    STATUS_RESPONSE = "status.response"
    
    # Registry intents
    REGISTER = "registry.register"
    DISCOVER = "registry.discover"
    
    # Custom intent creation
    @staticmethod
    def create_custom(domain: str, action: str) -> str:
        """Create a custom intent with domain and action"""
        return f"{domain}.{action}"


class Message:
    """
    Represents a message in the ReGenNexus protocol
    
    A message is the fundamental unit of communication between entities.
    """
    
    def __init__(
        self,
        sender_id: str,
        recipient_id: str,
        content: Any,
        intent: str,
        context_id: str,
        message_id: Optional[str] = None,
        timestamp: Optional[float] = None
    ):
        """
        Initialize a new message
        
        Args:
            sender_id: Identifier of the sending entity
            recipient_id: Identifier of the receiving entity
            content: The payload of the message (can be text or structured data)
            intent: The purpose or type of the message
            context_id: Identifier for the conversation context
            message_id: Optional unique identifier (generated if not provided)
            timestamp: Optional message creation time (current time if not provided)
        """
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.intent = intent
        self.context_id = context_id
        self.message_id = message_id or str(uuid.uuid4())
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "intent": self.intent,
            "context_id": self.context_id,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary representation"""
        return cls(
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            content=data["content"],
            intent=data["intent"],
            context_id=data["context_id"],
            message_id=data.get("message_id"),
            timestamp=data.get("timestamp")
        )


class Entity:
    """
    Base class for entities in the ReGenNexus protocol
    
    An entity is any component that can send or receive messages.
    """
    
    def __init__(self, entity_id: str):
        """
        Initialize a new entity
        
        Args:
            entity_id: Unique identifier for this entity
        """
        self.id = entity_id
        self.capabilities = []
    
    async def process_message(self, message: Message, context: Any) -> Optional[Message]:
        """
        Process an incoming message
        
        Args:
            message: The message to process
            context: The conversation context
            
        Returns:
            Optional response message
        """
        raise NotImplementedError("Subclasses must implement process_message")
    
    def add_capability(self, capability: str) -> None:
        """
        Add a capability to this entity
        
        Args:
            capability: String identifier for a capability
        """
        if capability not in self.capabilities:
            self.capabilities.append(capability)
    
    def has_capability(self, capability: str) -> bool:
        """
        Check if entity has a specific capability
        
        Args:
            capability: String identifier for a capability
            
        Returns:
            True if entity has the capability, False otherwise
        """
        return capability in self.capabilities
    
    def get_capabilities(self) -> List[str]:
        """
        Get all capabilities of this entity
        
        Returns:
            List of capability strings
        """
        return self.capabilities.copy()
