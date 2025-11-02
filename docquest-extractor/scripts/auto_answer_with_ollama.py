"""
Automatic Answer Generation using Ollama
=========================================
This script uses local Ollama models to automatically answer multiple-choice questions.

Usage:
    python auto_answer_with_ollama.py [--model gemma2:9b] [--batch-size 10] [--output answers.json]
"""

import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import re


def check_ollama_available() -> bool:
    """Check if Ollama is installed and running."""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[error] Ollama not available: {e}")
        return False


def get_available_models() -> List[str]:
    """Get list of available Ollama models."""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        models = []
        for line in result.stdout.strip().split('\n')[1:]:  # Skip header
            parts = line.split()
            if parts:
                models.append(parts[0])
        
        return models
    except Exception as e:
        print(f"[error] Failed to get models: {e}")
        return []


def format_question_prompt(question_data: Dict[str, Any]) -> str:
    """
    Format a question for the AI model with improved prompt engineering.
    """
    question_text = question_data.get('question_text', '')
    options = question_data.get('options', [])
    question_type = question_data.get('question_type_hint', 'single_correct')
    
    # Build options text
    options_text = ""
    for opt in options:
        label = opt.get('label', '')
        text = opt.get('text', '')
        options_text += f"{label}. {text}\n"
    
    # Create prompt based on question type
    if question_type == 'multiple_correct':
        instruction = "This question may have MULTIPLE correct answers. Respond with all correct option labels separated by commas (e.g., '1,3' or 'A,C')."
    elif question_type == 'assertion_reason':
        instruction = "This is an assertion-reason question. Evaluate both statements and select the correct option."
    else:
        instruction = "Select the single best answer from the options provided."
    
    prompt = f"""You are a Biology expert. Answer this multiple-choice question accurately.

Question: {question_text}

Options:
{options_text}

Instructions:
{instruction}

CRITICAL: Respond with ONLY the option label (e.g., '1' or 'A' or 'B'). 
- Do NOT write explanations
- Do NOT write "The answer is..."
- Do NOT write full sentences
- ONLY write the option label

Your answer (label only):"""
    
    return prompt


