#!/usr/bin/env python3
"""
Audio cache utilities
 - Decode base64 audio data and persist as MP3 files under cached_audio
 - Optionally upload files to a free temporary hosting service to obtain a shareable URL
 - Construct local static URLs served by FastAPI (mounted at /cached_audio)
"""

import base64
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


# Absolute path to the repository root (three levels up from this file)
REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO_ROOT / "cached_audio"


def ensure_cache_dir() -> Path:
    """Ensure the cached_audio directory exists and return its Path."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def _sanitize_base64(data: str) -> str:
    """Strip data URL prefixes if present and return pure base64 payload."""
    if not data:
        return data
    prefix_sep = ";base64,"
    if prefix_sep in data:
        try:
            return data.split(prefix_sep, 1)[1]
        except Exception:
            return data
    return data


def save_base64_mp3_to_cache(base64_audio: str, filename_hint: Optional[str] = None) -> Tuple[str, str]:
    """
    Save base64-encoded MP3 bytes into cached_audio directory.

    Returns:
      (absolute_file_path, relative_url_path)
    where relative_url_path is suitable to be prefixed by FastAPI base URL (e.g., /cached_audio/<file>.mp3)
    """
    ensure_cache_dir()

    safe_hint = (filename_hint or "audio").strip().replace(" ", "_")[:40]
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{safe_hint}_{timestamp}_{unique_id}.mp3"
    file_path = CACHE_DIR / filename

    payload = _sanitize_base64(base64_audio)
    audio_bytes = base64.b64decode(payload)
    with open(file_path, "wb") as f:
        f.write(audio_bytes)

    # Relative URL (served by FastAPI StaticFiles mounted at /cached_audio)
    url_path = f"/cached_audio/{filename}"
    return str(file_path), url_path


def make_absolute_url(relative_url: str, public_base_url: Optional[str]) -> Optional[str]:
    """Compose absolute URL from public base if provided; else None."""
    if not relative_url:
        return None
    if public_base_url:
        base = public_base_url.rstrip("/")
        if relative_url.startswith("/"):
            return f"{base}{relative_url}"
        return f"{base}/{relative_url}"
    return None


def try_upload_temp_cloud(file_path: str, preferred_host: Optional[str] = None) -> Optional[str]:
    """
    Best-effort upload to a free temporary file hosting service.
    Attempts preferred host first if provided, then transfer.sh (PUT), then file.io.
    Returns a public URL on success, or None on failure.
    """
    # Lazy import requests if available; otherwise skip
    try:
        import requests  # type: ignore
    except Exception:
        return None

    try:
        filename = os.path.basename(file_path)

        # Only use catbox.moe as requested
        def _upload_once(timeout_s: int = 120) -> Optional[str]:
            try:
                with open(file_path, "rb") as fh:
                    resp = requests.post(
                        "https://catbox.moe/user/api.php",
                        data={"reqtype": "fileupload"},
                        files={"fileToUpload": (filename, fh)},
                        timeout=timeout_s
                    )
                if resp.ok:
                    url_candidate = resp.text.strip()
                    if url_candidate.startswith("http"):
                        return url_candidate
            except Exception:
                return None
            return None

        def _verify_size(url: str) -> bool:
            try:
                local_size = os.path.getsize(file_path)
                head = requests.head(url, allow_redirects=True, timeout=20)
                remote_size_str = head.headers.get("Content-Length")
                if not remote_size_str:
                    return True  # cannot verify; assume OK
                remote_size = int(remote_size_str)
                # Consider OK if remote >= 98% of local (some hosts re-encode headers)
                return remote_size >= int(local_size * 0.98)
            except Exception:
                return True  # on any error, don't block

        # First attempt
        url = _upload_once(timeout_s=120)
        if url and _verify_size(url):
            return url
        # Retry once if size mismatch or upload failed
        url = _upload_once(timeout_s=180)
        if url and _verify_size(url):
            return url
        return url

        # No fallbacks per user request

    except Exception:
        return None

    return None


