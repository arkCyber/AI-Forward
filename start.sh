#!/bin/bash

# ==============================================================================
# OpenAI Forward Service Startup Script
# ==============================================================================
# Description: Automated startup script for OpenAI Forward with multi-AI support
# Author: Assistant
# Created: 2024-12-19
# Version: 1.0
#
# This script provides:
# - Automated Docker service management
# - Health checks and validation
# - Error handling and logging
# - Service status monitoring
# - Easy troubleshooting commands
# ==============================================================================

set -e  # Exit on any error

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function with timestamp
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log "Docker is running successfully"
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose >/dev/null 2>&1; then
        error "Docker Compose is not installed. Please install it and try again."
        exit 1
    fi
    log "Docker Compose is available"
}

# Function to validate configuration file
check_config() {
    if [ ! -f "openai-forward-config.yaml" ]; then
        error "Configuration file 'openai-forward-config.yaml' not found!"
        error "Please ensure the configuration file exists in the current directory."
        exit 1
    fi
    log "Configuration file found and validated"
}

# Function to create required directories
create_directories() {
    local dirs=("logs" "FLAXKV_DB")
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done
}

# Function to check if service is healthy
check_health() {
    local max_attempts=15
    local attempt=1
    
    info "Checking service health..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/ >/dev/null 2>&1; then
            log "Service is healthy and responding!"
            return 0
        fi
        
        if [ $attempt -eq 1 ]; then
            info "Waiting for service to start..."
        fi
        
        sleep 2
        ((attempt++))
    done
    
    warn "Service health check failed after $max_attempts attempts"
    warn "Service may still be starting up. Check logs with: docker-compose logs -f"
    return 1
}

# Function to display service information
show_service_info() {
    echo
    log "=== OpenAI Forward Service Information ==="
    echo
    info "Service Endpoints:"
    echo "  • Main service:     http://localhost:8000"
    echo "  • DeepSeek API:     http://localhost:8000/deepseek/v1/chat/completions"
    echo "  • LingyiWanwu API:  http://localhost:8000/lingyiwanwu/v1/chat/completions"
    echo "  • OpenAI API:       http://localhost:8000/v1/chat/completions"
    echo "  • Health check:     http://localhost:8000/health"
    echo
    info "Management Commands:"
    echo "  • View logs:        docker-compose logs -f"
    echo "  • Check status:     docker-compose ps"
    echo "  • Stop service:     docker-compose down"
    echo "  • Restart:          docker-compose restart"
    echo
    info "API Usage Examples:"
    echo "  • Test DeepSeek:"
    echo "    curl -X POST http://localhost:8000/deepseek/v1/chat/completions \\"
    echo "         -H 'Authorization: Bearer sk-878a5319c7b14bc48109e19315361b7f' \\"
    echo "         -H 'Content-Type: application/json' \\"
    echo "         -d '{\"model\":\"deepseek-chat\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
    echo
    echo "  • Test LingyiWanwu:"
    echo "    curl -X POST http://localhost:8000/lingyiwanwu/v1/chat/completions \\"
    echo "         -H 'Authorization: Bearer 72ebf8a6191e45bab0f646659c8cb121' \\"
    echo "         -H 'Content-Type: application/json' \\"
    echo "         -d '{\"model\":\"yi-34b-chat\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
    echo
}

# Function to stop service
stop_service() {
    log "Stopping OpenAI Forward service..."
    if docker-compose down; then
        log "Service stopped successfully"
    else
        error "Failed to stop service"
        exit 1
    fi
}

# Function to start service
start_service() {
    log "Starting OpenAI Forward service with multi-AI provider support..."
    
    # Check prerequisites
    check_docker
    check_docker_compose
    check_config
    create_directories
    
    # Build and start the service
    info "Building and starting containers..."
    if docker-compose up -d --build; then
        log "Containers started successfully"
    else
        error "Failed to start containers"
        exit 1
    fi
    
    # Wait for service to be ready
    sleep 5
    
    # Check health
    if check_health; then
        log "Service is ready!"
        show_service_info
    else
        warn "Service started but health check failed"
        info "Check logs for more details: docker-compose logs -f"
    fi
}

# Function to show status
show_status() {
    info "Current service status:"
    docker-compose ps
    echo
    
    if curl -f http://localhost:8000/ >/dev/null 2>&1; then
        log "Service is healthy and responding"
    else
        warn "Service is not responding to health checks"
    fi
}

# Function to show logs
show_logs() {
    info "Showing service logs (press Ctrl+C to exit):"
    docker-compose logs -f
}

# Main script logic
case "${1:-start}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        sleep 2
        start_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    info)
        show_service_info
        ;;
    help|--help|-h)
        echo "OpenAI Forward Service Management Script"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  start     Start the service (default)"
        echo "  stop      Stop the service"
        echo "  restart   Restart the service"
        echo "  status    Show service status"
        echo "  logs      Show service logs"
        echo "  info      Show service information"
        echo "  help      Show this help message"
        echo
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

# ==============================================================================
# Script completed successfully
# ============================================================================== 