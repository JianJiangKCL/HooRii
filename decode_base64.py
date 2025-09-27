#!/usr/bin/env python3
"""
Base64 MP3 Decoder
Decodes base64-encoded MP3 audio data from JSON files and saves as MP3 files.
"""

import json
import base64
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import datetime


def decode_base64_mp3(input_file: str, output_file: Optional[str] = None) -> bool:
    """
    Decode base64 MP3 data from JSON file and save as MP3.
    
    Args:
        input_file: Path to JSON file containing base64 audio data
        output_file: Output MP3 file path (optional, will auto-generate if not provided)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read the JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate JSON structure
        if not isinstance(data, dict):
            print(f"Error: JSON file must contain an object, got {type(data).__name__}")
            return False
        
        # Check for required fields
        if 'audio_data' not in data:
            print("Error: JSON must contain 'audio_data' field")
            return False
        
        audio_data = data['audio_data']
        if not isinstance(audio_data, str):
            print(f"Error: 'audio_data' must be a string, got {type(audio_data).__name__}")
            return False
        
        # Generate output filename if not provided
        if output_file is None:
            input_path = Path(input_file)
            timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
            # Clean timestamp for filename
            clean_timestamp = timestamp.replace(':', '-').replace('.', '-')
            output_file = f"{input_path.stem}_{clean_timestamp}.mp3"
        
        # Decode base64 data
        try:
            decoded_data = base64.b64decode(audio_data)
        except Exception as e:
            print(f"Error decoding base64 data: {e}")
            return False
        
        # Validate MP3 header (basic check)
        if len(decoded_data) < 3:
            print("Error: Decoded data is too short to be a valid MP3")
            return False
        
        # Check for MP3 frame header (starts with 0xFF and second byte has specific bits set)
        if not (decoded_data[0] == 0xFF and (decoded_data[1] & 0xE0) == 0xE0):
            print("Warning: Data doesn't appear to have valid MP3 header, but proceeding...")
        
        # Write MP3 file
        with open(output_file, 'wb') as f:
            f.write(decoded_data)
        
        # Print summary
        print(f"Successfully decoded MP3:")
        print(f"  Input file: {input_file}")
        print(f"  Output file: {output_file}")
        print(f"  File size: {len(decoded_data):,} bytes")
        
        # Print additional metadata if available
        if 'success' in data:
            print(f"  Success: {data['success']}")
        if 'text' in data:
            print(f"  Text: {data['text']}")
        if 'voice' in data:
            print(f"  Voice: {data['voice']}")
        if 'format' in data:
            print(f"  Format: {data['format']}")
        if 'timestamp' in data:
            print(f"  Timestamp: {data['timestamp']}")
        
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
    required_fields = ['audio_data']
    optional_fields = ['success', 'text', 'voice', 'format', 'timestamp']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            print(f"Missing required field: {field}")
            return False
    
    # Validate field types
    if not isinstance(data['audio_data'], str):
        print("Field 'audio_data' must be a string")
        return False
    
    # Check optional fields if present
    if 'success' in data and not isinstance(data['success'], bool):
        print("Field 'success' must be a boolean")
        return False
    
    for field in ['text', 'voice', 'format', 'timestamp']:
        if field in data and not isinstance(data[field], str):
            print(f"Field '{field}' must be a string")
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
    success = decode_base64_mp3(args.input_file, args.output)
    
    if success:
        print("\nDecoding completed successfully!")
        sys.exit(0)
    else:
        print("\nDecoding failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
