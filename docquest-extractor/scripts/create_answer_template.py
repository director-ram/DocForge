"""
Create Answer Template
======================
Creates a simple CSV/JSON file from classified questions for easy answer entry.

Usage:
    python create_answer_template.py [--format csv|json]
"""

import json
import csv
import argparse
from pathlib import Path


def create_csv_template(questions: list, output_file: str):
    """Create CSV template for answer entry."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Question_ID', 'Page', 'Question_Preview', 'Options', 'Correct_Answer'])
        
        for q in questions:
            temp_id = q.get('temp_id', '')
            question_text = q.get('question_text', '')[:80]  # First 80 chars
            options = q.get('options', [])
            
            # Create options string
            option_labels = [opt['label'] for opt in options]
            options_str = ', '.join(option_labels) if option_labels else ''
            
            # Parse page from temp_id
            try:
                page = temp_id.split('_')[0][1:]  # p1_q1 -> 1
            except:
                page = ''
            
            writer.writerow([
                temp_id,
                page,
                question_text,
                options_str,
                ''  # Empty for user to fill
            ])
    
    print(f"[ok] Created CSV template: {output_file}")
    print(f"[info] Fill the 'Correct_Answer' column with option labels (e.g., 1, 2, A, B)")


def create_json_template(questions: list, output_file: str):
    """Create JSON template for answer entry."""
    template = []
    
    for q in questions:
        temp_id = q.get('temp_id', '')
        question_text = q.get('question_text', '')
        options = q.get('options', [])
        
        template.append({
            'temp_id': temp_id,
            'question': question_text,
            'options': [f"{opt['label']}) {opt['text'][:50]}" for opt in options],
            'correct_answer': '<FILL_THIS>'
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"[ok] Created JSON template: {output_file}")
    print(f"[info] Fill 'correct_answer' fields with option labels")


def main():
    parser = argparse.ArgumentParser(description='Create answer template from classified questions')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                       help='Output format (default: csv)')
    parser.add_argument('--input', default='data/classified_output.json',
                       help='Input classified JSON file')
    parser.add_argument('--output', help='Output file path (auto-generated if not provided)')
    
    args = parser.parse_args()
    
    # Load classified questions
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        print(f"[ok] Loaded {len(questions)} questions from {args.input}")
    except FileNotFoundError:
        print(f"[error] File not found: {args.input}")
        return 1
    except json.JSONDecodeError as e:
        print(f"[error] Invalid JSON: {e}")
        return 1
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        output_file = f"data/answers_template.{args.format}"
    
    # Create template
    if args.format == 'csv':
        create_csv_template(questions, output_file)
    else:
        create_json_template(questions, output_file)
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
