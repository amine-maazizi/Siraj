#!/usr/bin/env python3
"""
Siraj Data Cleanup Script

This script clears all data from:
1. ChromaDB vector store
2. SirajProjects directory 
3. SQLite databases
4. Media files (audio, video, subs, manifests, etc.)

Usage:
    python clear_data.py [--confirm] [--keep-projects]
    
Options:
    --confirm       Skip confirmation prompt
    --keep-projects Keep SirajProjects directory structure but clear contents
"""

import os
import sys
import shutil
import sqlite3
import argparse
from pathlib import Path

# Add server to path for imports
sys.path.insert(0, str(Path(__file__).parent / "server"))

try:
    from config import (
        PROJECTS_DIR, FALLBACK_CHROMA_DIR, ACTIVE_PATHS_FILE,
        resolve_chroma_dir, _read_active_paths
    )
except ImportError:
    print("Warning: Could not import server config. Using default paths.")
    PROJECTS_DIR = Path("./SirajProjects")
    FALLBACK_CHROMA_DIR = Path("./server/store/chroma")
    ACTIVE_PATHS_FILE = Path("./server/store/active_paths.json")

def clear_chromadb():
    """Clear ChromaDB vector stores."""
    print("🗑️  Clearing ChromaDB...")
    
    # Clear fallback chroma directory
    if FALLBACK_CHROMA_DIR.exists():
        print(f"   Removing fallback ChromaDB: {FALLBACK_CHROMA_DIR}")
        shutil.rmtree(FALLBACK_CHROMA_DIR)
    
    # Clear active project chroma if different
    try:
        active_chroma = resolve_chroma_dir()
        if active_chroma != FALLBACK_CHROMA_DIR and active_chroma.exists():
            print(f"   Removing active ChromaDB: {active_chroma}")
            shutil.rmtree(active_chroma)
    except Exception as e:
        print(f"   Warning: Could not resolve active chroma dir: {e}")
    
    # Recreate empty directories
    FALLBACK_CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    print("   ✅ ChromaDB cleared")

def clear_databases():
    """Clear SQLite databases."""
    print("🗑️  Clearing SQLite databases...")
    
    db_files = [
        Path("server/store/siraj.sqlite3"),
        Path("server/store/sqlite.db"),
    ]
    
    for db_file in db_files:
        if db_file.exists():
            print(f"   Clearing database: {db_file}")
            try:
                # Connect and drop all tables
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                # Drop each table
                for table in tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
                
                conn.commit()
                conn.close()
                print(f"   ✅ Database {db_file} cleared")
            except Exception as e:
                print(f"   ❌ Error clearing {db_file}: {e}")

def clear_media():
    """Clear media files (audio, video, subs, etc.)."""
    print("🗑️  Clearing media files...")
    
    media_dirs = [
        Path("server/media/audio"),
        Path("server/media/video"), 
        Path("server/media/subs"),
        Path("server/media/manifests"),
        Path("server/media/thumbs"),
        Path("_out"),  # Generated videos output directory
    ]
    
    for media_dir in media_dirs:
        if media_dir.exists():
            print(f"   Clearing {media_dir}...")
            # Remove all files but keep directory structure
            for item in media_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print(f"   ✅ {media_dir} cleared")

def clear_projects(keep_structure=False):
    """Clear SirajProjects directory."""
    print("🗑️  Clearing SirajProjects...")
    
    if not PROJECTS_DIR.exists():
        print("   ℹ️  SirajProjects directory doesn't exist")
        return
    
    if keep_structure:
        print(f"   Clearing contents of {PROJECTS_DIR} (keeping structure)...")
        for project_dir in PROJECTS_DIR.iterdir():
            if project_dir.is_dir():
                # Clear resources and media subdirectories
                for subdir in ["resources", "media"]:
                    subdir_path = project_dir / subdir
                    if subdir_path.exists():
                        for item in subdir_path.iterdir():
                            if item.is_file():
                                item.unlink()
                            elif item.is_dir():
                                shutil.rmtree(item)
                        print(f"   ✅ Cleared {subdir_path}")
                
                # Remove .sirajproj files
                for proj_file in project_dir.glob("*.sirajproj"):
                    proj_file.unlink()
                    print(f"   ✅ Removed {proj_file}")
    else:
        print(f"   Removing entire {PROJECTS_DIR}...")
        shutil.rmtree(PROJECTS_DIR)
        print(f"   ✅ SirajProjects removed")

def clear_active_paths():
    """Clear active paths configuration."""
    print("🗑️  Clearing active paths...")
    
    if ACTIVE_PATHS_FILE.exists():
        ACTIVE_PATHS_FILE.unlink()
        print(f"   ✅ Removed {ACTIVE_PATHS_FILE}")
    else:
        print("   ℹ️  No active paths file found")

def main():
    parser = argparse.ArgumentParser(description="Clear Siraj application data")
    parser.add_argument("--confirm", action="store_true", 
                       help="Skip confirmation prompt")
    parser.add_argument("--keep-projects", action="store_true",
                       help="Keep SirajProjects directory structure but clear contents")
    
    args = parser.parse_args()
    
    print("🧹 Siraj Data Cleanup Script")
    print("=" * 50)
    
    if not args.confirm:
        print("\n⚠️  WARNING: This will permanently delete:")
        print("   • All ChromaDB vector stores")
        print("   • All SQLite database data")
        print("   • All media files (audio, video, captions)")
        print("   • All SirajProjects" + (" contents" if args.keep_projects else ""))
        print("   • Active project configuration")
        
        response = input("\nAre you sure you want to continue? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("❌ Cleanup cancelled")
            return
    
    print("\n🚀 Starting cleanup...")
    
    try:
        clear_chromadb()
        clear_databases()
        clear_media()
        clear_projects(keep_structure=args.keep_projects)
        clear_active_paths()
        
        print("\n🎉 Cleanup completed successfully!")
        print("\nNext steps:")
        print("   1. Restart your server if running")
        print("   2. Upload new documents to start fresh")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
