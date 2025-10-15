#!/usr/bin/env python3
"""
General purpose Base64 audio decoder
Handles OpenAI and Agora JSON payloads with optional metadata.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import datetime
import re
import base64


DEFAULT_PROVIDER = "auto"
SUPPORTED_FORMATS = {
    "base64_mp3": {
        "extension": ".mp3",
        "mime_prefix": "audio/mpeg",
        "description": "Base64-encoded MP3 audio"
    },
    "base64_wav": {
        "extension": ".wav",
        "mime_prefix": "audio/wav",
        "description": "Base64-encoded WAV audio"
    },
    "base64_pcm": {
        "extension": ".pcm",
        "mime_prefix": "audio/basic",
        "description": "Base64-encoded PCM audio"
    }
}

# Precompiled regex for common data URL prefixes
DATA_URL_PATTERN = re.compile(r"^data:(?P<mime>[^;]+);base64,(?P<data>.+)$", re.IGNORECASE)


def _merge_metadata(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    """Merge metadata dictionaries preferring values already set in base."""
    keys = ("provider", "format", "audio_format", "voice", "timestamp", "speaker")
    for key in keys:
        if base.get(key) in (None, ""):
            value = extra.get(key)
            if value not in (None, ""):
                base[key] = value
    return base


def _coerce_provider_hint(provider_hint: Optional[str]) -> Optional[str]:
    """Normalise provider hint input."""
    if provider_hint is None:
        return None
    normalized = provider_hint.strip()
    if not normalized or normalized.lower() == "auto":
        return None
    return normalized


def _extract_audio_fields(
    payload: Dict[str, Any],
    provider_hint: Optional[str] = None,
    depth: int = 0,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """Extract base64 audio string and related metadata from nested payloads."""
    if depth > 5 or not isinstance(payload, dict):
        return None, {"provider": provider_hint}

    metadata: Dict[str, Any] = {
        "provider": payload.get("provider") or provider_hint,
        "format": payload.get("format"),
        "audio_format": payload.get("audio_format"),
        "voice": payload.get("voice") or payload.get("speaker"),
        "timestamp": payload.get("timestamp"),
        "speaker": payload.get("speaker"),
    }

    audio_data: Optional[str] = None

    def consider_value(value: Any) -> bool:
        nonlocal audio_data
        if audio_data is None and isinstance(value, str):
            stripped = value.strip()
            if stripped:
                audio_data = stripped
                return True
        return False

    def merge_metadata(source: Dict[str, Any]) -> None:
        nonlocal metadata
        metadata = _merge_metadata(metadata, source)

    direct_keys = (
        "audio_data",
        "audioBase64",
        "audio_base64",
        "audioBase64String",
        "data",
        "value",
    )
    for key in direct_keys:
        if consider_value(payload.get(key)):
            merge_metadata(payload)
            return audio_data, metadata

    nested_keys = (
        "audio",
        "audio_generation_result",
        "audioResult",
        "tts_result",
        "tts",
        "result",
        "response",
        "payload",
        "output",
    )

    for nested_key in nested_keys:
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            merge_metadata(nested)
            nested_audio, nested_meta = _extract_audio_fields(nested, metadata.get("provider"), depth + 1)
            if nested_audio:
                metadata = _merge_metadata(metadata, nested_meta)
                return nested_audio, metadata
        elif isinstance(nested, list):
            for item in nested:
                if isinstance(item, dict):
                    nested_audio, nested_meta = _extract_audio_fields(item, metadata.get("provider"), depth + 1)
                    if nested_audio:
                        metadata = _merge_metadata(metadata, nested_meta)
                        return nested_audio, metadata
        elif isinstance(nested, str):
            stripped = nested.strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                try:
                    nested_json = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                nested_audio, nested_meta = _extract_audio_fields(nested_json, metadata.get("provider"), depth + 1)
                if nested_audio:
                    metadata = _merge_metadata(metadata, nested_meta)
                    return nested_audio, metadata

    return audio_data, metadata


def _validate_audio_bytes(decoded_data: bytes, format_key: str) -> bool:
    """Perform basic validation on decoded audio bytes based on format."""
    if not decoded_data:
        print("Error: Decoded data is empty")
        return False

    fmt = (format_key or "").lower()

    if fmt.endswith("_mp3") or fmt == "mp3":
        if len(decoded_data) < 3:
            print("Error: Decoded data is too short to be a valid MP3")
            return False
        if not (decoded_data[0] == 0xFF and (decoded_data[1] & 0xE0) == 0xE0):
            print("Warning: Data doesn't appear to have a valid MP3 header, but proceeding...")
    elif fmt.endswith("_wav") or fmt == "wav":
        if len(decoded_data) < 12 or not decoded_data.startswith(b"RIFF"):
            print("Warning: Data doesn't appear to have a valid WAV header, but proceeding...")
    elif fmt.endswith("_pcm") or fmt == "pcm":
        if len(decoded_data) < 2:
            print("Warning: Decoded PCM data is very short; verify source data")

    return True


def _strip_data_url_prefix(audio_data: str) -> Tuple[str, Optional[str]]:
    """Strip data URL prefix if present and return raw base64 plus MIME."""
    match = DATA_URL_PATTERN.match(audio_data.strip())
    if match:
        return match.group("data"), match.group("mime")
    return audio_data, None


def _detect_format_from_metadata(metadata: Dict[str, Any]) -> str:
    """Detect the expected audio format key from metadata."""
    format_hint = metadata.get("format") or metadata.get("audio_format")
    voice = metadata.get("voice")
    provider = metadata.get("provider")

    if isinstance(format_hint, str):
        normalized = format_hint.strip().lower()
        if normalized in SUPPORTED_FORMATS:
            return normalized
        if normalized.startswith("base64_"):
            return normalized
        if normalized in {"mp3", "wav", "pcm"}:
            return f"base64_{normalized}"

    if isinstance(provider, str) and provider.strip().lower() == "agora":
        return "base64_mp3"

    if isinstance(voice, str) and voice.endswith(".wav"):
        return "base64_wav"

    return "base64_mp3"


def _select_output_extension(format_key: str, mime_hint: Optional[str]) -> str:
    """Resolve the proper file extension based on format key and MIME hint."""
    fmt = format_key.lower()
    if fmt in SUPPORTED_FORMATS:
        return SUPPORTED_FORMATS[fmt]["extension"]

    if mime_hint:
        mime_lower = mime_hint.lower()
        if "mpeg" in mime_lower or "mp3" in mime_lower:
            return ".mp3"
        if "wav" in mime_lower:
            return ".wav"
        if "pcm" in mime_lower:
            return ".pcm"

    if fmt.endswith("_mp3"):
        return ".mp3"
    if fmt.endswith("_wav"):
        return ".wav"
    if fmt.endswith("_pcm"):
        return ".pcm"

    return ".mp3"


def _sanitize_filename_component(value: str) -> str:
    """Make a string safe for filenames."""
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
    return sanitized.strip("_") or "audio"


def _build_output_path(input_path: Path, metadata: Dict[str, Any], output_file: Optional[str], format_key: str, mime_hint: Optional[str]) -> Path:
    """Determine output path from metadata and format."""
    if output_file:
        return Path(output_file).expanduser().resolve()

    timestamp = metadata.get("timestamp") or datetime.datetime.now().isoformat()
    clean_timestamp = _sanitize_filename_component(timestamp.replace(":", "-").replace(".", "-"))
    voice = metadata.get("voice") or metadata.get("speaker") or "voice"
    clean_voice = _sanitize_filename_component(str(voice))

    extension = _select_output_extension(format_key, mime_hint)
    return (input_path.parent / f"{input_path.stem}_{clean_voice}_{clean_timestamp}{extension}").resolve()


def decode_base64_audio(input_file: str, output_file: Optional[str] = None, provider: str = DEFAULT_PROVIDER) -> bool:
    """Decode base64 audio data from JSON file and save to an audio file."""
    try:
        # Read the JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate JSON structure
        if not isinstance(data, dict):
            print(f"Error: JSON file must contain an object, got {type(data).__name__}")
            return False
        
        provider_hint = _coerce_provider_hint(provider)
        audio_data, metadata = _extract_audio_fields(data, provider_hint)

        if audio_data is None:
            print("Error: JSON payload does not contain base64 audio data")
            return False

        if not isinstance(audio_data, str):
            print(f"Error: Extracted audio data must be a string, got {type(audio_data).__name__}")
            return False

        audio_data, mime_hint = _strip_data_url_prefix(audio_data)

        # Detect format and determine output path
        format_key = _detect_format_from_metadata(metadata)
        output_path = _build_output_path(Path(input_file), metadata, output_file, format_key, mime_hint)

        # Decode base64 data
        try:
            decoded_data = base64.b64decode(audio_data)
        except Exception as e:
            print(f"Error decoding base64 data: {e}")
            return False

        if not _validate_audio_bytes(decoded_data, format_key):
            return False

        # Write audio file
        with open(output_path, 'wb') as f:
            f.write(decoded_data)

        # Print summary
        print("Successfully decoded audio:")
        print(f"  Input file: {input_file}")
        print(f"  Output file: {output_path}")
        print(f"  File size: {len(decoded_data):,} bytes")

        # Print additional metadata if available
        if 'success' in data:
            print(f"  Success: {data['success']}")
        text_value = data.get('text') or metadata.get('text')
        if text_value:
            print(f"  Text: {text_value}")
        if metadata.get("voice"):
            print(f"  Voice: {metadata['voice']}")
        if metadata.get("format"):
            print(f"  Format: {metadata['format']}")
        if metadata.get("timestamp"):
            print(f"  Timestamp: {metadata['timestamp']}")
        if metadata.get("provider"):
            print(f"  Provider: {metadata['provider']}")
        if mime_hint:
            print(f"  MIME hint: {mime_hint}")
        
        return True
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        return False
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def validate_json_structure(data: Dict[str, Any]) -> bool:
    """
    Validate the expected JSON structure for audio data.
    
    Args:
        data: Parsed JSON data
    
    Returns:
        bool: True if structure is valid
    """
    optional_fields = ['success', 'text', 'voice', 'format', 'timestamp']

    audio_data, metadata = _extract_audio_fields(data)

    if audio_data is None:
        print("Missing required audio data field (expected 'audio_data' or an 'audio.data' object)")
        return False

    if not isinstance(audio_data, str):
        print(f"Audio data must be a string, got {type(audio_data).__name__}")
        return False
    
    # Check optional fields if present
    if 'success' in data and not isinstance(data['success'], bool):
        print("Field 'success' must be a boolean")
        return False
    
    for field in optional_fields:
        value = data.get(field)
        if value is not None and not isinstance(value, str):
            print(f"Field '{field}' must be a string when present")
            return False

    if metadata.get('voice') is not None and not isinstance(metadata['voice'], str):
        print("Extracted 'voice' metadata must be a string")
        return False
    
    return True


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Decode base64-encoded MP3 audio data from JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python decode_base64.py audio_data.json
  python decode_base64.py audio_data.json -o output.mp3
  python decode_base64.py audio_data.json --validate-only

JSON Format:
  {
    "success": true,
    "audio_data": "base64_encoded_mp3_data_here",
    "text": "transcription text",
    "voice": "voice_name",
    "format": "base64_mp3",
    "timestamp": "2025-09-27T00:59:51.695467"
  }
        """
    )
    
    parser.add_argument('input_file', help='Input JSON file containing base64 audio data')
    parser.add_argument('-o', '--output', help='Output MP3 file path')
    parser.add_argument('--validate-only', action='store_true', 
                       help='Only validate JSON structure without decoding')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    parser.add_argument('--provider', help='Specify provider hint when format detection fails (e.g., agora, openai)', default=DEFAULT_PROVIDER)
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' does not exist")
        sys.exit(1)
    
    # Validate JSON structure if requested
    if args.validate_only:
        try:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if validate_json_structure(data):
                print("JSON structure is valid")
                sys.exit(0)
            else:
                print("JSON structure is invalid")
                sys.exit(1)
        except Exception as e:
            print(f"Error validating JSON: {e}")
            sys.exit(1)
    
    # Decode the MP3
    success = decode_base64_audio(args.input_file, args.output, provider=args.provider)
    
    if success:
        print("\nDecoding completed successfully!")
        sys.exit(0)
    else:
        print("\nDecoding failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
