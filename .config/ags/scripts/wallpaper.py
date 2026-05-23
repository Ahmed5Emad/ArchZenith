#!/usr/bin/env python3

import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any

import requests


class ErrorResponse:
    """Structured error response."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
        }


def emit_error(error: "ErrorResponse") -> None:
    print(json.dumps(error.to_dict()), file=sys.stderr)


SETTINGS_PATH = Path.home() / ".config" / "ags" / "cache" / "settings" / "settings.json"
SUPPORTED_APIS = {"danbooru", "gelbooru", "safebooru", "wallhaven"}


def read_settings() -> Dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}

    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise Exception(f"Failed to read settings file: {str(exc)}")


def write_settings(data: Dict[str, Any]) -> None:
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = SETTINGS_PATH.with_suffix(f"{SETTINGS_PATH.suffix}.tmp")
        tmp_path.write_text(json.dumps(data, indent=4), encoding="utf-8")
        os.replace(tmp_path, SETTINGS_PATH)
    except Exception as exc:
        raise Exception(f"Failed to write settings file: {str(exc)}")


def ensure_wallpaper_bookmarks(settings_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    wallpaper_data = settings_data.get("wallpaper")
    if not isinstance(wallpaper_data, dict):
        wallpaper_data = {}
        settings_data["wallpaper"] = wallpaper_data

    bookmarks = wallpaper_data.get("bookmarks")
    if not isinstance(bookmarks, list):
        bookmarks = []
        wallpaper_data["bookmarks"] = bookmarks

    return bookmarks


def normalize_api_value(bookmark: Dict[str, Any]) -> str:
    api_data = bookmark.get("api")
    if isinstance(api_data, dict):
        api_value = api_data.get("value")
        return api_value if isinstance(api_value, str) else ""
    if isinstance(api_data, str):
        return api_data
    return ""


def bookmark_match(bookmark: Dict[str, Any], target_id: Any, target_api: str) -> bool:
    bookmark_id = bookmark.get("id")
    if not isinstance(bookmark_id, (int, str)):
        return False
    return str(bookmark_id) == str(target_id) and normalize_api_value(bookmark) == target_api


def find_bookmark_index(
    bookmarks: List[Dict[str, Any]], target_id: Any, target_api: str
) -> int:
    for index, bookmark in enumerate(bookmarks):
        if isinstance(bookmark, dict) and bookmark_match(
            bookmark, target_id, target_api
        ):
            return index
    return -1


def validate_bookmark_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    bookmark = payload.get("bookmark")
    if not isinstance(bookmark, dict):
        raise Exception("payload.bookmark must be an object")

    bookmark_id = bookmark.get("id")
    if not isinstance(bookmark_id, (int, str)):
        raise Exception("payload.bookmark.id must be an integer or string")

    api_data = bookmark.get("api")
    if not isinstance(api_data, dict):
        raise Exception("payload.bookmark.api must be an object")

    api_value = api_data.get("value")
    if not isinstance(api_value, str) or not api_value.strip():
        raise Exception("payload.bookmark.api.value must be a non-empty string")

    return bookmark


def list_bookmarks_action(_: Dict[str, Any]) -> List[Dict[str, Any]]:
    settings_data = read_settings()
    bookmarks = ensure_wallpaper_bookmarks(settings_data)
    return [bookmark for bookmark in bookmarks if isinstance(bookmark, dict)]


def add_bookmark_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    bookmark = validate_bookmark_payload(payload)
    bookmark_id = bookmark["id"]
    api_value = str(bookmark["api"]["value"])

    settings_data = read_settings()
    bookmarks = ensure_wallpaper_bookmarks(settings_data)

    existing_index = find_bookmark_index(bookmarks, bookmark_id, api_value)
    if existing_index == -1:
        bookmarks.append(bookmark)
        write_settings(settings_data)

    return {
        "bookmarked": True,
        "bookmarks": [b for b in bookmarks if isinstance(b, dict)],
    }


def remove_bookmark_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    bookmark = validate_bookmark_payload(payload)
    bookmark_id = bookmark["id"]
    api_value = str(bookmark["api"]["value"])

    settings_data = read_settings()
    bookmarks = ensure_wallpaper_bookmarks(settings_data)

    existing_index = find_bookmark_index(bookmarks, bookmark_id, api_value)
    if existing_index != -1:
        bookmarks.pop(existing_index)
        write_settings(settings_data)

    return {
        "bookmarked": False,
        "bookmarks": [b for b in bookmarks if isinstance(b, dict)],
    }


def toggle_bookmark_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    bookmark = validate_bookmark_payload(payload)
    bookmark_id = bookmark["id"]
    api_value = str(bookmark["api"]["value"])

    settings_data = read_settings()
    bookmarks = ensure_wallpaper_bookmarks(settings_data)

    existing_index = find_bookmark_index(bookmarks, bookmark_id, api_value)
    if existing_index == -1:
        bookmarks.append(bookmark)
        is_bookmarked = True
    else:
        bookmarks.pop(existing_index)
        is_bookmarked = False

    write_settings(settings_data)

    return {
        "bookmarked": is_bookmarked,
        "bookmarks": [b for b in bookmarks if isinstance(b, dict)],
    }


def run_bookmark_action(action: str, payload: Dict[str, Any]) -> Any:
    actions = {
        "list-bookmarks": list_bookmarks_action,
        "add-bookmark": add_bookmark_action,
        "remove-bookmark": remove_bookmark_action,
        "toggle-bookmark": toggle_bookmark_action,
    }
    handler = actions.get(action)
    if not handler:
        raise Exception(
            f"Unsupported action '{action}'. Use list-bookmarks, add-bookmark, remove-bookmark, or toggle-bookmark."
        )

    return handler(payload)


# ============================================================
# Provider interface
# ============================================================


class WallpaperProvider(ABC):
    @abstractmethod
    def fetch_posts(
        self,
        tags: List[str],
        post_id: str = "random",
        page: int = 1,
        limit: int = 6,
    ) -> Optional[List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def fetch_tags(self, tag: str, limit: int = 10) -> List[str]:
        pass


# ============================================================
# Wallhaven provider
# ============================================================


class WallhavenProvider(WallpaperProvider):
    BASE = "https://wallhaven.cc/api/v1"

    def fetch_posts(self, tags, post_id="random", page=1, limit=6):
        headers = {"User-Agent": "AGSWallpaperViewer/1.0 (ArchLinux; Hyprland)"}

        if post_id != "random":
            url = f"{self.BASE}/w/{post_id}"
            try:
                r = requests.get(url, headers=headers, timeout=15)
                r.raise_for_status()
                post = r.json().get("data", {})
                if not post:
                    return None
                posts = [post]
            except Exception as e:
                raise Exception(f"Failed to fetch wallpaper {post_id}: {str(e)}")
        else:
            filtered_tags = [
                t for t in tags if not any(r in t.lower() for r in ["rating", "explicit", "nsfw"])
            ]
            query = " ".join(filtered_tags)

            params = {
                "q": query,
                "categories": "100",  # General only (no Anime, no People)
                "purity": "100",      # SFW only
                "page": page,
                "sorting": "toplist" if not query else "relevance",
            }

            try:
                r = requests.get(f"{self.BASE}/search", params=params, headers=headers, timeout=15)
                r.raise_for_status()
                posts = r.json().get("data", [])
            except Exception as e:
                raise Exception(f"Failed to search Wallhaven: {str(e)}")

        result = []
        for post in posts:
            thumbs = post.get("thumbs", {})
            preview_url = thumbs.get("large") or thumbs.get("small")
            file_url = post.get("path")
            extension = file_url.split(".")[-1] if file_url else "jpg"

            data = {
                "id": post.get("id"),
                "url": file_url,
                "preview": preview_url,
                "width": post.get("dimension_x"),
                "height": post.get("dimension_y"),
                "extension": extension,
                "tags": [post.get("category", "general")],
            }

            if all(data.values()):
                result.append(data)

        return result or None

    def fetch_tags(self, tag, limit=10):
        curated_tags = [
            "nature", "space", "minimalism", "cyberpunk", "pixel art", 
            "abstract", "landscape", "mountains", "forest", "ocean", 
            "sunset", "city", "architecture", "cars", "night"
        ]
        matching = [t for t in curated_tags if tag.lower() in t]
        return matching[:limit]


# ============================================================
# Provider registry
# ============================================================


def get_provider(
    api: str, api_user: Optional[str] = None, api_key: Optional[str] = None
) -> Optional[WallpaperProvider]:
    """Get a provider instance with optional custom credentials."""
    api_lower = api.lower()
    if api_lower in {"danbooru", "gelbooru", "safebooru"}:
        api_lower = "wallhaven"
    providers = {
        "wallhaven": lambda: WallhavenProvider(),
    }
    factory = providers.get(api_lower)
    return factory() if factory else None


# ============================================================
# CLI
# ============================================================


def main():
    if len(sys.argv) < 2:
        error = ErrorResponse(
            "MISSING_ARGS",
            "Missing required arguments. Use --api [wallhaven] and optional --id/--tags/--tag/--page/--limit/--api-user/--api-key.",
        )
        emit_error(error)
        sys.exit(1)

    api = None
    post_id = "random"
    tags: List[str] = []
    page = 1
    limit = 6
    tag_query = None
    api_user = None
    api_key = None
    action = None
    payload_json = None

    try:
        for i in range(1, len(sys.argv)):
            if sys.argv[i] == "--api":
                api = sys.argv[i + 1].lower()
            elif sys.argv[i] == "--id":
                post_id = sys.argv[i + 1]
            elif sys.argv[i] == "--tags":
                tags = sys.argv[i + 1].split(",")
            elif sys.argv[i] == "--tag":
                tag_query = sys.argv[i + 1]
            elif sys.argv[i] == "--page":
                page = int(sys.argv[i + 1])
            elif sys.argv[i] == "--limit":
                limit = int(sys.argv[i + 1])
            elif sys.argv[i] == "--api-user":
                api_user = sys.argv[i + 1]
            elif sys.argv[i] == "--api-key":
                api_key = sys.argv[i + 1]
            elif sys.argv[i] == "--action":
                action = sys.argv[i + 1].strip().lower()
            elif sys.argv[i] == "--payload-json":
                payload_json = sys.argv[i + 1]
    except (IndexError, ValueError) as e:
        error = ErrorResponse("INVALID_ARGS", f"Invalid argument format: {str(e)}")
        emit_error(error)
        sys.exit(1)

    if api:
        api = api.lower()
        if api in {"danbooru", "gelbooru", "safebooru"}:
            api = "wallhaven"

    if action:
        payload: Dict[str, Any] = {}
        if payload_json:
            try:
                parsed_payload = json.loads(payload_json)
            except json.JSONDecodeError as exc:
                error = ErrorResponse(
                    "INVALID_PAYLOAD", f"Invalid payload JSON: {str(exc)}"
                )
                emit_error(error)
                sys.exit(1)

            if not isinstance(parsed_payload, dict):
                error = ErrorResponse(
                    "INVALID_PAYLOAD", "Payload JSON must be an object."
                )
                emit_error(error)
                sys.exit(1)
            payload = parsed_payload

        try:
            result = run_bookmark_action(action, payload)
            print(json.dumps(result))
            return
        except Exception as e:
            error = ErrorResponse("BOOKMARK_ACTION_FAILED", str(e))
            emit_error(error)
            sys.exit(1)

    if not api:
        error = ErrorResponse(
            "MISSING_API",
            "API source is required. Use --api [wallhaven].",
        )
        emit_error(error)
        sys.exit(1)

    if api not in SUPPORTED_APIS:
        error = ErrorResponse(
            "INVALID_API",
            f"Invalid API source '{api}'. Use wallhaven.",
        )
        emit_error(error)
        sys.exit(1)

    try:
        provider = get_provider(api, api_user, api_key)
        if not provider:
            error = ErrorResponse(
                "PROVIDER_ERROR",
                f"Failed to initialize provider for API: {api}.",
            )
            emit_error(error)
            sys.exit(1)

        if tag_query:
            data = provider.fetch_tags(tag_query)
        else:
            data = provider.fetch_posts(tags, post_id, page, limit)

        if data is None or (isinstance(data, list) and len(data) == 0):
            if tag_query:
                # Output [] and exit cleanly (status code 0) on empty tag suggestions
                print(json.dumps([]))
                sys.exit(0)

            error = ErrorResponse(
                "NO_RESULTS",
                "No results found. Try different tags or verify the post exists.",
            )
            emit_error(error)
            sys.exit(1)

        print(json.dumps(data))
    except Exception as e:
        error = ErrorResponse("UNEXPECTED_ERROR", str(e))
        emit_error(error)
        sys.exit(1)


if __name__ == "__main__":
    main()
