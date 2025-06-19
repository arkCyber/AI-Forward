#!/bin/bash

# ==============================================================================
# Smart AI Router Management Script
# ==============================================================================
# Description: Complete management script for Smart AI Router service stack
# Author: Assistant
# Created: 2024-12-19
# Version: 1.0
#
# Features:
# - Service start/stop/restart
# - Health monitoring
# - Automated testing
# - Log viewing
# - Performance monitoring
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yaml"
LOG_DIR="$SCRIPT_DIR/ai-router-logs"

# Services
AI_ROUTER_URL="http://localhost:9000"
OPENAI_FORWARD_URL="http://localhost:8000"
OLLAMA_URL="http://localhost:11434"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

show_banner() {
    echo -e "${CYAN}"
    echo "=========================================="
    echo "     🤖 Smart AI Router Manager"
    echo "=========================================="
    echo -e "${NC}"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check Python (for testing)
    if ! command -v python3 &> /dev/null; then
        log_warning "Python3 not found - testing features will be limited"
    fi
    
    log_success "All dependencies are available"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    directories=(
        "$LOG_DIR"
        "$SCRIPT_DIR/logs"
        "$SCRIPT_DIR/ollama-models"
        "$SCRIPT_DIR/ollama-logs"
        "$SCRIPT_DIR/FLAXKV_DB"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done
    
    log_success "Directories are ready"
}

start_services() {
    log_info "Starting Smart AI Router service stack..."
    
    create_directories
    
    # Start services
    cd "$SCRIPT_DIR"
    docker-compose up -d
    
    log_info "Waiting for services to start..."
    sleep 10
    
    # Check service status
    check_service_health
}

stop_services() {
    log_info "Stopping Smart AI Router service stack..."
    
    cd "$SCRIPT_DIR"
    docker-compose down
    
    log_success "Services stopped"
}

restart_services() {
    log_info "Restarting Smart AI Router service stack..."
    stop_services
    sleep 3
    start_services
}

check_service_health() {
    log_info "Checking service health..."
    
    # Check AI Router
    if curl -s "$AI_ROUTER_URL/health" > /dev/null; then
        log_success "✅ AI Router is healthy (port 9000)"
    else
        log_error "❌ AI Router is not responding (port 9000)"
    fi
    
    # Check OpenAI Forward
    if curl -s "$OPENAI_FORWARD_URL" > /dev/null; then
        log_success "✅ OpenAI Forward is healthy (port 8000)"
    else
        log_error "❌ OpenAI Forward is not responding (port 8000)"
    fi
    
    # Check Ollama
    if curl -s "$OLLAMA_URL/api/tags" > /dev/null; then
        log_success "✅ Ollama is healthy (port 11434)"
    else
        log_warning "⚠️ Ollama is not responding (port 11434)"
    fi
}

show_status() {
    log_info "Service Status:"
    echo
    
    # Docker containers status
    docker-compose ps
    echo
    
    # Health checks
    check_service_health
    echo
    
    # AI Router stats
    if curl -s "$AI_ROUTER_URL/stats" > /dev/null; then
        log_info "AI Router Statistics:"
        curl -s "$AI_ROUTER_URL/stats" | python3 -m json.tool 2>/dev/null || curl -s "$AI_ROUTER_URL/stats"
    fi
}

run_tests() {
    log_info "Running comprehensive tests..."
    
    # Check if test script exists
    if [ ! -f "$SCRIPT_DIR/test_ai_router.py" ]; then
        log_error "Test script not found: $SCRIPT_DIR/test_ai_router.py"
        return 1
    fi
    
    # Install httpx if not available
    if ! python3 -c "import httpx" 2>/dev/null; then
        log_info "Installing httpx for testing..."
        pip3 install httpx || {
            log_error "Failed to install httpx. Please install it manually: pip3 install httpx"
            return 1
        }
    fi
    
    # Run tests
    cd "$SCRIPT_DIR"
    python3 test_ai_router.py --output test_results.json
    
    if [ $? -eq 0 ]; then
        log_success "Tests completed successfully"
    else
        log_error "Some tests failed"
    fi
}

quick_test() {
    log_info "Running quick API test..."
    
    # Simple chat completion test
    response=$(curl -s -X POST "$AI_ROUTER_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello! Say hi back."}],
            "max_tokens": 20
        }')
    
    if [ $? -eq 0 ] && echo "$response" | grep -q "choices"; then
        log_success "✅ Quick test passed"
        echo "Response: $(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['choices'][0]['message']['content'])" 2>/dev/null || echo "Unable to parse response")"
    else
        log_error "❌ Quick test failed"
        echo "Response: $response"
    fi
}

