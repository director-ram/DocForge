#!/usr/bin/env python3
"""Quick Analysis of Complete Pipeline Results"""
import json
import fitz

print("=" * 80)
print("📊 COMPLETE PIPELINE ANALYSIS")
print("=" * 80)

# PDF Analysis
pdf = fitz.open('Living Word.pdf')
print(f"\n📄 PDF FILE")
print(f"   Total Pages: {len(pdf)}")
print(f"   Filename: Living Word.pdf")

# Raw Blocks
with open('data/raw_blocks.json', encoding='utf-8') as f:
    raw_blocks = json.load(f)
print(f"\n📝 STEP 1: PDF PARSING (parse_pdf.py)")
print(f"   Raw text blocks extracted: {len(raw_blocks):,}")

# Classified Questions
with open('data/classified_output.json', encoding='utf-8') as f:
    classified = json.load(f)
print(f"\n🔍 STEP 2: CLASSIFICATION (classify_text.py)")
print(f"   Questions classified: {len(classified)}")
print(f"   Average per page: {len(classified)/len(pdf):.1f}")

# AI Answers
with open('data/ai_generated_answers.json', encoding='utf-8') as f:
    ai_answers = json.load(f)
    
print(f"\n🤖 STEP 3: AI ANSWERING (auto_answer_with_ollama.py)")
print(f"   Total questions: {len(classified)}")
print(f"   AI answered: {len(ai_answers)}")
print(f"   Not answered: {len(classified) - len(ai_answers)}")
print(f"   Coverage: {len(ai_answers)/len(classified)*100:.1f}%")

# PDF Generation
answered_pdf = fitz.open('Living_pdf_Answered.pdf')
print(f"\n📄 STEP 4: PDF GENERATION (generate_answered_pdf.py)")
print(f"   Output PDF: Living_pdf_Answered.pdf")
print(f"   Total pages: {len(answered_pdf)}")
print(f"   Questions highlighted: ~{len(ai_answers)}")

# Expected vs Actual
print(f"\n📊 SUMMARY")
print("-" * 80)
print(f"   Expected questions (from user): ~763")
print(f"   Actually found by classifier: {len(classified)}")
print(f"   Missing/Not detected: {763 - len(classified)}")
print(f"   Detection rate: {len(classified)/763*100:.1f}%")
print(f"")
print(f"   AI answering rate: {len(ai_answers)/len(classified)*100:.1f}%")
print(f"   Overall completion: {len(ai_answers)/763*100:.1f}% (of expected)")

# Check structure quality
good_structure = sum(1 for q in classified if len(q.get('options', [])) == 4)
print(f"\n✅ QUALITY CHECK")
print(f"   Questions with 4 options: {good_structure} ({good_structure/len(classified)*100:.1f}%)")
print(f"   Questions with ≠4 options: {len(classified) - good_structure}")

print("\n" + "=" * 80)

pdf.close()
answered_pdf.close()
