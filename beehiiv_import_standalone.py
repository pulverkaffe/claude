#!/usr/bin/env python3
"""
beehiiv Import Script - Standalone Version
Save this file to your Desktop and run it from the "podcast files" folder
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import re

try:
    import markdown
except ImportError:
    print("Installing required package: markdown...")
    os.system(f"{sys.executable} -m pip install markdown --quiet")
    import markdown

# ===== CONFIGURATION - EDIT THESE VALUES =====
API_KEY = 'y5rLYdyFKOCDLHuupb2R91MZjyRNS8Jhq4Gls6gzabbR8z9nEqwErSTzAvETQVVq'
PUBLICATION_ID = 'pub_3f662e64-d49f-4f5a-b581-59efae1b3b31'
# ============================================

BASE_URL = 'https://api.beehiiv.com/v2'
IMPORT_LOG = 'beehiiv_import_log.json'
DRY_RUN = False  # Set to True to test without creating posts
DELAY_BETWEEN_POSTS = 2  # seconds


class BeehiivImporter:
    def __init__(self):
        self.headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        self.import_log = self.load_import_log()
        self.md = markdown.Markdown(extensions=['extra', 'meta', 'nl2br', 'sane_lists'])

    def load_import_log(self) -> Dict:
        """Load the import log to track what's been imported"""
        if os.path.exists(IMPORT_LOG):
            with open(IMPORT_LOG, 'r') as f:
                return json.load(f)
        return {'imported': {}, 'failed': {}}

    def save_import_log(self):
        """Save the import log"""
        with open(IMPORT_LOG, 'w') as f:
            json.dump(self.import_log, f, indent=2)

    def get_markdown_files(self) -> List[Path]:
        """Get all markdown files from the current directory"""
        current_dir = Path('.')
        md_files = list(current_dir.glob('podd_*.md'))
        return sorted(md_files)

    def parse_markdown_file(self, file_path: Path) -> Optional[Dict]:
        """Parse a markdown file and extract metadata and content"""
        try:
            # Read the raw file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract episode number from filename (e.g., podd_2.md -> 2)
            episode_match = re.search(r'podd_(\d+)', file_path.stem)
            episode_num = episode_match.group(1) if episode_match else None

            # Remove leading zeros (02 -> 2, 003 -> 3)
            if episode_num:
                episode_num = str(int(episode_num))

            lines = content.split('\n')

            # Find the first h1 (# Title)
            h1_title = None
            h1_index = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('# '):
                    h1_title = line.strip()[2:].strip()  # Remove '# ' prefix
                    h1_index = i
                    break

            if not h1_title:
                print(f"  ⚠️  Warning: No h1 found in {file_path.name}, using filename")
                h1_title = file_path.stem

            # Remove "Podd X:" prefix from title if present
            if h1_title:
                h1_title = re.sub(r'^Podd\s+\d+:\s*', '', h1_title, flags=re.IGNORECASE)

            # Format title as "Podcast #X – Title" if episode number exists
            if episode_num:
                title = f"Podcast #{episode_num} – {h1_title}"
            else:
                title = h1_title

            # Extract subtitle (italic section after h1)
            subtitle = ""
            subtitle_lines = []
            body_start_index = h1_index + 1

            if h1_index >= 0:
                # Look for italic text after h1
                for i in range(h1_index + 1, len(lines)):
                    line = lines[i].strip()
                    if not line:  # Skip empty lines
                        continue
                    # Check if line is italic
                    if (line.startswith('*') and not line.startswith('**')) or \
                       (line.startswith('_') and not line.startswith('__')) or \
                       ('*' in line and not '**' in line):
                        # Remove markdown italic syntax
                        clean_line = re.sub(r'[*_]', '', line)
                        subtitle_lines.append(clean_line)
                        body_start_index = i + 1
                    else:
                        # Found non-italic content, stop looking for subtitle
                        break

            subtitle = ' '.join(subtitle_lines)

            # Get the rest as body content (skip h1 and subtitle lines)
            body_lines = lines[body_start_index:]
            body_content = '\n'.join(body_lines).strip()

            # Convert markdown to HTML
            html_content = self.md.convert(body_content)

            # Build post data
            post_data = {
                'title': title,
                'body_content': html_content,
                'status': 'draft'
            }

            # Add subtitle if found
            if subtitle:
                post_data['subtitle'] = subtitle

            # Store file info for logging
            post_data['_source_file'] = str(file_path)

            return post_data

        except Exception as e:
            print(f"❌ Error parsing {file_path.name}: {e}")
            return None

    def create_draft_post(self, post_data: Dict) -> Optional[str]:
        """Create a draft post in beehiiv"""
        endpoint = f"{BASE_URL}/publications/{PUBLICATION_ID}/posts"

        # Remove internal fields
        source_file = post_data.pop('_source_file', 'unknown')

        try:
            if DRY_RUN:
                print(f"  [DRY RUN] Would create post: {post_data['title']}")
                return 'dry-run-id'

            response = requests.post(endpoint, json=post_data, headers=self.headers)

            if response.status_code == 201:
                result = response.json()
                post_id = result.get('data', {}).get('id')
                print(f"  ✅ Created draft: {post_data['title']}")
                return post_id
            elif response.status_code == 429:
                print(f"  ⚠️  Rate limit hit. Waiting 60 seconds...")
                time.sleep(60)
                return self.create_draft_post({**post_data, '_source_file': source_file})
            else:
                print(f"  ❌ Failed to create post: {response.status_code}")
                print(f"     Response: {response.text}")
                return None

        except Exception as e:
            print(f"  ❌ Error creating post: {e}")
            return None

    def import_posts(self):
        """Import all markdown files as draft posts"""
        print("🐝 beehiiv Import Script - Standalone Version")
        print("=" * 50)
        print(f"Working directory: {os.getcwd()}")
        print()

        if DRY_RUN:
            print("🔍 DRY RUN MODE - No posts will be created")
            print()

        # Get all markdown files
        md_files = self.get_markdown_files()

        if not md_files:
            print(f"⚠️  No podd_*.md files found in current directory")
            print(f"   Make sure you're running this script from the 'podcast files' folder")
            return

        print(f"📁 Found {len(md_files)} podcast file(s)")
        print()

        # Filter out already imported files
        files_to_import = [
            f for f in md_files
            if str(f) not in self.import_log['imported']
        ]

        if len(files_to_import) < len(md_files):
            skipped = len(md_files) - len(files_to_import)
            print(f"⏭️  Skipping {skipped} already imported file(s)")
            print()

        if not files_to_import:
            print("✅ All files have already been imported!")
            return

        print(f"📝 Importing {len(files_to_import)} file(s)...")
        print()

        # Import each file
        success_count = 0
        failed_count = 0

        for i, file_path in enumerate(files_to_import, 1):
            print(f"[{i}/{len(files_to_import)}] Processing: {file_path.name}")

            # Parse the markdown file
            post_data = self.parse_markdown_file(file_path)

            if not post_data:
                failed_count += 1
                self.import_log['failed'][str(file_path)] = {
                    'timestamp': datetime.now().isoformat(),
                    'error': 'Failed to parse file'
                }
                continue

            # Create the draft post
            post_id = self.create_draft_post(post_data)

            if post_id:
                success_count += 1
                self.import_log['imported'][str(file_path)] = {
                    'post_id': post_id,
                    'timestamp': datetime.now().isoformat(),
                    'title': post_data['title']
                }
            else:
                failed_count += 1
                self.import_log['failed'][str(file_path)] = {
                    'timestamp': datetime.now().isoformat(),
                    'error': 'Failed to create post'
                }

            # Save progress after each import
            self.save_import_log()

            # Wait before next import to avoid rate limiting
            if i < len(files_to_import):
                time.sleep(DELAY_BETWEEN_POSTS)

            print()

        # Print summary
        print("=" * 50)
        print("📊 Import Summary")
        print("=" * 50)
        print(f"✅ Successfully imported: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📋 Total processed: {len(files_to_import)}")
        print()

        if not DRY_RUN:
            print(f"💾 Import log saved to: {IMPORT_LOG}")
            print("   (Use this to track imported posts and avoid duplicates)")

        print()
        print("🎉 Done!")


def main():
    """Main entry point"""
    print()
    print("=" * 50)
    print("INSTRUCTIONS:")
    print("=" * 50)
    print("1. Save this script to your 'podcast files' folder")
    print("2. Open Terminal and navigate to that folder:")
    print("   cd '/Users/daniel/Desktop/podcast files'")
    print("3. Run: python3 beehiiv_import_standalone.py")
    print("=" * 50)
    print()

    try:
        importer = BeehiivImporter()
        importer.import_posts()
    except KeyboardInterrupt:
        print("\n\n⚠️  Import interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
