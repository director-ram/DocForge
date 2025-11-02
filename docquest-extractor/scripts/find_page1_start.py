#!/usr/bin/env python3
import json
import re

with open('data/raw_blocks.json', 'r', encoding='utf-8') as f:
    blocks = json.load(f)

# Find where page 1 starts
print("Searching for first appearance of page 1...\n")
for i, b in enumerate(blocks[:200]):
    if b['page'] == 1:
        print(f"Page 1 starts at index {i}")
        print("\n10 blocks BEFORE page 1:")
        for j in range(max(0, i-10), i):
            text = blocks[j]['text'].strip()
            if text:
                print(f"  [{blocks[j]['page']}:{blocks[j].get('line_idx',0)}] {text[:80]}")
        print("\nFirst 20 blocks OF page 1:")
        for j in range(i, min(i+20, len(blocks))):
            text = blocks[j]['text'].strip()
            if text:
                # Check if matches question pattern
                q_match = re.match(r'^\s*(\d+)\.\s+', text)
                opt_match = re.match(r'^\s*\(([1-4A-Da-d])\)', text)
                marker = ""
                if q_match:
                    marker = f" <-- Q{q_match.group(1)}"
                elif opt_match:
                    marker = f" <-- OPT({opt_match.group(1)})"
                print(f"  [{blocks[j]['page']}:{blocks[j].get('line_idx',0)}] {text[:80]}{marker}")
        break
