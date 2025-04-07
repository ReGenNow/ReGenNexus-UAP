"""
Protocol Basics Tutorial - Step by Step Introduction to ReGenNexus UAP
This tutorial provides a step-by-step introduction to the core concepts of the 
ReGenNexus Universal Agent Protocol. It demonstrates:

1. Creating and understanding Message objects
2. Working with Entity classes
3. Using the Registry for message routing
4. Managing conversation context
5. Handling different message intents

This example is designed to be educational and includes detailed comments
explaining each concept and operation.
"""

import asyncio
import json
from regennexus.protocol.protocol_core import Message, Entity, Intent
from regennexus.registry.registry import Registry
from regennexus.context.context_manager import ContextManager

# Step 1: Understanding the Message class
# Messages are the fundamental unit of communication in ReGenNexus UAP
def explain_message_structure():
    """Create and explain a basic message structure"""
    print("\n=== STEP 1: Understanding Messages ===")
    
    # Create a simple message
    message = Message(
        sender_id="tutorial-sender",      # Who is sending the message
        recipient_id="tutorial-receiver", # Who should receive the message
        content="Hello, ReGenNexus!",     # The actual content/payload
        intent="greeting",                # The purpose/type of the message
        context_id="tutorial-context"     # Which conversation this belongs to
    )
    
    # Explain the message structure
    print("A Message object contains:")
    print(f"- sender_id: '{message.sender_id}' (identifies who sent the message)")
    print(f"- recipient_id: '{message.recipient_id}' (identifies who should receive it)")
    print(f"- content: '{message.content}' (the actual payload, can be string or dict)")
    print(f"- intent: '{message.intent}' (describes the purpose of the message)")
    print(f"- context_id: '{message.context_id}' (groups messages in a conversation)")
    print(f"- message_id: '{message.message_id}' (unique identifier, auto-generated)")
    print(f"- timestamp: {message.timestamp} (when the message was created)")
    
    # Show how content can be structured data
    structured_message = Message(
        sender_id="tutorial-sender",
        recipient_id="tutorial-receiver",
        content={
            "temperature": 22.5,
            "unit": "celsius",
            "location": "server-room"
        },
        intent="sensor.reading",
        context_id="tutorial-context"
    )
    
    print("\nMessages can contain structured data:")
    print(f"Content: {json.dumps(structured_message.content, indent=2)}")
    
    return message

# Step 2: Creating Entity classes
# Entities are the participants in the communication system
class TutorialEntity(Entity):
    """A simple entity implementation for the tutorial"""
    
    def __init__(self, entity_id, name):
        super().__init__(entity_id)
        self.name = name
        self.received_messages = []
        
    async def process_message(self, message, context):
        """Process an incoming message and optionally return a response"""
        print(f"{self.name} received: {message.content}")
        self.received_messages.append(message)
        
        # Different responses based on intent
        if message.intent == "greeting":
            # Respond to a greeting
            return Message(
                sender_id=self.id,
                recipient_id=message.sender_id,
                content=f"Hello from {self.name}!",
                intent="greeting.response",
                context_id=message.context_id
            )
        
        elif message.intent == "query":
            # Respond to a query
            return Message(
                sender_id=self.id,
                recipient_id=message.sender_id,
                content={
                    "answer": f"This is {self.name}'s response to your query",
                    "query_received": message.content
                },
                intent="query.response",
                context_id=message.context_id
            )
        
        # No response for other intents
        return None

def explain_entity_concept():
    """Explain the Entity concept"""
    print("\n=== STEP 2: Understanding Entities ===")
    print("Entities are the participants in the communication system.")
    print("Each Entity:")
    print("- Has a unique ID")
    print("- Can process incoming messages")
    print("- Can generate response messages")
    print("- Implements application-specific logic")
    print("\nEntities are implemented by extending the Entity base class")
    print("and implementing the process_message() method.")

# Step 3: Using the Registry for message routing
async def demonstrate_registry():
    """Demonstrate how the Registry works for message routing"""
    print("\n=== STEP 3: Using the Registry ===")
    print("The Registry:")
    print("- Keeps track of all available entities")
    print("- Routes messages to the correct recipient")
    print("- Handles entity registration and discovery")
    
    # Create a registry
    registry = Registry()
    
    # Create two entities
    alice = TutorialEntity("alice", "Alice")
    bob = TutorialEntity("bob", "Bob")
    
    # Register the entities with the registry
    print("\nRegistering entities with the registry...")
    await registry.register_entity(alice)
    await registry.register_entity(bob)
    
    # List registered entities
    entities = await registry.list_entities()
    print(f"Registered entities: {', '.join(entities)}")
    
    # Create a message from Alice to Bob
    message = Message(
        sender_id=alice.id,
        recipient_id=bob.id,
        content="Hi Bob, how are you?",
        intent="greeting",
        context_id="tutorial-context"
    )
    
    # Route the message through the registry
    print("\nRouting message from Alice to Bob...")
    response = await registry.route_message(message)
    
    # If there's a response, route it back
    if response:
        print("Received response from Bob, routing back to Alice...")
        await registry.route_message(response)
    
    # Show messages received by each entity
    print(f"\nAlice has received {len(alice.received_messages)} messages")
    print(f"Bob has received {len(bob.received_messages)} messages")
    
    return registry, alice, bob

