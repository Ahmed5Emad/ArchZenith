#!/usr/bin/env python3
import os
import sys
import argparse
import requests
from pathlib import Path
import subprocess

WALLHAVEN_API = "https://wallhaven.cc/api/v1/search"
DEFAULT_WALLPAPER_DIR = Path.home() / ".config" / "wallpapers"
AGS_SCRIPTS_DIR = Path.home() / ".config" / "ags" / "scripts"

CATEGORIES = {
    "Nature": "nature",
    "Space": "space",
    "Minimalism": "minimalism",
    "Cyberpunk": "cyberpunk",
    "PixelArt": "pixel art",
}

def fetch_wallpapers(query: str, limit: int = 8) -> list:
    """Fetch high-res, strictly SFW general wallpapers from Wallhaven."""
    params = {
        "q": query,
        "categories": "100",  # 1 = General, 0 = Anime, 0 = People (strictly no anime/girls/people)
        "purity": "100",      # 100 = SFW only (strictly safe for work, absolutely no mature/sketchy content)
        "sorting": "toplist", # Top rated wallpapers
        "topRange": "1y",     # From the past year
        "atleast": "1920x1080", # Minimum full HD resolution
    }
    
    headers = {
        "User-Agent": "AGSWallpaperFetcher/1.0 (ArchLinux; Hyprland)"
    }
    
    try:
        response = requests.get(WALLHAVEN_API, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])[:limit]
    except Exception as e:
        print(f"Error calling Wallhaven API: {e}", file=sys.stderr)
        return []

def download_image(url: str, dest_path: Path) -> bool:
    """Download an image to the destination path."""
    if dest_path.exists():
        print(f"Skipping (already exists): {dest_path.name}")
        return True
        
    print(f"Downloading: {dest_path.name} ...")
    try:
        headers = {"User-Agent": "AGSWallpaperFetcher/1.0 (ArchLinux; Hyprland)"}
        r = requests.get(url, headers=headers, stream=True, timeout=30)
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Failed to download {dest_path.name}: {e}", file=sys.stderr)
        if dest_path.exists():
            dest_path.unlink()  # Remove partial download
        return False

def main():
    parser = argparse.ArgumentParser(description="Fetch and download high-quality, strictly SFW general wallpapers from Wallhaven.")
    parser.add_argument(
        "--category", 
        type=str, 
        choices=list(CATEGORIES.keys()) + ["All"], 
        default="All",
        help="The wallpaper category to download (default: All)"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=8, 
        help="Number of wallpapers to download per category (default: 8)"
    )
    
    args = parser.parse_args()
    
    categories_to_process = list(CATEGORIES.keys()) if args.category == "All" else [args.category]
    
    total_downloaded = 0
    
    for cat_name in categories_to_process:
        query = CATEGORIES[cat_name]
        dest_dir = DEFAULT_WALLPAPER_DIR / cat_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n=== Fetching '{cat_name}' wallpapers (Query: '{query}') ===")
        wallpapers = fetch_wallpapers(query, limit=args.limit)
        
        if not wallpapers:
            print(f"No wallpapers returned for category: {cat_name}")
            continue
            
        print(f"Found {len(wallpapers)} wallpapers to download.")
        
        for item in wallpapers:
            img_url = item.get("path")
            img_id = item.get("id")
            file_ext = img_url.split(".")[-1] if img_url else "jpg"
            dest_file = dest_dir / f"wallhaven_{img_id}.{file_ext}"
            
            if download_image(img_url, dest_file):
                total_downloaded += 1

    if total_downloaded > 0:
        print("\n=== Generating Thumbnails ===")
        # Run the wallpaper script to generate thumbnails for the new downloads
        try:
            get_wallpapers_script = AGS_SCRIPTS_DIR / "get-wallpapers.sh"
            if get_wallpapers_script.exists():
                print("Triggering get-wallpapers.sh to generate thumbnails...")
                subprocess.run(["bash", str(get_wallpapers_script)], stdout=subprocess.DEVNULL)
                print("Thumbnails generated successfully!")
        except Exception as e:
            print(f"Failed to generate thumbnails: {e}", file=sys.stderr)
            
        print(f"\nSuccessfully downloaded {total_downloaded} beautiful SFW wallpapers!")
        print("They are now available under the new categories in your wallpaper switcher!")
    else:
        print("\nNo new wallpapers were downloaded.")

if __name__ == "__main__":
    main()
