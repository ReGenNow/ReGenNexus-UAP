// C++ Client for Cross-Language Communication
//
// This example demonstrates how to use the ReGenNexus Core protocol from C++
// to communicate with clients written in other programming languages.
//
// This file serves as the C++ side of the cross-language demonstration.
//
// Dependencies:
// - nlohmann/json for JSON parsing (https://github.com/nlohmann/json)
// - websocketpp for WebSocket communication (https://github.com/zaphoyd/websocketpp)
// - Boost for asio and uuid generation

#include <iostream>
#include <string>
#include <map>
#include <functional>
#include <memory>
#include <chrono>
#include <thread>
#include <mutex>
#include <condition_variable>

#include <websocketpp/config/asio_client.hpp>
#include <websocketpp/client.hpp>
#include <nlohmann/json.hpp>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_generators.hpp>
#include <boost/uuid/uuid_io.hpp>

using json = nlohmann::json;
using websocket_client = websocketpp::client<websocketpp::config::asio_client>;
using message_ptr = websocketpp::config::asio_client::message_type::ptr;
using websocketpp::lib::placeholders::_1;
using websocketpp::lib::placeholders::_2;

// Logger function
void log(const std::string& message) {
    auto now = std::chrono::system_clock::now();
    auto now_c = std::chrono::system_clock::to_time_t(now);
    std::string timestamp = std::ctime(&now_c);
    timestamp.pop_back(); // Remove trailing newline
    std::cout << "[" << timestamp << "] " << message << std::endl;
}

// UAP Client class
class UAP_Client {
public:
    UAP_Client(const std::string& entity_id, const std::string& registry_url)
        : entity_id_(entity_id), registry_url_(registry_url), connected_(false) {
        
        // Set up WebSocket client
        client_.clear_access_channels(websocketpp::log::alevel::all);
        client_.set_error_channels(websocketpp::log::elevel::all);
        
        client_.init_asio();
        
        // Set up callbacks
        client_.set_open_handler(std::bind(&UAP_Client::on_open, this, _1));
        client_.set_message_handler(std::bind(&UAP_Client::on_message, this, _1, _2));
        client_.set_close_handler(std::bind(&UAP_Client::on_close, this, _1));
        client_.set_fail_handler(std::bind(&UAP_Client::on_fail, this, _1));
    }
    
    ~UAP_Client() {
        disconnect();
    }
    
    // Connect to the registry
    bool connect() {
        try {
            log("Connecting to registry at " + registry_url_ + "...");
            
            websocketpp::lib::error_code ec;
            connection_ = client_.get_connection(registry_url_, ec);
            if (ec) {
                log("Connection error: " + ec.message());
                return false;
            }
            
            client_.connect(connection_);
            
            // Start the client thread
            client_thread_ = std::thread([this]() {
                try {
                    client_.run();
                } catch (const std::exception& e) {
                    log("Client thread error: " + std::string(e.what()));
                }
            });
            
            // Wait for connection to be established
            std::unique_lock<std::mutex> lock(mutex_);
            if (!connected_) {
                cv_.wait_for(lock, std::chrono::seconds(5), [this]() { return connected_; });
            }
            
            return connected_;
        } catch (const std::exception& e) {
            log("Exception in connect: " + std::string(e.what()));
            return false;
        }
    }
    
    // Disconnect from the registry
    void disconnect() {
        if (connected_) {
            try {
                websocketpp::lib::error_code ec;
                client_.close(connection_->get_handle(), websocketpp::close::status::normal, "Disconnecting", ec);
                if (ec) {
                    log("Error closing connection: " + ec.message());
                }
                
                connected_ = false;
            } catch (const std::exception& e) {
                log("Exception in disconnect: " + std::string(e.what()));
            }
        }
        
        if (client_thread_.joinable()) {
            client_.stop();
            client_thread_.join();
        }
        
        log("Disconnected from registry");
    }
    
    // Send a message to another entity
    bool send_message(const std::string& recipient, const std::string& intent, const json& payload) {
        if (!connected_) {
            log("Not connected to registry");
            return false;
        }
        
        try {
            // Create message
            json message = {
                {"sender", entity_id_},
                {"recipient", recipient},
                {"intent", intent},
                {"payload", payload},
                {"timestamp", std::chrono::system_clock::now().time_since_epoch().count() / 1000000000.0}
            };
            
            // Send the message
            websocketpp::lib::error_code ec;
            client_.send(connection_->get_handle(), message.dump(), websocketpp::frame::opcode::text, ec);
            
            if (ec) {
                log("Error sending message: " + ec.message());
                return false;
            }
            
            log("Sent message to " + recipient + " with intent " + intent);
            return true;
        } catch (const std::exception& e) {
            log("Exception in send_message: " + std::string(e.what()));
            return false;
        }
    }
    
    // Register a message handler for a specific intent
    void register_message_handler(const std::string& intent, 
                                 std::function<void(const json&)> handler) {
        message_handlers_[intent] = handler;
        log("Registered handler for intent: " + intent);
    }
    
