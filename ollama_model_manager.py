#!/usr/bin/env python3

"""
==============================================================================
Ollama Model Manager
==============================================================================
Description: Smart model detection and management for Ollama service
Author: Assistant
Created: 2024-12-19
Version: 1.0

This script provides:
- Model existence detection
- Intelligent model downloading
- Model validation and health checks
- Model size and status reporting
==============================================================================
"""

import os
import json
import subprocess
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Configure logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ollama_manager")

@dataclass
class ModelInfo:
    """Ollama model information"""
    name: str
    size: Optional[str] = None
    modified: Optional[str] = None
    digest: Optional[str] = None
    format: Optional[str] = None
    family: Optional[str] = None
    families: Optional[List[str]] = None
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None
    is_available: bool = False
    download_required: bool = True

class OllamaModelManager:
    """Smart Ollama model management"""
    
    def __init__(self, container_name: str = "ollama-server", 
                 models_path: str = "./ollama-models"):
        """Initialize model manager"""
        self.container_name = container_name
        self.models_path = Path(models_path)
        self.required_models = [
            "llama3.2:1b",      # 轻量级对话模型
            "llama3.2:3b",      # 中等大小模型
            "qwen2:1.5b",       # 中文优化轻量级
            "qwen2:7b",         # 中文优化标准版
            "codegemma:2b",     # 代码生成轻量级
            "codegemma:7b"      # 代码生成标准版
        ]
        
        # 模型优先级配置
        self.model_priority = {
            "llama3.2:1b": 1,    # 高优先级，小体积
            "qwen2:1.5b": 1,     # 高优先级，小体积
            "codegemma:2b": 2,   # 中优先级
            "llama3.2:3b": 3,    # 较低优先级
            "qwen2:7b": 3,       # 较低优先级
            "codegemma:7b": 4    # 最低优先级，大体积
        }
        
        logger.info(f"🦙 Initialized Ollama Model Manager")
        logger.info(f"📁 Models path: {self.models_path}")
        logger.info(f"🐳 Container: {self.container_name}")
    
    def check_container_running(self) -> bool:
        """Check if Ollama container is running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            is_running = self.container_name in result.stdout
            logger.info(f"🐳 Container {self.container_name} status: {'Running' if is_running else 'Not running'}")
            return is_running
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to check container status: {e}")
            return False
    
    def get_local_model_manifests(self) -> List[str]:
        """Get list of locally downloaded models from manifest files"""
        manifest_path = self.models_path / "models" / "manifests" / "registry.ollama.ai" / "library"
        local_models = []
        
        if not manifest_path.exists():
            logger.warning(f"⚠️ Manifest path not found: {manifest_path}")
            return local_models
        
        try:
            for model_dir in manifest_path.iterdir():
                if model_dir.is_dir():
                    # Check for version subdirectories
                    for version_dir in model_dir.iterdir():
                        if version_dir.is_dir():
                            model_name = f"{model_dir.name}:{version_dir.name}"
                            local_models.append(model_name)
                            logger.debug(f"📦 Found local model manifest: {model_name}")
            
            logger.info(f"📦 Found {len(local_models)} local model manifests")
            return local_models
            
        except Exception as e:
            logger.error(f"❌ Error reading local manifests: {e}")
            return []
    
    def get_ollama_models_list(self) -> List[ModelInfo]:
        """Get list of models from Ollama service"""
        if not self.check_container_running():
            logger.warning("⚠️ Ollama container not running, using local manifest check")
            local_models = self.get_local_model_manifests()
            return [
                ModelInfo(name=model, is_available=True, download_required=False)
                for model in local_models
            ]
        
        try:
            # Get model list from Ollama API
            result = subprocess.run(
                ["docker", "exec", self.container_name, "ollama", "list"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            
            models = []
            lines = result.stdout.strip().split('\n')
            
            # Skip header line if present
            if lines and 'NAME' in lines[0]:
                lines = lines[1:]
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        model_info = ModelInfo(
                            name=parts[0],
                            size=parts[1] if len(parts) > 1 else None,
                            modified=parts[2] if len(parts) > 2 else None,
                            is_available=True,
                            download_required=False
                        )
                        models.append(model_info)
                        logger.debug(f"✅ Found model: {model_info.name} ({model_info.size})")
            
            logger.info(f"📋 Retrieved {len(models)} models from Ollama service")
            return models
            
        except subprocess.TimeoutExpired:
            logger.error("⏰ Timeout getting model list from Ollama")
            return []
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to get model list: {e}")
            return []
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available locally"""
        available_models = self.get_ollama_models_list()
        
        # Check exact match first
        for model in available_models:
            if model.name == model_name:
                logger.debug(f"✅ Model {model_name} found (exact match)")
                return True
        
        # Check without tag (default to 'latest')
        model_base = model_name.split(':')[0]
        for model in available_models:
            model_base_available = model.name.split(':')[0]
            if model_base_available == model_base:
                logger.debug(f"✅ Model {model_name} found as {model.name}")
                return True
        
        logger.debug(f"❌ Model {model_name} not found locally")
        return False
    
    def download_model(self, model_name: str, force: bool = False) -> bool:
        """Download a specific model"""
        if not force and self.is_model_available(model_name):
            logger.info(f"✅ Model {model_name} already available, skipping download")
            return True
        
        if not self.check_container_running():
            logger.error(f"❌ Cannot download {model_name}: Ollama container not running")
            return False
        
        logger.info(f"📥 Downloading model: {model_name}...")
        start_time = time.time()
        
        try:
            # Use interactive mode for progress display
            result = subprocess.run(
                ["docker", "exec", "-it", self.container_name, "ollama", "pull", model_name],
                timeout=1800,  # 30 minutes timeout for large models
                check=True
            )
            
            download_time = time.time() - start_time
            logger.info(f"✅ Successfully downloaded {model_name} in {download_time:.1f}s")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Timeout downloading {model_name} (30 min limit)")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to download {model_name}: {e}")
            return False
    
    def validate_model(self, model_name: str) -> bool:
        """Validate a model by running a simple test"""
        if not self.check_container_running():
            logger.warning(f"⚠️ Cannot validate {model_name}: container not running")
            return False
        
        logger.info(f"🔍 Validating model: {model_name}...")
        
        try:
            # Run a simple completion test
            result = subprocess.run(
                ["docker", "exec", self.container_name, "ollama", "run", model_name, "Hello"],
                capture_output=True,
                text=True,
                timeout=60,
                check=True
            )
            
            if result.stdout.strip():
                logger.info(f"✅ Model {model_name} validation successful")
                return True
            else:
                logger.warning(f"⚠️ Model {model_name} returned empty response")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Model {model_name} validation timeout")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Model {model_name} validation failed: {e}")
            return False
    
    def smart_model_setup(self, priority_only: bool = True, 
                         validate_models: bool = True) -> Dict[str, bool]:
        """Smart model setup based on priorities and available space"""
        logger.info("🧠 Starting smart model setup...")
        
        results = {}
        
        # Sort models by priority
        models_to_process = sorted(
            self.required_models,
            key=lambda m: self.model_priority.get(m, 999)
        )
        
        if priority_only:
            # Only process high priority models (priority 1-2)
            models_to_process = [
                m for m in models_to_process 
                if self.model_priority.get(m, 999) <= 2
            ]
            logger.info(f"📋 Processing {len(models_to_process)} high-priority models")
        
        for model in models_to_process:
            logger.info(f"🔄 Processing model: {model}")
            
            # Check if model exists
            if self.is_model_available(model):
                logger.info(f"✅ Model {model} already available")
                
                # Validate if requested
                if validate_models:
                    is_valid = self.validate_model(model)
                    results[model] = is_valid
                    if not is_valid:
                        logger.warning(f"⚠️ Model {model} failed validation")
                else:
                    results[model] = True
            else:
                # Download model
                success = self.download_model(model)
                if success and validate_models:
                    success = self.validate_model(model)
                
                results[model] = success
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        logger.info(f"📊 Model setup complete: {successful}/{len(results)} models ready")
        
        return results
    
    def get_model_status_report(self) -> Dict:
        """Generate comprehensive model status report"""
        logger.info("📊 Generating model status report...")
        
        available_models = self.get_ollama_models_list()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "container_running": self.check_container_running(),
            "models_path": str(self.models_path),
            "total_models_available": len(available_models),
            "required_models": {},
            "available_models": [],
            "missing_models": [],
            "recommendations": []
        }
        
        # Check each required model
        for model in self.required_models:
            is_available = self.is_model_available(model)
            priority = self.model_priority.get(model, 999)
            
            report["required_models"][model] = {
                "available": is_available,
                "priority": priority,
                "recommended": priority <= 2
            }
            
            if is_available:
                # Find model info
                model_info = None
                for avail_model in available_models:
                    if avail_model.name == model or avail_model.name.split(':')[0] == model.split(':')[0]:
                        model_info = avail_model
                        break
                
                report["available_models"].append({
                    "name": model,
                    "size": model_info.size if model_info else "unknown",
                    "modified": model_info.modified if model_info else "unknown",
                    "priority": priority
                })
            else:
                report["missing_models"].append({
                    "name": model,
                    "priority": priority,
                    "recommended": priority <= 2
                })
        
        # Generate recommendations
        high_priority_missing = [
            m for m in report["missing_models"] 
            if m["priority"] <= 2
        ]
        
        if high_priority_missing:
            report["recommendations"].append(
                f"Download {len(high_priority_missing)} high-priority models: " +
                ", ".join([m["name"] for m in high_priority_missing])
            )
        
        if not report["container_running"]:
            report["recommendations"].append("Start Ollama container before downloading models")
        
        return report
    
    def cleanup_old_models(self, keep_latest: int = 2) -> List[str]:
        """Clean up old model versions, keeping only the latest versions"""
        if not self.check_container_running():
            logger.error("❌ Cannot cleanup: Ollama container not running")
            return []
        
        logger.info(f"🧹 Starting model cleanup (keeping {keep_latest} latest versions)...")
        
        removed_models = []
        
        try:
            # Get all models grouped by name
            available_models = self.get_ollama_models_list()
            models_by_name = {}
            
            for model in available_models:
                base_name = model.name.split(':')[0]
                if base_name not in models_by_name:
                    models_by_name[base_name] = []
                models_by_name[base_name].append(model)
            
            # For each model family, remove old versions
            for base_name, model_versions in models_by_name.items():
                if len(model_versions) > keep_latest:
                    # Sort by modified date (newest first)
                    sorted_versions = sorted(
                        model_versions,
                        key=lambda m: m.modified or "0000-00-00",
                        reverse=True
                    )
                    
                    # Remove old versions
                    for old_model in sorted_versions[keep_latest:]:
                        try:
                            subprocess.run(
                                ["docker", "exec", self.container_name, "ollama", "rm", old_model.name],
                                check=True,
                                capture_output=True
                            )
                            removed_models.append(old_model.name)
                            logger.info(f"🗑️ Removed old model: {old_model.name}")
                        except subprocess.CalledProcessError as e:
                            logger.error(f"❌ Failed to remove {old_model.name}: {e}")
            
            logger.info(f"🧹 Cleanup complete: removed {len(removed_models)} old models")
            return removed_models
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return []

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ollama Model Manager")
    parser.add_argument("--container", default="ollama-server", help="Ollama container name")
    parser.add_argument("--models-path", default="./ollama-models", help="Models storage path")
    parser.add_argument("--setup", action="store_true", help="Run smart model setup")
    parser.add_argument("--priority-only", action="store_true", help="Only setup priority models")
    parser.add_argument("--validate", action="store_true", help="Validate models after setup")
    parser.add_argument("--status", action="store_true", help="Show model status report")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup old models")
    parser.add_argument("--check", help="Check if specific model is available")
    parser.add_argument("--download", help="Download specific model")
    
    args = parser.parse_args()
    
    manager = OllamaModelManager(args.container, args.models_path)
    
    if args.setup:
        logger.info("🚀 Running smart model setup...")
        results = manager.smart_model_setup(
            priority_only=args.priority_only,
            validate_models=args.validate
        )
        
        print("\n📊 Setup Results:")
        for model, success in results.items():
            status = "✅ Ready" if success else "❌ Failed"
            print(f"  {model}: {status}")
    
    elif args.status:
        report = manager.get_model_status_report()
        
        print("\n📊 Ollama Model Status Report")
        print("=" * 50)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Container Running: {report['container_running']}")
        print(f"Total Models Available: {report['total_models_available']}")
        print(f"Models Path: {report['models_path']}")
        
        print(f"\n✅ Available Models ({len(report['available_models'])}):")
        for model in report['available_models']:
            print(f"  - {model['name']} ({model['size']}) [Priority: {model['priority']}]")
        
        if report['missing_models']:
            print(f"\n❌ Missing Models ({len(report['missing_models'])}):")
            for model in report['missing_models']:
                priority_str = f"[Priority: {model['priority']}]"
                recommended_str = " (Recommended)" if model['recommended'] else ""
                print(f"  - {model['name']} {priority_str}{recommended_str}")
        
        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"  - {rec}")
    
    elif args.cleanup:
        removed = manager.cleanup_old_models()
        print(f"\n🧹 Cleaned up {len(removed)} old models")
        for model in removed:
            print(f"  - Removed: {model}")
    
    elif args.check:
        available = manager.is_model_available(args.check)
        status = "✅ Available" if available else "❌ Not found"
        print(f"Model {args.check}: {status}")
    
    elif args.download:
        success = manager.download_model(args.download)
        status = "✅ Success" if success else "❌ Failed"
        print(f"Download {args.download}: {status}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 