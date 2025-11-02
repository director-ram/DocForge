"""
Complete AI Answer Generation in Batches
=========================================
This script runs the AI answer generation in batches until all questions are answered.
"""

import subprocess
import json
import time
from pathlib import Path

PYTHON_EXE = r"C:\Users\khema\AppData\Local\Programs\Python\Python312\python.exe"
SCRIPT_PATH = r"c:\Users\khema\Desktop\DOC_forge\Hemasai-work\director-ram-DocForge\docquest-extractor\scripts\auto_answer_with_ollama.py"
ANSWERS_FILE = Path("data/ai_generated_answers.json")
TOTAL_QUESTIONS = 668
BATCH_SIZE = 100

def get_progress():
    """Get current number of answered questions."""
    if not ANSWERS_FILE.exists():
        return 0
    try:
        with open(ANSWERS_FILE, 'r', encoding='utf-8') as f:
            answers = json.load(f)
        return len(answers)
    except:
        return 0

def run_batch():
    """Run one batch of AI answer generation."""
    cmd = [
        PYTHON_EXE,
        SCRIPT_PATH,
        "--model", "gemma2:9b",
        "--batch-size", "20",
        "--max", str(BATCH_SIZE)
    ]
    
    print(f"\n[Running] {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, cwd=str(ANSWERS_FILE.parent.parent))
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n[Interrupted] Batch processing stopped")
        return False
    except Exception as e:
        print(f"[Error] {e}")
        return False

def main():
    print("="*70)
    print("  AI Answer Generation - Batch Processing")
    print("="*70)
    print()
    
    batch_num = 1
    
    while True:
        answered = get_progress()
        remaining = TOTAL_QUESTIONS - answered
        percentage = round(answered * 100 / TOTAL_QUESTIONS, 1)
        
        print(f"\n{'='*70}")
        print(f"  Batch #{batch_num}")
        print(f"  Progress: {answered}/{TOTAL_QUESTIONS} ({percentage}%)")
        print(f"  Remaining: {remaining}")
        print(f"{'='*70}")
        
        if answered >= TOTAL_QUESTIONS:
            print("\n🎉 ALL QUESTIONS ANSWERED! 🎉\n")
            print("Generating final PDF...")
            
            pdf_cmd = [
                PYTHON_EXE,
                r"c:\Users\khema\Desktop\DOC_forge\Hemasai-work\director-ram-DocForge\docquest-extractor\scripts\generate_answered_pdf.py",
                "Living Word.pdf",
                "Living Word_Complete_AI.pdf",
                "--answers",
                "data/ai_generated_answers.json"
            ]
            
            subprocess.run(pdf_cmd, cwd=str(ANSWERS_FILE.parent.parent))
            print("\n✅ Done! Check: Living Word_Complete_AI.pdf")
            break
        
        # Run batch
        success = run_batch()
        
        if not success:
            print("\n[Paused] You can resume anytime by running this script again")
            break
        
        batch_num += 1
        print(f"\n[Wait] 5 seconds before next batch...")
        time.sleep(5)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Stopped] You can resume anytime by running this script again")
        print(f"Progress saved in: {ANSWERS_FILE}")
