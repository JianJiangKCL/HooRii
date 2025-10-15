#!/usr/bin/env python3
"""
Text formatting utilities for TTS with ElevenLabs Audio Tags
Converts text markers to ElevenLabs Voice Tags format
"""
import re
from typing import Dict, Callable


def format_for_elevenlabs(text: str) -> str:
    """
    Format text for ElevenLabs - keep it natural
    
    For eleven_turbo_v2_5 model:
    - NO voice tags support ([whispers], [sighs], etc.)
    - Only natural pauses with ... work
    - Keep text clean and simple
    
    Conversions:
    - ... (ellipsis) -> Keep as-is (natural pause)
    - Remove any tag markers - model doesn't support them
    
    Args:
        text: Original character response text
        
    Returns:
        Clean text with only natural pauses
    """
    if not text:
        return text
    
    result = text
    
    # Keep ellipsis as-is for natural pauses
    # No conversion needed for ...
    
    # Remove all tag markers (not supported by eleven_turbo_v2_5)
    # Remove [tag] style markers
    result = re.sub(r'\[whispers\]', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\[sighs\]', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\[exhales\]', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\[curious\]', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\[laughs\]', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\[.*?\]', '', result)  # Remove any other [tags]
    
    # Remove (marker) style markers
    result = re.sub(r'\(whisper\)', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\(whispers\)', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\(sigh\)', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\(sighs\)', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\(exhale\)', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\(exhales\)', '', result, flags=re.IGNORECASE)
    
    # Remove (marker: content) style - keep only content
    result = re.sub(r'\(whisper:\s*([^)]+)\)', r'\1', result, flags=re.IGNORECASE)
    
    # Remove Chinese markers
    result = re.sub(r'【轻声[：:]\s*([^】]+)】', r'\1', result)
    result = re.sub(r'【叹气】', '', result)
    result = re.sub(r'【停顿】', '', result)
    result = re.sub(r'【好奇】', '', result)
    
    # Clean up multiple spaces
    result = re.sub(r'\s+', ' ', result)
    result = result.strip()
    
    return result


# Preset configurations for different TTS providers
TTS_FORMATTERS: Dict[str, Callable[[str], str]] = {
    'elevenlabs': format_for_elevenlabs,
    'openai': lambda text: text,  # OpenAI keeps text as-is
}


def format_text_for_tts(text: str, provider: str = 'elevenlabs') -> str:
    """
    Format text for specific TTS provider
    
    Args:
        text: Original text
        provider: TTS provider name ('elevenlabs', 'openai', etc.)
        
    Returns:
        Formatted text for the provider
    """
    formatter = TTS_FORMATTERS.get(provider.lower(), lambda x: x)
    return formatter(text)

