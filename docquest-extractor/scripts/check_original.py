#!/usr/bin/env python3
import json

with open('data/classified_output.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total questions in ORIGINAL: {len(data)}")
q1 = data[0]
print(f"First question ID: {q1.get('temp_id')}")
print(f"First question options: {len(q1.get('options', []))}")
print(f"First 5 option labels: {[o['label'] for o in q1.get('options', [])[5]]}")