# Step 4: Managing conversation context
async def demonstrate_context_management(registry, alice, bob):
    """Demonstrate how context management works"""
    print("\n=== STEP 4: Managing Conversation Context ===")
    print("The ContextManager:")
    print("- Keeps track of conversation history")
    print("- Groups related messages together")
    print("- Provides conversation state and metadata")
    
    # Create a context manager
    context_manager = ContextManager()
    
    # Create a new context
    context = await context_manager.create_context()
    print(f"Created new context with ID: {context.id}")
    
    # Exchange a series of messages in this context
    messages = [
        Message(
            sender_id=alice.id,
            recipient_id=bob.id,
            content="Do you have the project report?",
            intent="query",
            context_id=context.id
        ),
        Message(
            sender_id=bob.id,
            recipient_id=alice.id,
            content="Yes, I'll send it right away.",
            intent="response",
            context_id=context.id
        ),
        Message(
            sender_id=bob.id,
            recipient_id=alice.id,
            content={"file": "project_report.pdf", "size": "2.5MB"},
            intent="file.transfer",
            context_id=context.id
        )
    ]
    
    # Add messages to the context
    print("\nExchanging messages in the context...")
    for message in messages:
        await context_manager.add_message_to_context(message)
        print(f"Added message: {message.intent} from {message.sender_id} to {message.recipient_id}")
    
    # Retrieve and display the conversation history
    updated_context = await context_manager.get_context(context.id)
    print(f"\nContext {context.id} now contains {len(updated_context.messages)} messages:")
    for i, msg in enumerate(updated_context.messages):
        print(f"{i+1}. {msg.sender_id} → {msg.recipient_id}: {msg.intent}")
        if isinstance(msg.content, dict):
            print(f"   Content: {json.dumps(msg.content, indent=3)}")
        else:
            print(f"   Content: {msg.content}")
    
    return context_manager, context

# Step 5: Handling different message intents
async def demonstrate_intents(registry, alice, bob, context):
    """Demonstrate how different message intents are handled"""
    print("\n=== STEP 5: Working with Message Intents ===")
    print("Message intents:")
    print("- Define the purpose or type of a message")
    print("- Help entities determine how to process messages")
    print("- Can form hierarchical categories with dot notation")
    print("- Enable protocol extensibility")
    
    # Create messages with different intents
    intents = [
        "query", 
        "command.start", 
        "data.sensor.temperature",
        "notification.warning"
    ]
    
    print("\nSending messages with different intents:")
    for intent in intents:
        message = Message(
            sender_id=alice.id,
            recipient_id=bob.id,
            content=f"This is a message with intent: {intent}",
            intent=intent,
            context_id=context.id
        )
        
        print(f"\nRouting message with intent '{intent}'...")
        response = await registry.route_message(message)
        
        if response:
            print(f"Received response with intent '{response.intent}'")
            if intent == "query":
                print(f"Response content: {json.dumps(response.content, indent=2)}")
        else:
            print("No response received (entity didn't generate a response for this intent)")

async def main():
    """Run the complete tutorial"""
    print("==================================================")
    print("  ReGenNexus UAP - Protocol Basics Tutorial")
    print("==================================================")
    print("This tutorial will guide you through the core concepts")
    print("of the ReGenNexus Universal Agent Protocol.")
    
    # Step 1: Message structure
    message = explain_message_structure()
    
    # Step 2: Entity concept
    explain_entity_concept()
    
    # Step 3: Registry for message routing
    registry, alice, bob = await demonstrate_registry()
    
    # Step 4: Context management
    context_manager, context = await demonstrate_context_management(registry, alice, bob)
    
    # Step 5: Message intents
    await demonstrate_intents(registry, alice, bob, context)
    
    print("\n==================================================")
    print("  Tutorial Complete!")
    print("==================================================")
    print("You've learned the core concepts of ReGenNexus UAP:")
    print("1. Message structure and creation")
    print("2. Entity implementation and behavior")
    print("3. Registry for entity discovery and message routing")
    print("4. Context management for conversation tracking")
    print("5. Message intents for protocol extensibility")
    print("\nNext steps:")
    print("- Explore the other examples in the examples/ directory")
    print("- Read the documentation in the docs/ directory")
    print("- Try implementing your own entities and applications")

if __name__ == "__main__":
    asyncio.run(main())
