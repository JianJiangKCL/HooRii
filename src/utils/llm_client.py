#!/usr/bin/env python3
"""
LLM Client Abstraction Layer
Provides a unified interface for multiple LLM providers (Anthropic, Gemini)
"""
import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

import anthropic

try:
    from langfuse import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from .config import Config


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def generate_sync(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate a response from the LLM (synchronous)"""
        pass


class AnthropicLLMClient(LLMClient):
    """Anthropic Claude LLM client implementation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = anthropic.Anthropic(
            api_key=config.anthropic.api_key,
            max_retries=3,
            timeout=config.anthropic.timeout
        )
        self.default_model = config.anthropic.model
        self.default_max_tokens = config.anthropic.max_tokens
    
    async def generate(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate a response using Anthropic Claude"""
        try:
            response = self.client.messages.create(
                model=self.default_model,
                max_tokens=max_tokens or self.default_max_tokens,
                system=system_prompt,
                messages=messages,
                temperature=temperature,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise
    
    def generate_sync(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate a response using Anthropic Claude (synchronous)"""
        try:
            response = self.client.messages.create(
                model=self.default_model,
                max_tokens=max_tokens or self.default_max_tokens,
                system=system_prompt,
                messages=messages,
                temperature=temperature,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise


class GeminiLLMClient(LLMClient):
    """Google Gemini LLM client implementation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Import google-generativeai
        try:
            import google.generativeai as genai
            self.genai = genai
        except ImportError:
            raise ImportError(
                "google-generativeai package is required for Gemini support. "
                "Install it with: pip install google-generativeai"
            )
        
        # Configure Gemini
        self.genai.configure(api_key=config.gemini.api_key)
        self.default_model = config.gemini.model
        self.default_max_tokens = config.gemini.max_tokens
        
        # Configure safety settings to be less restrictive for smart home commands
        # Using the correct Gemini API types
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Create model instance with safety settings
        self.model = self.genai.GenerativeModel(
            self.default_model,
            safety_settings=self.safety_settings
        )
    
    def _build_prompt(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]]
    ) -> str:
        """Build a single prompt from system prompt and messages for Gemini"""
        # Simple and direct prompt format to avoid safety filters
        prompt_parts = []
        
        # Add system prompt as context
        if system_prompt:
            prompt_parts.append(system_prompt)
            prompt_parts.append("")  # Empty line separator
        
        # Add only the last user message
        if messages:
            last_message = messages[-1] if messages else None
            if last_message and last_message.get("content"):
                prompt_parts.append(last_message.get("content"))
        
        return "\n".join(prompt_parts)
    
    async def generate(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate a response using Google Gemini"""
        try:
            # Build single prompt from system prompt and messages
            full_prompt = self._build_prompt(system_prompt, messages)
            
            # Generate response with safety settings
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=self.genai.GenerationConfig(
                    max_output_tokens=max_tokens or self.default_max_tokens,
                    temperature=temperature,
                ),
                safety_settings=self.safety_settings
            )
            
            # Handle response with better error checking
            if hasattr(response, 'text') and response.text:
                return response.text
            elif hasattr(response, 'parts') and response.parts:
                return ''.join(part.text for part in response.parts if hasattr(part, 'text'))
            else:
                # Log finish reason for debugging
                finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN') if hasattr(response, 'candidates') and response.candidates else 'UNKNOWN'
                self.logger.warning(f"Gemini response blocked. Finish reason: {finish_reason}")
                
                # If blocked by safety, provide fallback message
                if finish_reason == 2 or str(finish_reason) == 'SAFETY':
                    self.logger.error("Response blocked by Gemini safety filters")
                    raise ValueError("Response blocked by safety filters. Try rephrasing the request.")
                
                raise ValueError(f"Gemini returned no text. Finish reason: {finish_reason}")
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            raise
    
    def generate_sync(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate a response using Google Gemini (synchronous)"""
        try:
            # Build single prompt from system prompt and messages
            full_prompt = self._build_prompt(system_prompt, messages)
            
            # Generate response with safety settings
            response = self.model.generate_content(
                full_prompt,
                generation_config=self.genai.GenerationConfig(
                    max_output_tokens=max_tokens or self.default_max_tokens,
                    temperature=temperature,
                ),
                safety_settings=self.safety_settings
            )
            
            # Handle response with better error checking
            if hasattr(response, 'text') and response.text:
                return response.text
            elif hasattr(response, 'parts') and response.parts:
                return ''.join(part.text for part in response.parts if hasattr(part, 'text'))
            else:
                # Log finish reason for debugging
                finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN') if hasattr(response, 'candidates') and response.candidates else 'UNKNOWN'
                self.logger.warning(f"Gemini response blocked. Finish reason: {finish_reason}")
                
                # If blocked by safety, provide fallback message
                if finish_reason == 2 or str(finish_reason) == 'SAFETY':
                    self.logger.error("Response blocked by Gemini safety filters")
                    raise ValueError("Response blocked by safety filters. Try rephrasing the request.")
                
                raise ValueError(f"Gemini returned no text. Finish reason: {finish_reason}")
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            raise


def create_llm_client(config: Config) -> LLMClient:
    """Factory function to create the appropriate LLM client"""
    provider = config.llm.provider.lower()
    
    if provider == "anthropic":
        return AnthropicLLMClient(config)
    elif provider == "gemini":
        return GeminiLLMClient(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

