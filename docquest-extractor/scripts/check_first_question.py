#!/usr/bin/env python3
import json

with open('data/classified_output_FIXED.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

q1 = data[0]
print(f"Question ID: {q1['temp_id']}")
print(f"Number of options: {len(q1['options'])}")
print(f"\nFirst 10 option labels: {[o['label'] for o in q1['options'][:10]]}")
print(f"\nQuestion text (first 200 chars): {q1['question_text'][:200]}")
