// JavaScript Client for Cross-Language Communication
//
// This example demonstrates how to use the ReGenNexus Core protocol from JavaScript
// to communicate with clients written in other programming languages.
//
// This file serves as the JavaScript side of the cross-language demonstration.

const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

// Configuration
const REGISTRY_URL = 'ws://localhost:8000';
const ENTITY_ID = 'js_client';

// Set up logging
function log(message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${message}`);
}

// Create a client class
class UAP_Client {
  constructor(entityId, registryUrl) {
    this.entityId = entityId;
    this.registryUrl = registryUrl;
    this.ws = null;
    this.connected = false;
    this.messageHandlers = {};
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  // Connect to the registry
  connect() {
    return new Promise((resolve, reject) => {
      log(`Connecting to registry at ${this.registryUrl}...`);
      
      this.ws = new WebSocket(this.registryUrl);
      
      this.ws.on('open', () => {
        log('Connected to registry');
        this.connected = true;
        this.reconnectAttempts = 0;
        
        // Register with the registry
        const registrationMessage = {
          type: 'registration',
          entity_id: this.entityId
        };
        
        this.ws.send(JSON.stringify(registrationMessage));
        log(`Sent registration message for ${this.entityId}`);
        
        resolve();
      });
      
      this.ws.on('message', (data) => {
        try {
          const message = JSON.parse(data);
          log(`Received message: ${JSON.stringify(message)}`);
          
          // Handle the message
          this._handleMessage(message);
        } catch (error) {
          log(`Error handling message: ${error.message}`);
        }
      });
      
      this.ws.on('close', () => {
        log('Connection to registry closed');
        this.connected = false;
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = Math.pow(2, this.reconnectAttempts) * 1000;
          log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
          
          setTimeout(() => {
            this.connect().catch(error => {
              log(`Reconnection failed: ${error.message}`);
            });
          }, delay);
        } else {
          log('Maximum reconnection attempts reached');
        }
      });
      
      this.ws.on('error', (error) => {
        log(`WebSocket error: ${error.message}`);
        reject(error);
      });
    });
  }

  // Send a message to another entity
  sendMessage(recipient, intent, payload) {
    if (!this.connected) {
      throw new Error('Not connected to registry');
    }
    
    const message = {
      sender: this.entityId,
      recipient: recipient,
      intent: intent,
      payload: payload,
      timestamp: Date.now() / 1000
    };
    
    this.ws.send(JSON.stringify(message));
    log(`Sent message to ${recipient} with intent ${intent}`);
    
    return message;
  }

  // Register a message handler for a specific intent
  registerMessageHandler(intent, handler) {
    this.messageHandlers[intent] = handler;
    log(`Registered handler for intent: ${intent}`);
  }

  // Handle incoming messages
  _handleMessage(message) {
    const intent = message.intent;
    
    if (intent && this.messageHandlers[intent]) {
      // Call the appropriate handler
      this.messageHandlers[intent](message);
    } else {
      log(`No handler registered for intent: ${intent}`);
    }
  }

  // Disconnect from the registry
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.connected = false;
      log('Disconnected from registry');
    }
  }
}

// Main function
async function main() {
  // Create a client
  const client = new UAP_Client(ENTITY_ID, REGISTRY_URL);
  
  try {
    // Connect to the registry
    await client.connect();
    
    // Register message handlers
    client.registerMessageHandler('python_message', (message) => {
      log(`Received message from Python client: ${JSON.stringify(message.payload)}`);
      
      // Process the message
      const responseData = {
        received: message.payload,
        processed_by: 'JavaScript',
        timestamp: Date.now() / 1000,
        message: 'Hello from JavaScript to Python!'
      };
      
      // Send response back to Python client
      client.sendMessage(message.sender, 'js_message', responseData);
      
      log('Sent response to Python client');
    });
    
    client.registerMessageHandler('cpp_message', (message) => {
      log(`Received message from C++ client: ${JSON.stringify(message.payload)}`);
      
      // Process the message
      const responseData = {
        received: message.payload,
        processed_by: 'JavaScript',
        timestamp: Date.now() / 1000,
        message: 'Hello from JavaScript to C++!'
      };
      
      // Send response back to C++ client
      client.sendMessage(message.sender, 'js_message', responseData);
      
      log('Sent response to C++ client');
    });
    
    client.registerMessageHandler('python_response', (message) => {
      log(`Received response from Python client: ${JSON.stringify(message.payload)}`);
    });
    
    // Periodic ping to other language clients
    setInterval(() => {
      // Create a unique request ID
      const requestId = uuidv4();
      
      // Ping Python client
      log('Pinging Python client...');
      client.sendMessage('python_client', 'js_message', {
        message: 'Ping from JavaScript!',
        timestamp: Date.now() / 1000,
        request_id: requestId
      });
      
      // Wait a bit before pinging C++ client
      setTimeout(() => {
        // Ping C++ client
        log('Pinging C++ client...');
        client.sendMessage('cpp_client', 'js_message', {
          message: 'Ping from JavaScript!',
          timestamp: Date.now() / 1000,
          request_id: requestId
        });
      }, 2000);
    }, 12000); // Every 12 seconds
    
    log('JavaScript client is running...');
    
    // Keep the process running
    process.on('SIGINT', () => {
      log('JavaScript client terminated by user');
      client.disconnect();
      process.exit(0);
    });
  } catch (error) {
    log(`Error: ${error.message}`);
  }
}

// Run the main function
main().catch(error => {
  log(`Fatal error: ${error.message}`);
  process.exit(1);
});
