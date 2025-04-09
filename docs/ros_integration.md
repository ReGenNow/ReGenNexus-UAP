# ROS Integration Guide

This document provides detailed information about integrating ReGenNexus Core with the Robot Operating System (ROS).

## Overview

ReGenNexus Core includes a ROS bridge that enables seamless communication between ReGenNexus entities and ROS nodes. The bridge supports both ROS 1 and ROS 2, with a focus on ROS 2 for future compatibility.

## ROS Bridge Architecture

The ROS bridge acts as a translator between the ReGenNexus protocol and ROS communication mechanisms:

- **Topic Mapping**: Maps ReGenNexus messages to ROS topics and vice versa
- **Service Integration**: Exposes ROS services to ReGenNexus entities
- **Action Support**: Bridges ReGenNexus intents to ROS actions
- **Parameter Access**: Provides access to the ROS parameter server

## Prerequisites

Before using the ROS bridge, ensure you have:

1. ROS 1 (Noetic) or ROS 2 (Foxy/Galactic/Humble) installed
2. ReGenNexus Core installed
3. Python 3.8 or higher

## Installation

### ROS 1 Dependencies

```bash
# Install ROS 1 bridge dependencies
pip install rospkg rospy
```

### ROS 2 Dependencies

```bash
# Install ROS 2 bridge dependencies
pip install rclpy
```

## Basic Usage

### Initializing the ROS Bridge

```python
import asyncio
from regennexus.bridges.ros_bridge import ROSBridge
from regennexus.protocol.client import UAP_Client

async def main():
    # Create a ROS bridge
    ros_bridge = ROSBridge(node_name="regennexus_bridge")
    
    # Initialize the bridge
    await ros_bridge.initialize()
    
    # Create a ReGenNexus client
    client = UAP_Client(entity_id="ros_agent", registry_url="localhost:8000")
    
    # Register the bridge with the client
    client.register_bridge(ros_bridge)
    
    # Connect to the registry
    await client.connect()
    
    # Keep the client running
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## Topic Subscription

### Subscribing to ROS Topics

```python
# Subscribe to a ROS topic
subscription = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="create_topic_subscription",
    parameters={
        "topic_name": "/robot/sensors/imu",
        "message_type": "sensor_msgs/Imu",
        "callback_intent": "process_imu_data"
    }
)

# Define a message handler for the subscription
@client.message_handler(intent="process_imu_data")
async def handle_imu_data(message):
    imu_data = message.payload
    print(f"Received IMU data: {imu_data}")
    
    # Process the data
    # ...
```

### Publishing to ROS Topics

```python
# Create a publisher for a ROS topic
publisher = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="create_topic_publisher",
    parameters={
        "topic_name": "/robot/cmd_vel",
        "message_type": "geometry_msgs/Twist"
    }
)

# Publish a message to the topic
await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="publish_message",
    parameters={
        "publisher_id": publisher["publisher_id"],
        "message": {
            "linear": {"x": 0.5, "y": 0.0, "z": 0.0},
            "angular": {"x": 0.0, "y": 0.0, "z": 0.2}
        }
    }
)
```

## Service Integration

### Calling ROS Services

```python
# Call a ROS service
result = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="call_service",
    parameters={
        "service_name": "/robot/set_mode",
        "service_type": "std_srvs/SetBool",
        "request": {"data": True}
    }
)

print(f"Service response: {result['response']}")
```

### Creating ROS Services

```python
# Define a service handler
async def handle_get_status(request):
    # Process the request
    # ...
    return {"success": True, "message": "Status retrieved", "data": {"battery": 85}}

# Create a ROS service
service = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="create_service",
    parameters={
        "service_name": "/regennexus/get_status",
        "service_type": "regennexus_msgs/GetStatus",
        "handler": handle_get_status
    }
)
```

## Action Support

### Using ROS Actions

```python
# Send a goal to a ROS action server
goal_handle = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="send_action_goal",
    parameters={
        "action_name": "/robot/navigate",
        "action_type": "nav_msgs/NavigateToPose",
        "goal": {
            "pose": {
                "position": {"x": 1.0, "y": 2.0, "z": 0.0},
                "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
            }
        },
        "feedback_intent": "navigation_feedback",
        "result_intent": "navigation_result"
    }
)

# Define handlers for feedback and result
@client.message_handler(intent="navigation_feedback")
async def handle_navigation_feedback(message):
    feedback = message.payload
    print(f"Navigation progress: {feedback['progress']}%")

@client.message_handler(intent="navigation_result")
async def handle_navigation_result(message):
    result = message.payload
    print(f"Navigation completed: {result['success']}")
