"""
Convert CSV answers to JSON for PDF generation
"""

import csv
import json

def csv_to_json(csv_file: str, json_file: str):
    """Convert answers CSV to simple JSON format."""
    answers = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            temp_id = row['Question_ID']
            answer = row['Correct_Answer'].strip()
            
            if answer and answer != '<FILL_THIS>':
                answers[temp_id] = answer
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(answers, f, indent=2)
    
    print(f"[ok] Converted {len(answers)} answers to {json_file}")


if __name__ == '__main__':
    import sys
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'data/answers_template.csv'
    json_file = sys.argv[2] if len(sys.argv) > 2 else 'data/answers.json'
    
    csv_to_json(csv_file, json_file)