def ask_ollama(model: str, prompt: str, timeout: int = 30, retry: int = 0) -> Optional[str]:
    """
    Ask Ollama model a question and get response with retry logic.
    """
    max_retries = 2
    
    for attempt in range(max_retries + 1):
        try:
            # Use ollama run with prompt
            result = subprocess.run(
                ['ollama', 'run', model],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                return response
            else:
                print(f"[warn] Ollama error: {result.stderr}")
                if attempt < max_retries:
                    print(f"  [retry {attempt+1}/{max_retries}]")
                    continue
                return None
                
        except subprocess.TimeoutExpired:
            print(f"[warn] Timeout waiting for model response")
            if attempt < max_retries:
                print(f"  [retry {attempt+1}/{max_retries}] Increasing timeout...")
                timeout = timeout + 30  # Increase timeout for retry
                continue
            return None
        except Exception as e:
            print(f"[warn] Error calling Ollama: {e}")
            if attempt < max_retries:
                print(f"  [retry {attempt+1}/{max_retries}]")
                continue
            return None
    
    return None


def extract_answer_label(response: str, available_labels: List[str]) -> Optional[str]:
    """
    Extract answer label from model response.
    Handles formats like "1", "A", "The answer is 1", "Option 1", etc.
    Enhanced with better pattern matching and error handling.
    """
    if not response:
        return None
    
    # Clean response
    response = response.strip()
    response_upper = response.upper()
    
    # Strategy 1: Exact match (case-insensitive)
    for label in available_labels:
        label_upper = label.upper()
        # Direct match
        if response_upper == label_upper:
            return label
        # Match with parentheses: (1) or (A)
        if response_upper == f"({label_upper})":
            return label
        # Match with brackets: [1] or [A]
        if response_upper == f"[{label_upper}]":
            return label
        # Match at start of response
        if response_upper.startswith(label_upper + " ") or response_upper.startswith(label_upper + "."):
            return label
        if response_upper.startswith(label_upper + ")") or response_upper.startswith(label_upper + ":"):
            return label
    
    # Strategy 2: Enhanced regex patterns
    patterns = [
        r'^([A-Z0-9]+)[\s\.\)\]\-:]',  # "A " or "1. " or "A) " or "A]" or "A:"
        r'answer\s+is\s+([A-Z0-9]+)',  # "answer is 1"
        r'correct\s+answer\s+is\s+([A-Z0-9]+)',  # "correct answer is 1"
        r'option\s+([A-Z0-9]+)',  # "option A"
        r'choice\s+([A-Z0-9]+)',  # "choice A"
        r'\(([A-Z0-9]+)\)',  # "(1)" or "(A)"
        r'\[([A-Z0-9]+)\]',  # "[1]" or "[A]"
        r'^([A-Z0-9]+)$',  # Just "1" or "A"
        r'select\s+([A-Z0-9]+)',  # "select 1"
        r'^([A-Z0-9]+)\s*[-–—]',  # "1 -" or "A –"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response_upper, re.IGNORECASE)
        if match:
            extracted = match.group(1).upper()
            # Check if extracted label is in available labels
            for label in available_labels:
                if label.upper() == extracted:
                    return label
    
    # Strategy 3: Handle multiple answers (take first valid one)
    # e.g., "2,3" or "A and B" - take the first
    for label in available_labels:
        label_upper = label.upper()
        # Check if label appears first in comma-separated or "and"-separated list
        if re.search(rf'\b{re.escape(label_upper)}\b', response_upper):
            return label
    
    # Strategy 4: Try to find any available label anywhere in response
    for label in available_labels:
        if label.upper() in response_upper:
            return label
    
    # Strategy 5: Handle Roman numerals if present
    roman_map = {'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5'}
    for roman, digit in roman_map.items():
        if roman in response_upper and digit in [l.upper() for l in available_labels]:
            for label in available_labels:
                if label.upper() == digit:
                    return label
    
    return None


def generate_answers(
    classified_file: str,
    model: str = 'gemma2:9b',
    batch_size: int = 10,
    output_file: str = 'data/ai_generated_answers.json',
    start_from: int = 0,
    max_questions: Optional[int] = None
) -> Dict[str, str]:
    """
    Generate answers for all questions using Ollama model.
    """
    # Load questions
    try:
        with open(classified_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        print(f"[ok] Loaded {len(questions)} questions from {classified_file}")
    except Exception as e:
        print(f"[error] Failed to load questions: {e}")
        return {}
    
    # Check if Ollama is available
    if not check_ollama_available():
        print("[error] Ollama is not running. Please start Ollama first.")
        return {}
    
    # Check if model is available
    available_models = get_available_models()
    if model not in available_models:
        print(f"[error] Model '{model}' not found.")
        print(f"[info] Available models: {', '.join(available_models)}")
        return {}
    
    print(f"[ok] Using model: {model}")
    
    # Load existing answers if output file exists
    answers = {}
    if Path(output_file).exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                answers = json.load(f)
            print(f"[ok] Loaded {len(answers)} existing answers")
        except:
            pass
    
    # Filter questions to process
    questions_to_process = questions[start_from:]
    if max_questions:
        questions_to_process = questions_to_process[:max_questions]
    
    print(f"[info] Processing {len(questions_to_process)} questions (starting from {start_from})")
    
    # Process questions
    success_count = 0
    fail_count = 0
    
    for i, question in enumerate(questions_to_process, start=start_from + 1):
        temp_id = question.get('temp_id', '')
        
        # Skip if already answered
        if temp_id in answers:
            print(f"[{i}/{len(questions)}] Skipping {temp_id} (already answered)")
            success_count += 1
            continue
        
        question_text = question.get('question_text', '')[:60]
        options = question.get('options', [])
        
        if not options:
            print(f"[{i}/{len(questions)}] Skipping {temp_id} (no options)")
            fail_count += 1
            continue
        
        # Skip questions with too many options (likely merged questions)
        if len(options) > 6:
            print(f"[{i}/{len(questions)}] Skipping {temp_id} (too many options: {len(options)}, likely merged)")
            fail_count += 1
            continue
        
        print(f"[{i}/{len(questions)}] Processing {temp_id}: {question_text}...")
        
        # Create prompt
        prompt = format_question_prompt(question)
        
        # Get answer from model
        response = ask_ollama(model, prompt, timeout=45)
        
        if response:
            # Extract answer label
            available_labels = [opt['label'] for opt in options]
            answer_label = extract_answer_label(response, available_labels)
            
            if answer_label:
                answers[temp_id] = answer_label
                success_count += 1
                print(f"  ✓ Answer: {answer_label}")
            else:
                fail_count += 1
                print(f"  ✗ Could not extract answer from: {response[:100]}")
        else:
            fail_count += 1
            print(f"  ✗ No response from model")
        
        # Save progress after each batch
        if i % batch_size == 0:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(answers, f, indent=2)
            print(f"[save] Progress saved: {len(answers)} answers")
    
    # Final save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(answers, f, indent=2)
    
    print(f"\n[done] Generated {success_count} answers, {fail_count} failed")
    print(f"[ok] Saved to: {output_file}")
    
    return answers


def main():
    parser = argparse.ArgumentParser(
        description='Generate answers using Ollama AI models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all answers with default model (gemma2:9b)
  python auto_answer_with_ollama.py
  
  # Use a different model
  python auto_answer_with_ollama.py --model mistral:latest
  
  # Process first 50 questions only
  python auto_answer_with_ollama.py --max 50
  
  # Resume from question 100
  python auto_answer_with_ollama.py --start-from 100
  
  # List available models
  python auto_answer_with_ollama.py --list-models
        """
    )
    
    parser.add_argument('--input', default='data/classified_output.json',
                       help='Input classified questions JSON')
    parser.add_argument('--model', default='gemma2:9b',
                       help='Ollama model to use (default: gemma2:9b)')
    parser.add_argument('--output', default='data/ai_generated_answers.json',
                       help='Output answers JSON file')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Save progress every N questions (default: 10)')
    parser.add_argument('--start-from', type=int, default=0,
                       help='Start from question N (for resuming)')
    parser.add_argument('--max', type=int, dest='max_questions',
                       help='Maximum number of questions to process')
    parser.add_argument('--list-models', action='store_true',
                       help='List available Ollama models and exit')
    
    args = parser.parse_args()
    
    # List models if requested
    if args.list_models:
        models = get_available_models()
        print("Available Ollama models:")
        for model in models:
            print(f"  - {model}")
        return 0
    
    # Check input file
    if not Path(args.input).exists():
        print(f"[error] Input file not found: {args.input}")
        return 1
    
    # Generate answers
    answers = generate_answers(
        args.input,
        model=args.model,
        batch_size=args.batch_size,
        output_file=args.output,
        start_from=args.start_from,
        max_questions=args.max_questions
    )
    
    if answers:
        print(f"\n[success] Generated {len(answers)} answers!")
        print(f"\nNext step: Generate PDF with answers:")
        print(f'  python scripts/generate_answered_pdf.py "Living Word.pdf" "Living Word_AI_Answered.pdf" --answers {args.output}')
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