```

### Creating ROS Action Servers

```python
# Define action handlers
async def handle_execute_task(goal):
    # Process the goal
    # ...
    
    # Send feedback
    await goal.publish_feedback({"progress": 50})
    
    # Return result
    return {"success": True, "message": "Task completed"}

# Create a ROS action server
action_server = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="create_action_server",
    parameters={
        "action_name": "/regennexus/execute_task",
        "action_type": "regennexus_msgs/ExecuteTask",
        "execute_callback": handle_execute_task
    }
)
```

## Parameter Access

### Reading ROS Parameters

```python
# Get a parameter from the ROS parameter server
param_value = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="get_parameter",
    parameters={"name": "robot_name"}
)

print(f"Robot name: {param_value['value']}")
```

### Setting ROS Parameters

```python
# Set a parameter on the ROS parameter server
await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="set_parameter",
    parameters={
        "name": "max_velocity",
        "value": 1.5,
        "type": "double"
    }
)
```

## Advanced Features

### TF Integration

```python
# Get a transform from the TF tree
transform = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="lookup_transform",
    parameters={
        "target_frame": "base_link",
        "source_frame": "map",
        "time": 0  # latest
    }
)

print(f"Transform: {transform}")

# Broadcast a transform
await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="broadcast_transform",
    parameters={
        "transform": {
            "header": {
                "frame_id": "base_link"
            },
            "child_frame_id": "sensor",
            "transform": {
                "translation": {"x": 0.1, "y": 0.0, "z": 0.2},
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
            }
        }
    }
)
```

### Message Conversion

```python
# Convert a ROS message to a ReGenNexus message
uap_message = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="convert_ros_to_uap",
    parameters={
        "ros_message": ros_message,
        "intent": "sensor_data"
    }
)

# Convert a ReGenNexus message to a ROS message
ros_message = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="convert_uap_to_ros",
    parameters={
        "uap_message": uap_message,
        "message_type": "sensor_msgs/LaserScan"
    }
)
```

## Working with ROS 2

The ROS bridge automatically detects whether you're using ROS 1 or ROS 2. For ROS 2 specific features:

```python
# Create a ROS 2 Quality of Service profile
qos_profile = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="create_qos_profile",
    parameters={
        "reliability": "reliable",
        "durability": "transient_local",
        "history": "keep_last",
        "history_depth": 10
    }
)

# Create a publisher with the QoS profile
publisher = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="create_topic_publisher",
    parameters={
        "topic_name": "/robot/status",
        "message_type": "std_msgs/String",
        "qos_profile": qos_profile
    }
)
```

## Integration with Robotics Frameworks

### Integration with Navigation2

```python
# Send a navigation goal
nav_goal = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="navigate_to_pose",
    parameters={
        "position": {"x": 1.0, "y": 2.0, "z": 0.0},
        "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        "behavior_tree": "navigate_w_replanning"
    }
)
```

### Integration with MoveIt

```python
# Plan and execute a motion
motion_result = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="plan_and_execute",
    parameters={
        "group_name": "arm",
        "target_pose": {
            "position": {"x": 0.5, "y": 0.0, "z": 0.5},
            "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
        }
    }
)
```

## Best Practices

1. **Message Type Handling**
   - Use standard ROS message types when possible
   - Create custom message types for specialized data
   - Document message type requirements

2. **Error Handling**
   - Implement proper error handling for ROS operations
   - Use try-except blocks for service calls
   - Handle timeouts appropriately

3. **Resource Management**
   - Clean up subscribers, publishers, and services when no longer needed
   - Use context managers for resource acquisition
   - Monitor resource usage in long-running applications

4. **Performance Optimization**
   - Use appropriate QoS settings for your use case
   - Implement message filtering for high-frequency topics
   - Consider using compressed message formats for large data

5. **Security**
   - Use ROS 2 security features when available
   - Implement access control for sensitive operations
   - Validate all input parameters

## Troubleshooting

### Common Issues

1. **Connection Problems**
   - Ensure ROS master is running (ROS 1)
   - Check ROS_DOMAIN_ID (ROS 2)
   - Verify network connectivity

2. **Message Type Errors**
   - Ensure message types are correctly specified
   - Check for typos in message field names
   - Verify message package dependencies

3. **Timing Issues**
   - Use proper synchronization mechanisms
   - Implement retry logic for transient failures
   - Consider using time synchronization for distributed systems

### Debugging Tools

```python
# Enable debug logging
await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="set_log_level",
    parameters={"level": "debug"}
)

# Get bridge status
status = await client.execute_bridge_action(
    bridge_id="ros_bridge",
    action="get_status"
)
print(f"Bridge status: {status}")
```
