"""
Generate PDF with Correct Answers
==================================
This script creates a new PDF with questions and highlights the correct answers.
It maintains the original question and option order from the input.

Usage:
    python generate_answered_pdf.py input.pdf output.pdf [--answers answers.json]
"""

import fitz  # PyMuPDF
import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any

# Color schemes for answer highlighting
CORRECT_ANSWER_COLOR = (0.2, 0.8, 0.2)  # Green
HIGHLIGHT_OPACITY = 0.3


def load_answers(answers_file: str) -> Dict[str, Any]:
    """Load answer mapping from JSON file."""
    try:
        with open(answers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[ok] Loaded answers from {answers_file}")
        return data
    except FileNotFoundError:
        print(f"[warn] Answers file not found: {answers_file}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[error] Invalid JSON in {answers_file}: {e}")
        return {}


def parse_classified_output(classified_file: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse classified_output.json to extract question-answer mapping.
    Returns dict with temp_id as key and answer info as value.
    """
    try:
        with open(classified_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        answer_map = {}
        for q in questions:
            temp_id = q.get('temp_id', '')
            answer_index = q.get('answer_index')
            answer_label = q.get('answer_label', '')
            
            # Only include if we have a valid answer
            if answer_index is not None and answer_index >= 0:
                answer_map[temp_id] = {
                    'answer_index': answer_index,
                    'answer_label': answer_label,
                    'question_text': q.get('question_text', ''),
                    'options': q.get('options', [])
                }
        
        print(f"[ok] Loaded {len(answer_map)} questions with answers from {classified_file}")
        return answer_map
    except Exception as e:
        print(f"[error] Failed to parse classified output: {e}")
        return {}


def create_simple_answer_json(questions: List[Dict[str, Any]], output_file: str):
    """
    Create a simple JSON file for manual answer entry.
    Format: {"p1_q1": "1", "p1_q2": "3", ...}
    """
    answer_template = {}
    for q in questions:
        temp_id = q.get('temp_id', '')
        if temp_id:
            # Get first option label as example
            options = q.get('options', [])
            example = options[0]['label'] if options else "1"
            answer_template[temp_id] = f"<ENTER_ANSWER_LABEL_HERE (e.g., {example})>"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(answer_template, f, indent=2)
    
    print(f"[ok] Created answer template: {output_file}")
    print(f"[info] Please edit this file and replace placeholders with correct answer labels")


def normalize_text(text: str) -> str:
    """Normalize text for better matching."""
    import re
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special quotes
    text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
    # Remove zero-width spaces and other invisible characters
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e\ufeff]', '', text)
    return text.strip()


def highlight_text_in_pdf(page: fitz.Page, search_text: str, color: tuple, opacity: float = 0.3):
    """
    Search for text in page and highlight it with specified color.
    Tries multiple search strategies for better matching.
    """
    # Strategy 1: Exact match
    text_instances = page.search_for(search_text)
    
    if not text_instances:
        # Strategy 2: Normalized match
        normalized = normalize_text(search_text)
        text_instances = page.search_for(normalized)
    
    if not text_instances:
        # Strategy 3: Case-insensitive match (PyMuPDF doesn't support directly, so try variations)
        text_instances = page.search_for(search_text.lower())
        if not text_instances:
            text_instances = page.search_for(search_text.upper())
    
    if not text_instances:
        # Strategy 4: Partial match with first few words
        words = search_text.split()
        if len(words) > 3:
            partial = ' '.join(words[:3])
            text_instances = page.search_for(partial)
    
    if not text_instances:
        # Strategy 5: Try just the first substantial word (>3 chars)
        words = [w for w in search_text.split() if len(w) > 3]
        if words:
            text_instances = page.search_for(words[0])
    
    # Highlight all instances
    for inst in text_instances:
        highlight = page.add_highlight_annot(inst)
        highlight.set_colors(stroke=color)
        highlight.set_opacity(opacity)
        highlight.update()
    
    return len(text_instances) > 0


def add_answer_marker(page: fitz.Page, option_text: str, label: str, page_height: float):
    """
    Add a visual marker (checkmark or highlighting) for the correct answer.
    Tries multiple search patterns for better coverage.
    """
    # Normalize option text
    option_text_clean = normalize_text(option_text)
    
    # Try many different patterns
    search_patterns = [
        # With parentheses
        f"({label}) {option_text}",
        f"({label}){option_text}",
        f"({label})  {option_text}",  # Double space
        f"( {label} ) {option_text}",
        f"({label}) {option_text_clean}",
        
        # With period
        f"{label}. {option_text}",
        f"{label}.{option_text}",
        f"{label}.  {option_text}",  # Double space
        f"{label}. {option_text_clean}",
        
        # With colon
        f"{label}: {option_text}",
        f"{label}:{option_text}",
        
        # With dash
        f"{label} - {option_text}",
        f"{label}- {option_text}",
        f"{label} -{option_text}",
        
        # Just label and text (no punctuation)
        f"{label} {option_text}",
        f"{label}  {option_text}",
        f"{label} {option_text_clean}",
        
        # Just the option text (first 80 chars)
        option_text[:80] if len(option_text) > 80 else option_text,
        option_text_clean[:80] if len(option_text_clean) > 80 else option_text_clean,
        
        # First 50 chars
        option_text[:50] if len(option_text) > 50 else option_text,
        
        # First 30 chars (more aggressive)
        option_text[:30] if len(option_text) > 30 else option_text,
    ]
    
    highlighted = False
    for pattern in search_patterns:
        if highlight_text_in_pdf(page, pattern, CORRECT_ANSWER_COLOR, HIGHLIGHT_OPACITY):
            highlighted = True
            break
    
    return highlighted


def generate_answered_pdf(
    input_pdf: str,
    output_pdf: str,
    answer_source: Optional[str] = None,
    use_classified: bool = True
):
    """
    Generate a new PDF with correct answers highlighted.
    
    Args:
        input_pdf: Path to original PDF
        output_pdf: Path to output PDF with answers
        answer_source: Path to answers JSON file (optional)
        use_classified: Use classified_output.json for answers
    """
    # Load the PDF
    try:
        doc = fitz.open(input_pdf)
        print(f"[ok] Opened PDF: {input_pdf} ({len(doc)} pages)")
    except Exception as e:
        print(f"[error] Failed to open PDF: {e}")
        return False
    
    # Load answers
    answer_map = {}
    
    if use_classified:
        classified_file = Path(input_pdf).parent / '../data/classified_output.json'
        if classified_file.exists():
            classified_data = parse_classified_output(str(classified_file))
            
            # If no answers in classified data, create template for manual entry
            if not classified_data:
                print("[warn] No answers found in classified_output.json")
                template_file = Path(input_pdf).parent / '../data/answers_template.json'
                
                # Load questions to create template
                with open(str(classified_file), 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                create_simple_answer_json(questions, str(template_file))
                print(f"[info] Please fill in {template_file} and run again with --answers flag")
                doc.close()
                return False
            
            answer_map = classified_data
    
    if answer_source:
        # Load manual answers (simple format: {"temp_id": "label"})
        manual_answers = load_answers(answer_source)
        
        # Always load classified data to get question structure
        classified_file = Path(input_pdf).parent / 'data/classified_output.json'
        if not classified_file.exists():
            # Try alternative path
            classified_file = Path('data/classified_output.json')
        
        if classified_file.exists():
            with open(str(classified_file), 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            # Update answer_map with manual answers
            for q in questions:
                temp_id = q.get('temp_id', '')
                if temp_id in manual_answers:
                    answer_label = str(manual_answers[temp_id])
                    
                    # Find option index for this label
                    options = q.get('options', [])
                    answer_index = -1
                    for i, opt in enumerate(options):
                        if opt['label'] == answer_label:
                            answer_index = i
                            break
                    
                    if answer_index >= 0:
                        answer_map[temp_id] = {
                            'answer_index': answer_index,
                            'answer_label': answer_label,
                            'question_text': q.get('question_text', ''),
                            'options': options
                        }
        else:
            print(f"[error] Could not find classified_output.json")
            doc.close()
            return False
    
    if not answer_map:
        print("[error] No answers available. Please provide answers via --answers or ensure classified_output.json has answers.")
        doc.close()
        return False
    
    print(f"[ok] Processing {len(answer_map)} questions with answers")
    
    # Track statistics
    highlighted_count = 0
    failed_count = 0
    
    # Process each question
    for temp_id, answer_info in answer_map.items():
        # Parse page number from temp_id (e.g., "p1_q1" -> page 0)
        try:
            page_num = int(temp_id.split('_')[0][1:]) - 1  # p1 -> 0
        except:
            print(f"[warn] Invalid temp_id format: {temp_id}")
            continue
        
        if page_num < 0 or page_num >= len(doc):
            continue
        
        page = doc[page_num]
        page_height = page.rect.height
        
        answer_index = answer_info['answer_index']
        options = answer_info['options']
        
        if answer_index >= 0 and answer_index < len(options):
            option = options[answer_index]
            option_text = option['text']
            option_label = option['label']
            
            # Highlight the correct answer
            if add_answer_marker(page, option_text, option_label, page_height):
                highlighted_count += 1
            else:
                failed_count += 1
                print(f"[warn] Could not highlight answer for {temp_id}: {option_label}")
    
    # Save the modified PDF
    try:
        doc.save(output_pdf, garbage=4, deflate=True, clean=True)
        print(f"[ok] Generated answered PDF: {output_pdf}")
        print(f"[stats] Highlighted: {highlighted_count}, Failed: {failed_count}")
        doc.close()
        return True
    except Exception as e:
        print(f"[error] Failed to save PDF: {e}")
        doc.close()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Generate PDF with correct answers highlighted',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use answers from classified_output.json
  python generate_answered_pdf.py "Living Word.pdf" "Living Word_Answered.pdf"
  
  # Use manual answers file
  python generate_answered_pdf.py "Living Word.pdf" "output.pdf" --answers answers.json
  
  # Generate answer template for manual entry
  python generate_answered_pdf.py "Living Word.pdf" "output.pdf" --create-template
        """
    )
    
    parser.add_argument('input_pdf', help='Input PDF file path')
    parser.add_argument('output_pdf', help='Output PDF file path with answers')
    parser.add_argument('--answers', help='JSON file with manual answers (format: {"temp_id": "label"})')
    parser.add_argument('--no-classified', action='store_true', 
                       help='Do not use classified_output.json for answers')
    parser.add_argument('--create-template', action='store_true',
                       help='Create answer template JSON for manual entry')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_pdf).exists():
        print(f"[error] Input PDF not found: {args.input_pdf}")
        return 1
    
    # Generate answered PDF
    success = generate_answered_pdf(
        args.input_pdf,
        args.output_pdf,
        answer_source=args.answers,
        use_classified=not args.no_classified
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
