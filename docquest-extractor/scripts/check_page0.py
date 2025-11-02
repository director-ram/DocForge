#!/usr/bin/env python3
import json

with open('data/raw_blocks.json', 'r', encoding='utf-8') as f:
    blocks = json.load(f)

p0 = [b for b in blocks if b['page'] == 0]
print(f"Page 0 has {len(p0)} blocks\n")
print("Last 15 blocks of Page 0:")
for b in p0[-15:]:
    if b['text'].strip():
        print(f"  {b['text']}")
