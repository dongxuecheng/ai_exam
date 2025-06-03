#!/usr/bin/env python3
"""
GPU Configuration Checker for AI Exam Services
This script checks if GPU configurations are properly loaded from YAML.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.utils.config import get_service_config, get_service_names

def check_gpu_configurations():
    """Check GPU configurations for all services."""
    print("AI Exam Services - GPU Configuration Check")
    print("=" * 50)
    
    try:
        service_names = get_service_names()
        print(f"Found {len(service_names)} services:\n")
        
        for service_name in service_names:
            try:
                config = get_service_config(service_name)
                gpu_device = config.gpu_device
                
                print(f"Service: {service_name}")
                print(f"  GPU Device: {gpu_device}")
                print(f"  Server Port: {config.server_port}")
                print(f"  Models: {len(config.weights_paths)}")
                print(f"  Streams: {len(config.stream_configs)}")
                print()
                
            except Exception as e:
                print(f"Error loading config for {service_name}: {e}")
                print()
                
    except Exception as e:
        print(f"Error loading service names: {e}")
        return False
    
    return True

def check_gpu_availability():
    """Check if CUDA GPUs are available."""
    print("GPU Availability Check")
    print("=" * 30)
    
    try:
        import torch
        
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            print(f"CUDA Available: Yes")
            print(f"GPU Count: {gpu_count}")
            
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                print(f"  GPU {i}: {gpu_name}")
                
        else:
            print("CUDA Available: No")
            print("Running in CPU mode")
            
    except ImportError:
        print("PyTorch not available - cannot check GPU status")
    
    print()

def main():
    """Main function."""
    print("Checking GPU configurations...\n")
    
    # Check GPU availability
    check_gpu_availability()
    
    # Check service configurations
    success = check_gpu_configurations()
    
    if success:
        print("✅ GPU configuration check completed successfully!")
    else:
        print("❌ GPU configuration check failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
