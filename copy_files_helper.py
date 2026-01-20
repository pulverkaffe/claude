#!/usr/bin/env python3
"""
Helper script to copy podcast files from Desktop to posts directory
Run this from your Mac Terminal
"""

import shutil
from pathlib import Path

# Source and destination
source_dir = Path("/Users/daniel/Desktop/podcast files")
dest_dir = Path("/home/user/claude/posts")

print("🐝 Podcast Files Copy Helper")
print("=" * 50)
print(f"Source: {source_dir}")
print(f"Destination: {dest_dir}")
print()

# Check if source exists
if not source_dir.exists():
    print(f"❌ Error: Source directory not found!")
    print(f"   {source_dir}")
    exit(1)

# Check if destination exists
if not dest_dir.exists():
    print(f"❌ Error: Destination directory not found!")
    print(f"   {dest_dir}")
    print()
    print("The destination should be accessible from your Mac.")
    print("It's the directory where the beehiiv_import.py script is located.")
    exit(1)

# Find all podd_*.md files
podcast_files = list(source_dir.glob("podd_*.md"))

if not podcast_files:
    print(f"❌ No podd_*.md files found in {source_dir}")
    exit(1)

print(f"📁 Found {len(podcast_files)} podcast file(s)")
print()

# Copy files
copied = 0
failed = 0

for file in podcast_files:
    try:
        dest_file = dest_dir / file.name
        shutil.copy2(file, dest_file)
        print(f"✅ Copied: {file.name}")
        copied += 1
    except Exception as e:
        print(f"❌ Failed: {file.name} - {e}")
        failed += 1

print()
print("=" * 50)
print(f"✅ Successfully copied: {copied}")
print(f"❌ Failed: {failed}")
print()
print("Now you can run: python beehiiv_import.py")
