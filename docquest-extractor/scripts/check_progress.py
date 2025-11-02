"""
Monitor AI Answer Generation Progress
======================================
Quick script to check how many questions have been answered.
"""

import json
from pathlib import Path

def check_progress():
    answers_file = Path('data/ai_generated_answers.json')
    
    if not answers_file.exists():
        print("❌ No answers file found yet")
        return
    
    try:
        with open(answers_file, 'r', encoding='utf-8') as f:
            answers = json.load(f)
        
        total = 668
        answered = len(answers)
        remaining = total - answered
        percentage = round(answered * 100 / total, 1)
        
        print(f"\n{'='*60}")
        print(f"  📊 AI Answer Generation Progress")
        print(f"{'='*60}")
        print(f"  ✅ Answered:   {answered:3d} / {total}")
        print(f"  ⏳ Remaining:  {remaining:3d}")
        print(f"  📈 Progress:   {percentage}%")
        print(f"{'='*60}")
        
        # Progress bar
        bar_length = 50
        filled = int(bar_length * answered / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"  [{bar}]")
        print(f"{'='*60}\n")
        
        if answered >= total:
            print("  🎉 ALL QUESTIONS ANSWERED! 🎉")
            print(f"\n  Next step: Generate complete PDF:")
            print(f'  python scripts/generate_answered_pdf.py "Living Word.pdf" "Living Word_Complete.pdf" --answers data/ai_generated_answers.json')
        else:
            estimated_time = remaining * 6  # ~6 seconds per question
            hours = estimated_time // 3600
            minutes = (estimated_time % 3600) // 60
            print(f"  ⏱️  Estimated time remaining: {hours}h {minutes}m")
        
        print()
        
    except Exception as e:
        print(f"❌ Error reading answers: {e}")

if __name__ == '__main__':
    check_progress()
