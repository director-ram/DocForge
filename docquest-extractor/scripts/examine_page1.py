#!/usr/bin/env python3
import json

with open('data/raw_blocks.json', 'r', encoding='utf-8') as f:
    blocks = json.load(f)

# Get blocks from page 1
page1_blocks = [b for b in blocks if b['page'] == 1][:50]

print(f"First 50 blocks from Page 1:\n")
for i, b in enumerate(page1_blocks):
    text = b['text'].strip()
    if text:
        print(f"{i:3d}) [{b['page']}:{b.get('line_idx',0)}] {text[:100]}")