view_logs() {
    local service=${1:-ai-router}
    log_info "Viewing logs for service: $service"
    
    case $service in
        "ai-router")
            docker-compose logs -f ai-router
            ;;
        "openai-forward")
            docker-compose logs -f openai-forward
            ;;
        "ollama")
            docker-compose logs -f ollama
            ;;
        "all")
            docker-compose logs -f
            ;;
        *)
            log_error "Unknown service. Available: ai-router, openai-forward, ollama, all"
            ;;
    esac
}

install_ollama_models() {
    log_info "🧠 Starting smart Ollama model management..."
    
    # Check if ollama_model_manager.py exists
    if [ ! -f "$SCRIPT_DIR/ollama_model_manager.py" ]; then
        log_error "Model manager script not found: $SCRIPT_DIR/ollama_model_manager.py"
        return 1
    fi
    
    # Make script executable
    chmod +x "$SCRIPT_DIR/ollama_model_manager.py"
    
    # Check current model status first
    log_info "📊 Checking current model status..."
    python3 "$SCRIPT_DIR/ollama_model_manager.py" --status
    
    echo
    read -p "Do you want to run smart model setup? [y/N]: " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "🚀 Running smart model setup (priority models only)..."
        python3 "$SCRIPT_DIR/ollama_model_manager.py" --setup --priority-only --validate
        
        if [ $? -eq 0 ]; then
            log_success "✅ Smart model setup completed"
        else
            log_error "❌ Model setup encountered issues"
        fi
    else
        log_info "⏭️ Skipping model setup"
    fi
    
    echo
    log_info "📋 Final model status:"
    python3 "$SCRIPT_DIR/ollama_model_manager.py" --status
}

smart_model_setup() {
    log_info "🧠 Running smart model setup..."
    
    if [ ! -f "$SCRIPT_DIR/ollama_model_manager.py" ]; then
        log_error "Model manager script not found: $SCRIPT_DIR/ollama_model_manager.py"
        return 1
    fi
    
    # Run with priority models only by default
    local priority_only=${1:-true}
    local validate=${2:-true}
    
    if [ "$priority_only" = "true" ]; then
        log_info "🎯 Setting up high-priority models only..."
        python3 "$SCRIPT_DIR/ollama_model_manager.py" --setup --priority-only --validate
    else
        log_info "📦 Setting up all required models..."
        python3 "$SCRIPT_DIR/ollama_model_manager.py" --setup --validate
    fi
}

check_model_status() {
    log_info "📊 Checking Ollama model status..."
    
    if [ ! -f "$SCRIPT_DIR/ollama_model_manager.py" ]; then
        log_warning "Model manager script not found, using basic check..."
        
        # Basic fallback check
        if docker exec ollama-server ollama list >/dev/null 2>&1; then
            log_info "Available models:"
            docker exec ollama-server ollama list
        else
            log_warning "Cannot access Ollama service"
        fi
        return
    fi
    
    python3 "$SCRIPT_DIR/ollama_model_manager.py" --status
}

check_specific_model() {
    local model_name=${1}
    
    if [ -z "$model_name" ]; then
        log_error "Model name required. Usage: check_specific_model <model_name>"
        return 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/ollama_model_manager.py" ]; then
        log_error "Model manager script not found"
        return 1
    fi
    
    python3 "$SCRIPT_DIR/ollama_model_manager.py" --check "$model_name"
}

