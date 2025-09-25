import subprocess
import time
import os
import sys
import signal

# Define services and their ports
services = [
    ("detection_service.py", 5001, "Product Detection"),
    ("grouping_service.py", 5002, "Product Grouping"), 
    ("visualization_service.py", 5003, "Image Visualization"),
]

# Store process references
processes = []
basedir = os.path.dirname(__file__) or "."

def start_services():
    """Start all microservices"""
    print("Starting BrandEye Microservices...")
    print("=" * 50)
    
    try:
        for script, port, description in services:
            script_path = os.path.join(basedir, script)
            print(f"Starting {description} on port {port}...")
            
            # Start service as subprocess
            process = subprocess.Popen([sys.executable, script_path], cwd=basedir)
            processes.append((script, process, description))
            
            # Wait a bit between starting services
            time.sleep(2)
        
        print("=" * 50)
        print("All services started successfully!")
        print("Services running:")
        for script, process, description in processes:
            print(f"  - {description}: http://localhost:{services[processes.index((script, process, description))][1]}")
        
        print("\nPress Ctrl+C to stop all services")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping all services...")
        stop_services()

def stop_services():
    """Stop all running services"""
    for script, process, description in processes:
        try:
            print(f"Stopping {description}...")
            process.terminate()
            process.wait(timeout=5)  # Wait up to 5 seconds
        except subprocess.TimeoutExpired:
            print(f"Force killing {description}...")
            process.kill()
        except Exception as e:
            print(f"Error stopping {description}: {e}")
    
    print("All services stopped.")

if __name__ == '__main__':
    start_services()
