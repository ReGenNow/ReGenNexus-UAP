"""
ReGenNexus Core - Jetson Plugin Module

This module implements integration with NVIDIA Jetson devices,
providing access to Jetson-specific features like CUDA acceleration,
camera interfaces, and GPIO.
"""

import os
import json
import logging
import subprocess
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class JetsonPlugin:
    """
    Plugin for NVIDIA Jetson devices.
    
    Provides access to Jetson-specific features and capabilities.
    """
    
    def __init__(self):
        """Initialize the Jetson plugin."""
        self.jetson_initialized = False
        self.jetson_model = None
        self.cuda_available = False
        self.camera_devices = {}
        self.gpio_pins = {}
        
    async def initialize(self):
        """Initialize the Jetson plugin."""
        try:
            # Check if running on a Jetson device
            if not os.path.exists('/etc/nv_tegra_release'):
                logger.warning("Not running on a Jetson device. Jetson plugin will be disabled.")
                return
            
            # Detect Jetson model
            self.jetson_model = self._detect_jetson_model()
            
            # Check CUDA availability
            self.cuda_available = self._check_cuda_availability()
            
            # Detect camera devices
            self.camera_devices = self._detect_camera_devices()
            
            # Initialize GPIO
            self._initialize_gpio()
            
            self.jetson_initialized = True
            logger.info(f"Jetson plugin initialized for model: {self.jetson_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Jetson plugin: {e}")
            self.jetson_initialized = False
    
    def _detect_jetson_model(self) -> str:
        """
        Detect the Jetson model.
        
        Returns:
            Jetson model name
        """
        try:
            # Try to use the Jetson-specific utility
            result = subprocess.run(['cat', '/proc/device-tree/model'], 
                                   capture_output=True, text=True, check=True)
            model = result.stdout.strip()
            
            # Map to common names
            if 'Nano' in model:
                return 'Jetson Nano'
            elif 'Xavier NX' in model:
                return 'Jetson Xavier NX'
            elif 'AGX Xavier' in model:
                return 'Jetson AGX Xavier'
            elif 'Orin Nano' in model:
                return 'Jetson Orin Nano'
            elif 'Orin NX' in model:
                return 'Jetson Orin NX'
            elif 'AGX Orin' in model:
                return 'Jetson AGX Orin'
            else:
                return model
            
        except Exception as e:
            logger.error(f"Failed to detect Jetson model: {e}")
            return "Unknown Jetson"
    
    def _check_cuda_availability(self) -> bool:
        """
        Check if CUDA is available.
        
        Returns:
            True if CUDA is available, False otherwise
        """
        try:
            # Check for CUDA libraries
            cuda_path = '/usr/local/cuda'
            if not os.path.exists(cuda_path):
                return False
            
            # Try to run nvidia-smi
            result = subprocess.run(['nvidia-smi'], 
                                   capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to check CUDA availability: {e}")
            return False
    
    def _detect_camera_devices(self) -> Dict[str, Dict[str, Any]]:
        """
        Detect available camera devices.
        
        Returns:
            Dictionary of camera devices
        """
        cameras = {}
        
        try:
            # Check for V4L2 devices
            if os.path.exists('/dev/video0'):
                # Get camera info using v4l2-ctl
                for i in range(10):  # Check up to 10 cameras
                    device_path = f'/dev/video{i}'
                    if not os.path.exists(device_path):
                        continue
                    
                    try:
                        result = subprocess.run(['v4l2-ctl', '--device', device_path, '--all'], 
                                              capture_output=True, text=True)
                        
                        # Extract camera info
                        camera_info = {
                            'path': device_path,
                            'type': 'v4l2'
                        }
                        
                        # Try to extract camera name
                        for line in result.stdout.split('\n'):
                            if 'Card type' in line:
                                camera_info['name'] = line.split(':')[1].strip()
                                break
                        
                        cameras[f'camera{i}'] = camera_info
                        
                    except Exception as e:
                        logger.error(f"Failed to get info for camera {device_path}: {e}")
            
            # Check for CSI cameras
            csi_path = '/dev/video0'
            if os.path.exists(csi_path):
                cameras['csi0'] = {
                    'path': csi_path,
                    'type': 'csi',
                    'name': 'CSI Camera'
                }
                
        except Exception as e:
            logger.error(f"Failed to detect camera devices: {e}")
        
        return cameras
    
    def _initialize_gpio(self):
        """Initialize GPIO pins."""
        try:
            # Try to import Jetson.GPIO
            import Jetson.GPIO as GPIO
            
            # Set up GPIO
            GPIO.setmode(GPIO.BOARD)
            
            # Map available pins
            for pin in range(1, 41):
                try:
                    # Check if pin is valid
                    if pin in [1, 2, 4, 6, 9, 14, 17, 20, 25, 30, 34, 39]:
                        # Power or ground pins
                        continue
                    
                    self.gpio_pins[pin] = {
                        'pin': pin,
                        'mode': 'input',  # Default mode
                        'state': None
                    }
                    
                except Exception:
                    # Skip pins that can't be initialized
                    pass
            
            logger.debug(f"Initialized {len(self.gpio_pins)} GPIO pins")
            
        except ImportError:
            logger.warning("Jetson.GPIO module not found. GPIO functionality will be disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {e}")
    
    async def get_device_info(self) -> Dict[str, Any]:
        """
        Get information about the Jetson device.
        
        Returns:
            Dictionary of device information
        """
        if not self.jetson_initialized:
            return {'error': 'Jetson plugin not initialized'}
        
        info = {
            'model': self.jetson_model,
            'cuda_available': self.cuda_available,
            'camera_devices': list(self.camera_devices.keys()),
            'gpio_pins': list(self.gpio_pins.keys())
        }
        
        # Get additional system info
        try:
            # Get CPU info
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            
            # Extract CPU count
            cpu_count = cpuinfo.count('processor')
            info['cpu_count'] = cpu_count
            
            # Get memory info
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            # Extract total memory
            for line in meminfo.split('\n'):
                if 'MemTotal' in line:
                    mem_kb = int(line.split(':')[1].strip().split(' ')[0])
                    info['memory_mb'] = mem_kb // 1024
                    break
            
            # Get CUDA info if available
            if self.cuda_available:
                try:
                    result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,compute_cap', '--format=csv,noheader'], 
                                          capture_output=True, text=True, check=True)
                    
                    gpu_info = result.stdout.strip().split(',')
                    info['gpu'] = {
                        'name': gpu_info[0].strip(),
                        'memory': gpu_info[1].strip(),
                        'compute_capability': gpu_info[2].strip()
                    }
                except Exception as e:
                    logger.error(f"Failed to get GPU info: {e}")
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
        
        return info
    
    async def set_gpio_mode(self, pin: int, mode: str) -> bool:
        """
        Set the mode of a GPIO pin.
        
        Args:
            pin: Pin number
            mode: Pin mode ('input' or 'output')
            
        Returns:
            True if successful, False otherwise
        """
        if not self.jetson_initialized or pin not in self.gpio_pins:
            return False
        
        try:
            import Jetson.GPIO as GPIO
            
            if mode == 'input':
                GPIO.setup(pin, GPIO.IN)
            elif mode == 'output':
                GPIO.setup(pin, GPIO.OUT)
            else:
                logger.error(f"Invalid GPIO mode: {mode}")
                return False
            
            self.gpio_pins[pin]['mode'] = mode
            return True
            
        except Exception as e:
            logger.error(f"Failed to set GPIO mode: {e}")
            return False
    
    async def set_gpio_value(self, pin: int, value: int) -> bool:
        """
        Set the value of a GPIO pin.
        
        Args:
            pin: Pin number
            value: Pin value (0 or 1)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.jetson_initialized or pin not in self.gpio_pins:
            return False
        
        if self.gpio_pins[pin]['mode'] != 'output':
            logger.error(f"Pin {pin} is not set as output")
            return False
        
        try:
            import Jetson.GPIO as GPIO
            
            GPIO.output(pin, value)
            self.gpio_pins[pin]['state'] = value
            return True
            
        except Exception as e:
            logger.error(f"Failed to set GPIO value: {e}")
            return False
    
    async def get_gpio_value(self, pin: int) -> Optional[int]:
        """
        Get the value of a GPIO pin.
        
        Args:
            pin: Pin number
            
        Returns:
            Pin value (0 or 1) or None if failed
        """
        if not self.jetson_initialized or pin not in self.gpio_pins:
            return None
        
        try:
            import Jetson.GPIO as GPIO
            
            value = GPIO.input(pin)
            self.gpio_pins[pin]['state'] = value
            return value
            
        except Exception as e:
            logger.error(f"Failed to get GPIO value: {e}")
            return None
    
    async def capture_image(self, camera_id: str, width: int = 640, height: int = 480) -> Optional[bytes]:
        """
        Capture an image from a camera.
        
        Args:
            camera_id: Camera identifier
            width: Image width
            height: Image height
            
        Returns:
            Image data as bytes or None if failed
        """
        if not self.jetson_initialized or camera_id not in self.camera_devices:
            return None
        
        try:
            # Try to use OpenCV
            import cv2
            
            camera_path = self.camera_devices[camera_id]['path']
            cap = cv2.VideoCapture(camera_path)
            
            # Set resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Capture frame
            ret, frame = cap.read()
            
            # Release camera
            cap.release()
            
            if not ret:
                logger.error(f"Failed to capture image from camera {camera_id}")
                return None
            
            # Encode image as JPEG
            _, img_encoded = cv2.imencode('.jpg', frame)
            return img_encoded.tobytes()
            
        except ImportError:
            logger.error("OpenCV not found. Cannot capture image.")
            return None
        except Exception as e:
            logger.error(f"Failed to capture image: {e}")
            return None
    
    async def run_inference(self, model_path: str, input_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Run inference using TensorRT.
        
        Args:
            model_path: Path to the TensorRT model
            input_data: Input data
            
        Returns:
            Inference results or None if failed
        """
        if not self.jetson_initialized or not self.cuda_available:
            return None
        
        try:
            # This is a simplified example. In a real implementation,
            # you would use TensorRT Python API to load the model and run inference.
            logger.warning("TensorRT inference not fully implemented in this example")
            
            # Placeholder for inference results
            results = {
                'status': 'success',
                'model': model_path,
                'results': [
                    {'label': 'example', 'confidence': 0.95}
                ]
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to run inference: {e}")
            return None