download_specific_model() {
    local model_name=${1}
    
    if [ -z "$model_name" ]; then
        log_error "Model name required. Usage: download_specific_model <model_name>"
        return 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/ollama_model_manager.py" ]; then
        log_error "Model manager script not found"
        return 1
    fi
    
    python3 "$SCRIPT_DIR/ollama_model_manager.py" --download "$model_name"
}

cleanup_old_models() {
    log_info "🧹 Cleaning up old Ollama models..."
    
    if [ ! -f "$SCRIPT_DIR/ollama_model_manager.py" ]; then
        log_error "Model manager script not found"
        return 1
    fi
    
    echo
    read -p "This will remove old model versions. Continue? [y/N]: " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 "$SCRIPT_DIR/ollama_model_manager.py" --cleanup
    else
        log_info "Cleanup cancelled"
    fi
}

show_endpoints() {
    echo -e "${PURPLE}"
    echo "=========================================="
    echo "           📡 Service Endpoints"
    echo "=========================================="
    echo -e "${NC}"
    echo "🎯 Unified AI API:     $AI_ROUTER_URL/v1/chat/completions"
    echo "🔍 Health Check:       $AI_ROUTER_URL/health"
    echo "📊 Statistics:         $AI_ROUTER_URL/stats"
    echo "🌐 OpenAI Forward:     $OPENAI_FORWARD_URL"
    echo "🦙 Ollama Direct:      $OLLAMA_URL"
    echo ""
    echo "Example usage:"
    echo "curl -X POST $AI_ROUTER_URL/v1/chat/completions \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"model\":\"gpt-3.5-turbo\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}'"
}

show_help() {
    echo -e "${CYAN}Smart AI Router Management Script${NC}"
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  start              Start all services"
    echo "  stop               Stop all services"
    echo "  restart            Restart all services"
    echo "  status             Show service status"
    echo "  health             Check service health"
    echo "  test               Run comprehensive tests"
    echo "  quick-test         Run quick API test"
    echo "  logs [SERVICE]     View logs (ai-router|openai-forward|ollama|all)"
    echo "  install-models     Smart Ollama model management (interactive)"
    echo "  model-status       Check Ollama model status"
    echo "  model-setup        Run smart model setup (priority models)"
    echo "  model-setup-all    Setup all required models"
    echo "  check-model MODEL  Check if specific model is available"
    echo "  download-model MODEL Download specific model"
    echo "  cleanup-models     Cleanup old model versions"
    echo "  endpoints          Show service endpoints"
    echo "  help               Show this help"
    echo
    echo "Examples:"
    echo "  $0 start                    # Start all services"
    echo "  $0 model-status             # Check model availability"
    echo "  $0 model-setup              # Setup priority models"
    echo "  $0 check-model llama3.2:1b  # Check specific model"
    echo "  $0 download-model qwen2:7b  # Download specific model"
    echo "  $0 test                     # Run tests"
    echo "  $0 logs ai-router           # View AI router logs"
    echo "  $0 quick-test               # Quick functionality test"
}

main() {
    show_banner
    check_dependencies
    
    case "${1:-help}" in
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "status")
            show_status
            ;;
        "health")
            check_service_health
            ;;
        "test")
            run_tests
            ;;
        "quick-test")
            quick_test
            ;;
        "logs")
            view_logs "${2:-ai-router}"
            ;;
        "install-models")
            install_ollama_models
            ;;
        "model-status")
            check_model_status
            ;;
        "model-setup")
            smart_model_setup
            ;;
        "model-setup-all")
            smart_model_setup false false
            ;;
        "check-model")
            check_specific_model "${2:-}"
            ;;
        "download-model")
            download_specific_model "${2:-}"
            ;;
        "cleanup-models")
            cleanup_old_models
            ;;
        "endpoints")
            show_endpoints
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 