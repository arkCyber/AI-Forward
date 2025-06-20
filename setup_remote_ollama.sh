#!/bin/bash
# ==============================================================================
# Remote Ollama Setup Script
# ==============================================================================
# Description: Automated setup for using remote Ollama server with AI Gateway
# Author: Assistant
# Created: 2024-12-19
# Version: 1.0
#
# This script helps configure your AI Gateway to use a remote Ollama server
# instead of running Ollama locally in Docker.
# ==============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    log "Checking dependencies..."
    
    local deps=("docker" "docker-compose" "curl" "python3")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error "$dep is required but not installed."
            exit 1
        fi
    done
    
    log "✅ All dependencies are installed"
}

# Get user input for remote Ollama configuration
get_ollama_config() {
    log "Configuring remote Ollama connection..."
    
    # Get Ollama server URL
    while true; do
        read -p "Enter your remote Ollama server URL (e.g., http://192.168.1.100:11434): " OLLAMA_URL
        
        if [[ $OLLAMA_URL =~ ^https?://[^[:space:]]+:[0-9]+$ ]]; then
            break
        else
            error "Invalid URL format. Please use format: http://IP:PORT or https://DOMAIN:PORT"
        fi
    done
    
    # Test connection
    info "Testing connection to $OLLAMA_URL..."
    if curl -s --connect-timeout 10 "$OLLAMA_URL/api/tags" > /dev/null; then
        log "✅ Successfully connected to remote Ollama server"
    else
        error "❌ Cannot connect to remote Ollama server at $OLLAMA_URL"
        error "Please check:"
        error "  1. Server is running and accessible"
        error "  2. Firewall allows port 11434"
        error "  3. Ollama is configured to listen on 0.0.0.0:11434"
        exit 1
    fi
    
    # Get API keys (optional)
    echo
    info "Enter your API keys (press Enter to skip):"
    read -p "OpenAI API Key: " OPENAI_KEY
    read -p "DeepSeek API Key: " DEEPSEEK_KEY
    read -p "LingyiWanwu API Key: " LINGYIWANWU_KEY
}

# Create environment file
create_env_file() {
    log "Creating environment configuration..."
    
    cat > .env << EOF
# ==============================================================================
# Environment Variables for Remote Ollama Setup
# Generated by setup_remote_ollama.sh on $(date)
# ==============================================================================

# Remote Ollama Server Configuration
OLLAMA_REMOTE_URL=${OLLAMA_URL}

# Ollama Configuration
OLLAMA_TIMEOUT=60
OLLAMA_HEALTH_CHECK=true
OLLAMA_MODELS=llama3.2,qwen2,codegemma

# API Keys Configuration
OPENAI_API_KEY=${OPENAI_KEY:-}
DEEPSEEK_API_KEY=${DEEPSEEK_KEY:-}
LINGYIWANWU_API_KEY=${LINGYIWANWU_KEY:-}

# Service Configuration
OPENAI_FORWARD_LOG_LEVEL=INFO
WEBUI_LOG_LEVEL=INFO
ROUTER_LOG_LEVEL=INFO

# Load Balancing & Health Checks
LOAD_BALANCE_STRATEGY=round_robin
HEALTH_CHECK_INTERVAL=30
CHECK_INTERVAL=30

# Network & Performance Settings
CONNECTION_POOL_MAXSIZE=100
CONNECTION_RETRIES=3
REQUEST_TIMEOUT=60

# Monitoring Configuration
MONITORING_PORT=8002
SERVICES_TO_MONITOR=openai-forward:8000,webui:8001,ai-router:9000
EOF

    log "✅ Environment file created: .env"
}

# Update configuration file with remote Ollama URL
update_config_file() {
    log "Updating configuration file..."
    
    # Update the remote Ollama configuration file
    sed "s|YOUR_REMOTE_OLLAMA_IP:11434|${OLLAMA_URL#http://}|g" \
        openai-forward-config-remote-ollama.yaml > openai-forward-config-active.yaml
    
    log "✅ Configuration file updated: openai-forward-config-active.yaml"
}

# Test remote Ollama connection
test_remote_connection() {
    log "Running comprehensive connection test..."
    
    if [ -f "test_remote_ollama.py" ]; then
        python3 test_remote_ollama.py "$OLLAMA_URL"
        if [ $? -eq 0 ]; then
            log "✅ All remote Ollama tests passed!"
        else
            warning "Some tests failed. You may still proceed, but check the remote server."
        fi
    else
        warning "Test script not found. Skipping detailed tests."
    fi
}

# Start services
start_services() {
    log "Starting AI Gateway services with remote Ollama..."
    
    # Stop any existing services
    docker-compose down 2>/dev/null || true
    
    # Start services with remote Ollama configuration
    docker-compose -f docker-compose-remote-ollama.yaml up -d
    
    if [ $? -eq 0 ]; then
        log "✅ Services started successfully!"
        
        # Wait for services to be ready
        sleep 10
        
        # Check service health
        info "Checking service health..."
        
        services=("nginx:80" "openai-forward:8000" "webui:8001" "ai-router:9000" "monitoring:8002")
        for service in "${services[@]}"; do
            service_name="${service%:*}"
            port="${service#*:}"
            
            if curl -s --connect-timeout 5 "http://localhost:$port/health" > /dev/null 2>&1 || \
               curl -s --connect-timeout 5 "http://localhost:$port/" > /dev/null 2>&1; then
                log "✅ $service_name is healthy"
            else
                warning "⚠️  $service_name may not be ready yet"
            fi
        done
        
    else
        error "Failed to start services. Check Docker logs for details."
        exit 1
    fi
}

# Display final information
show_final_info() {
    log "🎉 Remote Ollama setup completed successfully!"
    
    echo
    echo "================================================================================"
    echo "                         🚀 AI Gateway - Remote Ollama Ready"
    echo "================================================================================"
    echo
    echo "📍 Service Endpoints:"
    echo "   • AI Gateway (NGINX):     http://localhost"
    echo "   • OpenAI Forward Proxy:   http://localhost:8000"
    echo "   • WebUI Management:       http://localhost:8001"
    echo "   • Smart AI Router:        http://localhost:9000"
    echo "   • System Monitoring:      http://localhost:8002"
    echo
    echo "🔗 Remote Ollama Server:     $OLLAMA_URL"
    echo
    echo "📋 API Usage Examples:"
    echo "   # Via NGINX Gateway (Recommended)"
    echo "   curl -X POST http://localhost/ollama/v1/chat/completions \\"
    echo "        -H \"Content-Type: application/json\" \\"
    echo "        -d '{\"model\":\"llama3.2\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
    echo
    echo "   # Direct to OpenAI Forward"  
    echo "   curl -X POST http://localhost:8000/ollama/v1/chat/completions \\"
    echo "        -H \"Content-Type: application/json\" \\"
    echo "        -d '{\"model\":\"llama3.2\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
    echo
    echo "🔧 Management Commands:"
    echo "   • View logs:    docker-compose -f docker-compose-remote-ollama.yaml logs -f"
    echo "   • Stop all:     docker-compose -f docker-compose-remote-ollama.yaml down"
    echo "   • Restart:      docker-compose -f docker-compose-remote-ollama.yaml restart"
    echo "   • Monitor:      python3 monitor_system.py"
    echo
    echo "📁 Configuration Files:"
    echo "   • Environment:  .env"
    echo "   • AI Gateway:   openai-forward-config-active.yaml"
    echo "   • Docker:       docker-compose-remote-ollama.yaml"
    echo
    echo "================================================================================"
}

# Main execution
main() {
    echo
    echo "================================================================================"
    echo "                   🤖 AI Gateway - Remote Ollama Setup"
    echo "================================================================================"
    echo
    
    # Run setup steps
    check_dependencies
    get_ollama_config
    create_env_file
    update_config_file
    test_remote_connection
    
    # Ask before starting services
    echo
    read -p "Start AI Gateway services now? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_services
        show_final_info
    else
        log "Setup completed. You can start services later with:"
        echo "docker-compose -f docker-compose-remote-ollama.yaml up -d"
    fi
}

# Run main function
main "$@" 