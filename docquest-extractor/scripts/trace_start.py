#!/usr/bin/env python3
import json

with open('data/raw_blocks.json', 'r', encoding='utf-8') as f:
    blocks = json.load(f)

# Show first 30 blocks with annotations
print("First 30 blocks from raw data:\n")
for i, b in enumerate(blocks[:30]):
    if b['text'].strip():
        text = b['text'].strip()[:100]
        print(f"{i:3d}) [{b['page']}:{b.get('line_idx',0):3d}] {text}")
        
        # Check if matches question pattern
        import re
        if re.match(r'^\s*\d+\.\s+', text):
            print("      ^^^ NUMBERED QUESTION")
        elif re.match(r'^\s*\([1-4A-Da-d]\)\s*', text):
            print("      ^^^ OPTION")
