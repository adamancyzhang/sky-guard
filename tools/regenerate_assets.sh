#!/bin/bash
# Regenerate all BGM asset files (Contra-style chiptune .wav)
cd "$(dirname "$0")/.."
python3 tools/generate_assets.py
