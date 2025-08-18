#!/bin/bash

# Load YAML-based configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/yaml_common.sh"

# Start sling_k2 service using YAML configuration
start_service "sling_k2"