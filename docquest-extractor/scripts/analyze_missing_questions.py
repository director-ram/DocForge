"""
Analyze Question Count Discrepancy
===================================
Check why we have 668 classified questions but 763 in PDF
"""

import json
import fitz
import re
from collections import defaultdict

# Load classified questions
with open('data/classified_output_FIXED.json', 'r', encoding='utf-8') as f:
    classified = json.load(f)

print(f"📊 Classified Questions: {len(classified)}")
print(f"📄 Expected in PDF: 763")
print(f"❌ Missing: {763 - len(classified)} questions ({round((763-len(classified))*100/763, 1)}%)\n")

# Analyze by page
questions_per_page = defaultdict(int)
for q in classified:
    temp_id = q.get('temp_id', '')
    if temp_id:
        page = int(temp_id.split('_')[0][1:])  # p1_q1 -> 1
        questions_per_page[page] += 1

print("📋 Questions per page (classified):")
for page in sorted(questions_per_page.keys())[:10]:  # First 10 pages
    print(f"  Page {page}: {questions_per_page[page]} questions")

# Check PDF directly
print("\n🔍 Analyzing PDF directly...")
doc = fitz.open('Living Word.pdf')

total_found = 0
for page_num in range(min(5, len(doc))):  # Check first 5 pages
    page = doc[page_num]
    text = page.get_text("text")
    if not isinstance(text, str):
        text = str(text)
    
    # Count question patterns
    patterns = [
        r'^\d+\.\s+',  # "1. "
        r'^\d+\)\s+',  # "1) "
    ]
    
    questions = 0
    for pattern in patterns:
        questions += len(re.findall(pattern, text, re.MULTILINE))
    
    print(f"  Page {page_num + 1}: ~{questions} question markers found")
    total_found += questions

print(f"\n📈 Estimated total (extrapolated): {total_found * len(doc) // 5} questions")

# Check for issues in classification
print("\n🔎 Checking classification issues...")
issues = []
for q in classified[:20]:  # Check first 20
    options = q.get('options', [])
    if len(options) == 0:
        issues.append(f"  - {q['temp_id']}: No options")
    elif len(options) < 2:
        issues.append(f"  - {q['temp_id']}: Only {len(options)} option")
    elif len(options) > 10:
        issues.append(f"  - {q['temp_id']}: Too many options ({len(options)}) - might be merged questions")

if issues:
    print("⚠️ Found classification issues:")
    for issue in issues[:10]:
        print(issue)
else:
    print("✅ No obvious classification issues in sample")

print("\n💡 Recommendation:")
print("The classifier might be:")
print("1. Missing questions at page boundaries")
print("2. Merging multiple questions into one")
print("3. Skipping questions with unusual formatting")
print("4. Missing questions in the last pages")
print("\nNeed to re-run classifier with adjusted settings!")
