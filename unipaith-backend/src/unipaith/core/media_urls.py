"""Resolve stored S3 keys to presigned download URLs for client display."""

from __future__ import annotations

from unipaith.core.s3 import S3Client


def _is_absolute_url(value: str) -> bool:
    return value.startswith(("http://", "https://", "file://", "data:"))


def resolve_media_urls(media_urls: object) -> list | dict | None:
    """Turn S3 object keys in post media payloads into fetchable URLs."""
    if media_urls is None:
        return None
    if not isinstance(media_urls, list):
        return media_urls

    s3 = S3Client()
    resolved: list = []
    for item in media_urls:
        if isinstance(item, dict):
            url = str(item.get("url") or item.get("key") or "")
            if url and not _is_absolute_url(url):
                resolved.append({**item, "url": s3.generate_download_url(url)})
            else:
                resolved.append(item)
        elif isinstance(item, str):
            if item and not _is_absolute_url(item):
                resolved.append(s3.generate_download_url(item))
            else:
                resolved.append(item)
        else:
            resolved.append(item)
    return resolved
