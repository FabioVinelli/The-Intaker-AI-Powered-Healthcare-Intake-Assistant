#!/bin/bash

# Prepare Transfer Script (V2)
# Creates a clean zip of the project for AirDrop transfer
# Excludes node_modules, venv, pycache, and .git to keep file size small (~5MB)

ZIP_NAME="The_Intaker_Clean.zip"

echo "🧹 Preparing clean archive for transfer..."

# Remove old zip if it exists
rm -f "$ZIP_NAME"

# Create the zip with strict exclusions
# Note: We use -x to exclude patterns. 
# We need to be careful to match both file paths and directory contents.

zip -r "$ZIP_NAME" . \
  -x "*/node_modules/*" \
  -x "node_modules/*" \
  -x "*/venv/*" \
  -x "venv/*" \
  -x "*/scout_env/*" \
  -x "scout_env/*" \
  -x "*/__pycache__/*" \
  -x "*/.git/*" \
  -x ".git/*" \
  -x "*/.Ds_Store" \
  -x "*.zip" \
  -x "*/build/*" \
  -x "*/dist/*" \
  -x "*/.roomodes/*" \
  -x ".roomodes/*"

echo "✅ Archive created: $ZIP_NAME"
echo "📦 Size: $(du -sh $ZIP_NAME | cut -f1)"
echo "---------------------------------------------------"
echo "👉 Instructions:"
echo "1. Reveal in Finder: open ."
echo "2. AirDrop '$ZIP_NAME' to your MacBook Air M4"
echo "3. Remember to send your .env file separately!"
