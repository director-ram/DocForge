#!/usr/bin/env python3
"""Quick analysis of classified questions"""
import json

# Load data
with open('data/classified_output.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

print(f"{'='*60}")
print(f"CLASSIFICATION RESULTS SUMMARY")
print(f"{'='*60}\n")

print(f"📊 Total questions extracted: {len(questions)}")

# Confidence analysis
high_conf = [q for q in questions if q.get('confidence', 0) >= 0.75]
medium_conf = [q for q in questions if 0.5 <= q.get('confidence', 0) < 0.75]
low_conf = [q for q in questions if q.get('confidence', 0) < 0.5]

print(f"\n🎯 Confidence Distribution:")
print(f"   High (≥0.75):   {len(high_conf)} ({len(high_conf)/len(questions)*100:.1f}%)")
print(f"   Medium (0.5-0.75): {len(medium_conf)} ({len(medium_conf)/len(questions)*100:.1f}%)")
print(f"   Low (<0.5):     {len(low_conf)} ({len(low_conf)/len(questions)*100:.1f}%)")

# Manual review needed
manual = [q for q in questions if q.get('manual_review')]
print(f"\n⚠️  Needs manual review: {len(manual)} ({len(manual)/len(questions)*100:.1f}%)")

# Question types
types = {}
for q in questions:
    qtype = q.get('question_type_hint', 'unknown')
    types[qtype] = types.get(qtype, 0) + 1

print(f"\n📝 Question Types:")
for qtype, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
    print(f"   {qtype}: {count}")

# Options analysis
with_options = [q for q in questions if len(q.get('options', [])) >= 2]
with_answer = [q for q in questions if q.get('answer_index') is not None]
with_explanation = [q for q in questions if q.get('explanation')]

print(f"\n✅ Completeness:")
print(f"   With options (≥2):   {len(with_options)} ({len(with_options)/len(questions)*100:.1f}%)")
print(f"   With answer:         {len(with_answer)} ({len(with_answer)/len(questions)*100:.1f}%)")
print(f"   With explanation:    {len(with_explanation)} ({len(with_explanation)/len(questions)*100:.1f}%)")

# Sample questions
print(f"\n{'='*60}")
print("SAMPLE QUESTIONS (First 3 High Confidence)")
print(f"{'='*60}\n")

for i, q in enumerate(high_conf[:3], 1):
    print(f"Question {i} (Confidence: {q.get('confidence')})")
    print(f"Pages: {q.get('source', {}).get('pages', [])}")
    print(f"Type: {q.get('question_type_hint')}")
    print(f"Q: {q.get('question_text', 'N/A')[:150]}...")
    
    opts = q.get('options', [])
    if opts:
        print(f"Options: {len(opts)}")
        for opt in opts[:4]:
            prefix = "✓" if opt.get('label') == q.get('answer_label') else " "
            print(f"  {prefix} {opt.get('label')}) {opt.get('text', '')[:80]}")
    
    if q.get('answer_label'):
        print(f"Answer: {q.get('answer_label')}")
    
    if q.get('explanation'):
        print(f"Explanation: {q.get('explanation', '')[:100]}...")
    
    print()

print(f"{'='*60}")
print("✅ Analysis complete! Check the Review Dashboard at http://127.0.0.1:5000")
print(f"{'='*60}")
