#!/bin/bash
# Helper script to copy podcast files
# Run this script on your Mac

SOURCE_DIR="/Users/daniel/Desktop/podcast files"
DEST_DIR="/home/user/claude/posts"

echo "Copying podcast files..."
echo "From: $SOURCE_DIR"
echo "To: $DEST_DIR"
echo ""

# Copy all podd_*.md files
cp "$SOURCE_DIR"/podd_*.md "$DEST_DIR/" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Files copied successfully!"
    echo ""
    echo "File count:"
    ls "$DEST_DIR"/podd_*.md 2>/dev/null | wc -l
else
    echo "❌ Error copying files"
    echo "Please check that both directories exist"
fi
