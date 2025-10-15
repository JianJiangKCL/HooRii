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
        
        # Base model name; per-request model is built with system_instruction
        self.model_name = self.default_model
    
    def _build_contents(self, messages: List[Dict[str, str]]) -> list:
        """Build Gemini contents array from messages (use only last user message)."""
        if not messages:
            return []
        last = messages[-1]
        text = last.get("content") if isinstance(last, dict) else str(last)
        if not text:
            return []
        return [{"role": "user", "parts": [{"text": text}]}]
    
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
            # Build model with system instruction per request
            model = self.genai.GenerativeModel(
                self.model_name,
                system_instruction=system_prompt or "",
                safety_settings=self.safety_settings
            )

            contents = self._build_contents(messages)

            response = await model.generate_content_async(
                contents,
                generation_config=self.genai.GenerationConfig(
                    max_output_tokens=max_tokens or self.default_max_tokens,
                    temperature=temperature,
                    response_mime_type="application/json"
                )
            )
            
            # Handle response with better error checking
            # Extract text robustly from candidates/parts, avoid touching response.text early
            if getattr(response, 'candidates', None):
                # Check finish_reason first for MAX_TOKENS (2)
                finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN')
                if finish_reason == 2 or str(finish_reason).upper() in ('MAX_TOKENS', 'MAX_TOKENS_EXCEEDED'):
                    # Retry once with a higher token limit
                    retry_tokens = (max_tokens or self.default_max_tokens) + 512
                    retry_model = self.genai.GenerativeModel(
                        self.model_name,
                        system_instruction=(system_prompt or "") + "\n# Instruction: If the previous response was cut due to token limits, return a complete valid JSON object only.",
                        safety_settings=self.safety_settings
                    )
                    retry_resp = await retry_model.generate_content_async(
                        contents,
                        generation_config=self.genai.GenerationConfig(
                            max_output_tokens=retry_tokens,
                            temperature=temperature,
                            response_mime_type="application/json"
                        )
                    )
                    if getattr(retry_resp, 'candidates', None):
                        for cand in retry_resp.candidates:
                            content = getattr(cand, 'content', None)
                            if content and getattr(content, 'parts', None):
                                texts = [getattr(p, 'text', '') for p in content.parts if getattr(p, 'text', None)]
                                if texts:
                                    return ''.join(texts)
                    # Last chance, only then attempt property
                    try:
                        if getattr(retry_resp, 'text', None):
                            return retry_resp.text
                    except Exception:
                        pass
                for cand in response.candidates:
                    content = getattr(cand, 'content', None)
                    if content and getattr(content, 'parts', None):
                        texts = [getattr(p, 'text', '') for p in content.parts if getattr(p, 'text', None)]
                        if texts:
                            return ''.join(texts)
                self.logger.error(f"Gemini returned no text. Finish reason: {finish_reason}")
                raise ValueError(f"Gemini returned no text. Finish reason: {finish_reason}")
            # Fallback to parts, then text
            if getattr(response, 'parts', None):
                texts = [getattr(p, 'text', '') for p in response.parts if getattr(p, 'text', None)]
                if texts:
                    return ''.join(texts)
            try:
                if getattr(response, 'text', None):
                    return response.text
            except Exception:
                pass
            raise ValueError("Gemini returned empty response")
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
            model = self.genai.GenerativeModel(
                self.model_name,
                system_instruction=system_prompt or "",
                safety_settings=self.safety_settings
            )

            contents = self._build_contents(messages)

            response = model.generate_content(
                contents,
                generation_config=self.genai.GenerationConfig(
                    max_output_tokens=max_tokens or self.default_max_tokens,
                    temperature=temperature,
                    response_mime_type="application/json"
                )
            )
            
            # Handle response with better error checking
            if getattr(response, 'candidates', None):
                finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN')
                if finish_reason == 2 or str(finish_reason).upper() in ('MAX_TOKENS', 'MAX_TOKENS_EXCEEDED'):
                    retry_tokens = (max_tokens or self.default_max_tokens) + 512
                    retry_model = self.genai.GenerativeModel(
                        self.model_name,
                        system_instruction=(system_prompt or "") + "\n# Instruction: If the previous response was cut due to token limits, return a complete valid JSON object only.",
                        safety_settings=self.safety_settings
                    )
                    retry_resp = retry_model.generate_content(
                        contents,
                        generation_config=self.genai.GenerationConfig(
                            max_output_tokens=retry_tokens,
                            temperature=temperature,
                            response_mime_type="application/json"
                        )
                    )
                    if getattr(retry_resp, 'candidates', None):
                        for cand in retry_resp.candidates:
                            content = getattr(cand, 'content', None)
                            if content and getattr(content, 'parts', None):
                                texts = [getattr(p, 'text', '') for p in content.parts if getattr(p, 'text', None)]
                                if texts:
                                    return ''.join(texts)
                    try:
                        if getattr(retry_resp, 'text', None):
                            return retry_resp.text
                    except Exception:
                        pass
                for cand in response.candidates:
                    content = getattr(cand, 'content', None)
                    if content and getattr(content, 'parts', None):
                        texts = [getattr(p, 'text', '') for p in content.parts if getattr(p, 'text', None)]
                        if texts:
                            return ''.join(texts)
                self.logger.error(f"Gemini returned no text. Finish reason: {finish_reason}")
                raise ValueError(f"Gemini returned no text. Finish reason: {finish_reason}")
            if getattr(response, 'parts', None):
                texts = [getattr(p, 'text', '') for p in response.parts if getattr(p, 'text', None)]
                if texts:
                    return ''.join(texts)
            try:
                if getattr(response, 'text', None):
                    return response.text
            except Exception:
                pass
            raise ValueError("Gemini returned empty response")
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