    // Run the client (blocking)
    void run() {
        // This is a no-op since we already started the client thread in connect()
        // Just wait for the client to be stopped
        if (client_thread_.joinable()) {
            client_thread_.join();
        }
    }
    
private:
    // WebSocket callbacks
    void on_open(websocketpp::connection_hdl hdl) {
        log("Connected to registry");
        
        // Register with the registry
        json registration_message = {
            {"type", "registration"},
            {"entity_id", entity_id_}
        };
        
        websocketpp::lib::error_code ec;
        client_.send(hdl, registration_message.dump(), websocketpp::frame::opcode::text, ec);
        
        if (ec) {
            log("Error sending registration message: " + ec.message());
            return;
        }
        
        log("Sent registration message for " + entity_id_);
        
        // Update connection status
        {
            std::lock_guard<std::mutex> lock(mutex_);
            connected_ = true;
        }
        cv_.notify_all();
    }
    
    void on_message(websocketpp::connection_hdl hdl, message_ptr msg) {
        try {
            // Parse the message
            json message = json::parse(msg->get_payload());
            log("Received message: " + message.dump());
            
            // Handle the message
            if (message.contains("intent")) {
                std::string intent = message["intent"];
                
                auto it = message_handlers_.find(intent);
                if (it != message_handlers_.end()) {
                    // Call the appropriate handler
                    it->second(message);
                } else {
                    log("No handler registered for intent: " + intent);
                }
            }
        } catch (const std::exception& e) {
            log("Error handling message: " + std::string(e.what()));
        }
    }
    
    void on_close(websocketpp::connection_hdl hdl) {
        log("Connection to registry closed");
        
        {
            std::lock_guard<std::mutex> lock(mutex_);
            connected_ = false;
        }
        cv_.notify_all();
    }
    
    void on_fail(websocketpp::connection_hdl hdl) {
        log("Connection to registry failed");
        
        {
            std::lock_guard<std::mutex> lock(mutex_);
            connected_ = false;
        }
        cv_.notify_all();
    }
    
private:
    std::string entity_id_;
    std::string registry_url_;
    bool connected_;
    
    websocket_client client_;
    websocket_client::connection_ptr connection_;
    std::thread client_thread_;
    
    std::map<std::string, std::function<void(const json&)>> message_handlers_;
    
    std::mutex mutex_;
    std::condition_variable cv_;
};

// Generate a UUID
std::string generate_uuid() {
    boost::uuids::random_generator gen;
    boost::uuids::uuid uuid = gen();
    return boost::uuids::to_string(uuid);
}

// Main function
int main() {
    // Configuration
    const std::string REGISTRY_URL = "ws://localhost:8000";
    const std::string ENTITY_ID = "cpp_client";
    
    // Create a client
    UAP_Client client(ENTITY_ID, REGISTRY_URL);
    
    try {
        // Connect to the registry
        if (!client.connect()) {
            log("Failed to connect to registry");
            return 1;
        }
        
        // Register message handlers
        client.register_message_handler("python_message", [&client](const json& message) {
            log("Received message from Python client: " + message["payload"].dump());
            
            // Process the message
            json response_data = {
                {"received", message["payload"]},
                {"processed_by", "C++"},
                {"timestamp", std::chrono::system_clock::now().time_since_epoch().count() / 1000000000.0},
                {"message", "Hello from C++ to Python!"}
            };
            
            // Send response back to Python client
            client.send_message(message["sender"], "cpp_message", response_data);
            
            log("Sent response to Python client");
        });
        
        client.register_message_handler("js_message", [&client](const json& message) {
            log("Received message from JavaScript client: " + message["payload"].dump());
            
            // Process the message
            json response_data = {
                {"received", message["payload"]},
                {"processed_by", "C++"},
                {"timestamp", std::chrono::system_clock::now().time_since_epoch().count() / 1000000000.0},
                {"message", "Hello from C++ to JavaScript!"}
            };
            
            // Send response back to JavaScript client
            client.send_message(message["sender"], "cpp_message", response_data);
            
            log("Sent response to JavaScript client");
        });
        
        client.register_message_handler("python_response", [](const json& message) {
            log("Received response from Python client: " + message["payload"].dump());
        });
        
        // Start a thread for periodic pinging
        std::thread ping_thread([&client]() {
            while (true) {
                try {
                    // Create a unique request ID
                    std::string request_id = generate_uuid();
                    
                    // Ping Python client
                    log("Pinging Python client...");
                    client.send_message("python_client", "cpp_message", {
                        {"message", "Ping from C++!"},
                        {"timestamp", std::chrono::system_clock::now().time_since_epoch().count() / 1000000000.0},
                        {"request_id", request_id}
                    });
                    
                    // Wait a bit
                    std::this_thread::sleep_for(std::chrono::seconds(2));
                    
                    // Ping JavaScript client
                    log("Pinging JavaScript client...");
                    client.send_message("js_client", "cpp_message", {
                        {"message", "Ping from C++!"},
                        {"timestamp", std::chrono::system_clock::now().time_since_epoch().count() / 1000000000.0},
                        {"request_id", request_id}
                    });
                    
                    // Wait before next ping cycle
                    std::this_thread::sleep_for(std::chrono::seconds(15));
                } catch (const std::exception& e) {
                    log("Error in ping thread: " + std::string(e.what()));
                    std::this_thread::sleep_for(std::chrono::seconds(5));
                }
            }
        });
        
        log("C++ client is running...");
        
        // Set up signal handling for clean shutdown
        // This is a simplified example - in a real application, you would use proper signal handling
        std::cout << "Press Enter to exit..." << std::endl;
        std::cin.get();
        
        // Clean up
        ping_thread.detach(); // In a real application, you would join this thread properly
        client.disconnect();
        
    } catch (const std::exception& e) {
        log("Error: " + std::string(e.what()));
        return 1;
    }
    
    return 0;
}
