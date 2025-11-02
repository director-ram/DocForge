#!/usr/bin/env python3
import json

with open('data/classified_output_FIXED.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total questions: {len(data)}\n")

for i in range(min(5, len(data))):
    q = data[i]
    print(f"Question {i+1}:")
    print(f"  ID: {q['temp_id']}")
    print(f"  Text: {q['question_text'][:80]}...")
    print(f"  Options: {len(q['options'])}")
    if len(q['options']) > 0:
        print(f"  Labels: {[o['label'] for o in q['options']]}")
    print()
