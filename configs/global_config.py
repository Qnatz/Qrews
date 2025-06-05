"""
config.py - Configuration for Gemini 2.0 Flash
Add this file to your project
"""

import time
from pathlib import Path
import os
import logging
import datetime
import requests  # Added missing import
import sqlite3
import numpy #  Import NumPy
from typing import Dict, Any, List
from pydantic import BaseModel

class GeminiConfig:
    """Configuration class for Gemini 2.0 Flash API"""
    
    # API Configuration
    API_KEY = os.getenv("GEMINI_API_KEY")
    BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models'
    MODEL_NAME = 'gemini-2.0-flash' # Updated model name
    
    TIMEOUT = 90  # Default timeout in seconds
    #print("FROM CONFIG =", API_KEY)
    # Generation Configuration
    DEFAULT_GENERATION_CONFIG = {
        'temperature': 0.4,
        'maxOutputTokens': 8048,
        'topP': 0.8,
        'topK': 10,
        'responseMimeType': 'text/plain'
    }
    
        # Agent-specific configurations
    AGENT_CONFIGS = {
        'project_analyzer': {
            'temperature': 0.2,  # Lower for more consistent analysis
            'maxOutputTokens': 1024
        },
        'planner': {
            'temperature': 0.3,
            'maxOutputTokens': 2048
        },
        'architect': { # Coding agent, uses CODING_MODEL_NAME by default logic in Agent class, but token limits here are still relevant
            'temperature': 0.2,
            'maxOutputTokens': 4096 # Increased
        },
        'code_writer': {
            'temperature': 0.1,  # Very low for code generation
            'maxOutputTokens': 4096 # Remains high, could be 8190
        },
        'frontend_builder': {
            'temperature': 0.2,
            'maxOutputTokens': 3072
        },
        'mobile_developer': { # Coding agent
            'temperature': 0.2,
            'maxOutputTokens': 4096 # Increased
        },
        'tester': {
            'temperature': 0.3,
            'maxOutputTokens': 2048
        },
        'debugger': {
            'temperature': 0.1,  # Very focused for debugging
            'maxOutputTokens': 2048
        }
    }
    
    # Safety settings for Gemini 2.0
    SAFETY_SETTINGS = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]
    
    @classmethod
    def get_generation_config(cls, agent_name: str = None) -> Dict[str, Any]:
        """Get generation configuration for specific agent or default"""
        config = cls.DEFAULT_GENERATION_CONFIG.copy()
        
        if agent_name and agent_name in cls.AGENT_CONFIGS:
            config.update(cls.AGENT_CONFIGS[agent_name])
        
        return config
    
    @classmethod
    def get_api_url(cls) -> str:
        """Get the full API URL for Gemini 2.0"""
        return f"{cls.BASE_URL}/{cls.MODEL_NAME}:generateContent"
    
    @classmethod
    def validate_api_key(cls) -> bool:
        """Validate that API key is present"""
        return bool(cls.API_KEY and cls.API_KEY != 'your-api-key-here')

# Model comparison and fallback configuration
class ModelConfig:
    """Configuration for model selection and fallbacks"""
    from typing import Dict, Any
    MODELS = {
        'gemini-2.0-flash': { # Renamed key and updated name
            'name': 'Gemini 2.0 Flash Latest',
            'max_tokens': 8192, # Max tokens for gemini 1.5 flash is 8192 output, 1M context
            'supports_tools': True,
            'cost_per_1k_tokens': 0.075,  # Example pricing, check actual
            'speed': 'fast'
        },
        'gemini-1.5-pro-latest': { # Ensuring this key exists if used by CODING_MODEL_NAME
            'name': 'Gemini 1.5 Pro Latest',
            'max_tokens': 8192, # Max tokens for gemini 1.5 pro is 8192 output, 1M context
            'supports_tools': True,
            'cost_per_1k_tokens': 0.125, # Example pricing, check actual
            'speed': 'medium'
        },
        # Keeping gemini-1.5-pro as an option if distinct from latest, or remove if it's the same
        # For this change, let's assume 'gemini-1.5-pro-latest' is the one we want for pro.
        # 'gemini-1.5-pro': {
        #     'name': 'Gemini 1.5 Pro',
        #     'max_tokens': 2048, # This was likely an old/incorrect value for 1.5 pro
        #     'supports_tools': True,
        #     'cost_per_1k_tokens': 0.125,
        #     'speed': 'medium'
        # },
        'deepseek-coder-1.3': {
            'name': 'DeepSeek Coder 1.3 (Local)',
            'max_tokens': 8192,
            'supports_tools': True, # May need testing
            'cost_per_1k_tokens': 0.0,
            'speed': 'medium',
            'local': True # Flag as local
        },
       'deepseek-r1': {
            'name': 'DeepSeek R1 (Local)',
            'max_tokens': 8192,
            'supports_tools': False, # May need testing
            'cost_per_1k_tokens': 0.0,
            'speed': 'slow',
            'local': True # Flag as local
        }
    }

    TIMEOUTS = {
        'gemini-2.0-flash': 60, # Updated key
        'gemini-1.5-pro-latest': 120, # Added for new pro model
        # 'gemini-1.5-pro': 120, # Old pro key
        'deepseek-coder-1.3': 120,
        'deepseek-r1': 240,
    }
    
    # Fallback order if primary model fails
    FALLBACK_ORDER = ['gemini-2.0-flash', 'gemini-1.5-flash-latest', 'deepseek-coder-1.3', 'deepseek-r1'] # Updated order
    
    @classmethod
    def get_model_info(cls, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        return cls.MODELS.get(model_name, {})
    
    @classmethod
    def get_fallback_model(cls, current_model: str) -> str:
        """Get next fallback model"""
        try:
            current_index = cls.FALLBACK_ORDER.index(current_model)
            if current_index < len(cls.FALLBACK_ORDER) - 1:
                return cls.FALLBACK_ORDER[current_index + 1]
        except (ValueError, IndexError):
            pass
        return cls.FALLBACK_ORDER[0]

    @classmethod
    def get_timeout(cls, model_name: str) -> int:
        """Get timeout for specific model"""
        return cls.TIMEOUTS.get(model_name, GeminiConfig.TIMEOUT)

# Usage example
if __name__ == "__main__":
    # Test configuration
    print("Gemini 2.0 Configuration Test")
    print(f"API URL: {GeminiConfig.get_api_url()}")
    print(f"API Key Valid: {GeminiConfig.validate_api_key()}")
    print(f"Default Config: {GeminiConfig.get_generation_config()}")
    print(f"Code Writer Config: {GeminiConfig.get_generation_config('code_writer')}")
    
    # Test model info
    print(f"Gemini 1.5 Flash Latest Info: {ModelConfig.get_model_info('gemini-1.5-flash-latest')}")
    print(f"Fallback Model from Flash: {ModelConfig.get_fallback_model('gemini-1.5-flash-latest')}")
    print(f"Gemini 1.5 Flash Latest Timeout: {ModelConfig.get_timeout('gemini-1.5-flash-latest')}")
    print(f"Gemini 1.5 Pro Latest Info: {ModelConfig.get_model_info('gemini-1.5-pro-latest')}")
    print(f"Gemini 1.5 Pro Latest Timeout: {ModelConfig.get_timeout('gemini-1.5-pro-latest')}")
    print(f"Unknown Model Timeout: {ModelConfig.get_timeout('unknown-model')}")


class ModelStrategyConfig(BaseModel):
    DEFAULT_GEMINI_MODEL: str = "gemini-1.5-flash" # Updated
    CODING_MODEL_NAME: str = "gemini-2.0-flash" # Updated to use Gemini Pro for coding
    LOCAL_FALLBACK_MODEL_NAME: str = "deepseek-base" # User can adjust this value
    LOCAL_MODEL_ENDPOINTS: Dict[str, str] = {
        "deepseek-coder": "http://localhost:8081/v1", # Updated port for coder
        "deepseek-base": "http://localhost:8080/v1"   # Updated port for general/fallback
    }
    CODING_AGENT_NAMES: List[str] = [
        "code_writer",
        "debugger",
        "frontend_builder",
        "mobile_developer"
        # Add other agents that primarily do coding if any
    ]
    ENABLE_LOCAL_FALLBACK: bool = True

MODEL_STRATEGY_CONFIG = ModelStrategyConfig()

# Agent Specialization Matrix
# Maps technology categories to a list of agent names that can propose technologies for that category.
AGENT_SPECIALIZATIONS = {
    "database": ["ProjectAnalyzer", "MobileDeveloper", "Architect"], # ProjectAnalyzer (general), MobileDeveloper (mobile-specific DBs), Architect (system-wide DB)
    "web_backend": ["Architect", "CodeWriter"], # Architect (high-level), CodeWriter (implementation details)
    "mobile_native_features": ["MobileDeveloper"],
    "media_storage": ["Architect"],
    "pdf_generation": ["Architect", "CodeWriter"],
    "background_work": ["Architect", "CodeWriter"],
    "frontend_framework": ["FrontendBuilder", "ProjectAnalyzer"], # ProjectAnalyzer for initial, FrontendBuilder for detailed
    # Add more categories and specialized agents as the system evolves.
    # For example:
    # "authentication": ["Architect", "CodeWriter"],
    # "real_time_communication": ["Architect"],
    # "analytics_tracking": ["ProjectAnalyzer", "FrontendBuilder"],
    # "payment_gateway": ["Architect", "CodeWriter"],
    # "dev_ops_deployment": ["Architect"], # Or a dedicated DevOps agent
}