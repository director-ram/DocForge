#!/usr/bin/env python3
"""
Script to upload processed questions and AI-generated answers to database

This script:
1. Reads classified questions from classified_output.json
2. Reads AI-generated answers from ai_generated_answers.json
3. Stores everything in a SQLite database with proper schema

Usage:
    python upload_to_db.py
    
Environment Variables:
    CLASSIFIED_JSON - Path to classified questions (default: ../data/classified_output.json)
    AI_ANSWERS_JSON - Path to AI answers (default: ../data/ai_generated_answers.json)
    DB_PATH - Database file path (default: docquest.db)
    DOCUMENT_ID - Document identifier (default: living_word_pdf)
"""
import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime


def create_database_schema(conn):
    """
    Create comprehensive database schema for questions, options, and answers
    """
    # Create documents table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT,
            original_path TEXT,
            total_questions INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create questions table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            question_text TEXT NOT NULL,
            question_type TEXT,
            page_numbers TEXT,
            confidence REAL,
            manual_review INTEGER,
            explanation TEXT,
            correct_answer_label TEXT,
            correct_answer_index INTEGER,
            ai_generated_answer TEXT,
            ai_answer_matched INTEGER,
            document_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    ''')
    
    # Create options table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT NOT NULL,
            label TEXT NOT NULL,
            text TEXT NOT NULL,
            option_index INTEGER,
            is_correct INTEGER DEFAULT 0,
            is_ai_answer INTEGER DEFAULT 0,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    
    # Create indexes for faster queries
    conn.execute('CREATE INDEX IF NOT EXISTS idx_questions_document ON questions(document_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_options_question ON options(question_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_options_correct ON options(is_correct)')
    
    conn.commit()


def upload_document(conn, document_id, filename, total_questions):
    """
    Upload or update document information
    """
    conn.execute(
        '''INSERT OR REPLACE INTO documents 
           (id, filename, total_questions, status, created_at) 
           VALUES (?, ?, ?, ?, ?)''',
        (document_id, filename, total_questions, 'processed', datetime.now())
    )
    conn.commit()


def upload_questions_with_answers(conn, questions, ai_answers, document_id):
    """
    Upload questions with their options and AI-generated answers
    
    Args:
        questions: List of question objects from classified_output.json
        ai_answers: Dict mapping question_id -> answer_label from ai_generated_answers.json
        document_id: Document identifier
    """
    uploaded_count = 0
    matched_count = 0
    
    for question in questions:
        q_id = question.get('temp_id', '')
        if not q_id:
            continue
            
        # Get AI answer for this question
        ai_answer = ai_answers.get(q_id, None)
        
        # Check if AI answer matches correct answer
        correct_label = question.get('answer_label', None)
        ai_matched = 1 if (ai_answer and correct_label and ai_answer == correct_label) else 0
        
        # Convert page numbers to string
        pages = question.get('source', {}).get('pages', [])
        page_str = ','.join(map(str, pages)) if pages else ''
        
        # Insert question
        conn.execute(
            '''INSERT OR REPLACE INTO questions 
               (id, question_text, question_type, page_numbers, confidence, 
                manual_review, explanation, correct_answer_label, correct_answer_index,
                ai_generated_answer, ai_answer_matched, document_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                q_id,
                question.get('question_text', ''),
                question.get('question_type_hint', 'single_correct'),
                page_str,
                question.get('confidence', 0.0),
                1 if question.get('manual_review', False) else 0,
                question.get('explanation', ''),
                correct_label,
                question.get('answer_index', None),
                ai_answer,
                ai_matched,
                document_id
            )
        )
        
        # Insert options
        options = question.get('options', [])
        for idx, option in enumerate(options):
            label = option.get('label', '')
            text = option.get('text', '')
            
            # Mark if this is the correct answer
            is_correct = 1 if (correct_label and label == correct_label) else 0
            
            # Mark if this is the AI's answer
            is_ai_answer = 1 if (ai_answer and label == ai_answer) else 0
            
            conn.execute(
                '''INSERT INTO options 
                   (question_id, label, text, option_index, is_correct, is_ai_answer)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (q_id, label, text, idx, is_correct, is_ai_answer)
            )
        
        uploaded_count += 1
        if ai_matched:
            matched_count += 1
    
    conn.commit()
    return uploaded_count, matched_count


def get_statistics(conn):
    """
    Get database statistics
    """
    stats = {}
    
    # Total questions
    cursor = conn.execute('SELECT COUNT(*) FROM questions')
    stats['total_questions'] = cursor.fetchone()[0]
    
    # Questions with AI answers
    cursor = conn.execute('SELECT COUNT(*) FROM questions WHERE ai_generated_answer IS NOT NULL')
    stats['ai_answered'] = cursor.fetchone()[0]
    
    # Correct AI answers
    cursor = conn.execute('SELECT COUNT(*) FROM questions WHERE ai_answer_matched = 1')
    stats['ai_correct'] = cursor.fetchone()[0]
    
    # Questions with correct answers
    cursor = conn.execute('SELECT COUNT(*) FROM questions WHERE correct_answer_label IS NOT NULL')
    stats['has_correct_answer'] = cursor.fetchone()[0]
    
    # Total options
    cursor = conn.execute('SELECT COUNT(*) FROM options')
    stats['total_options'] = cursor.fetchone()[0]
    
    return stats


def main():
    """
    Main function to upload questions and answers to database
    """
    # Get paths from environment or use defaults
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data'
    
    classified_json = os.getenv("CLASSIFIED_JSON", str(data_dir / "classified_output.json"))
    ai_answers_json = os.getenv("AI_ANSWERS_JSON", str(data_dir / "ai_generated_answers.json"))
    db_path = os.getenv("DB_PATH", str(script_dir / "docquest.db"))
    document_id = os.getenv("DOCUMENT_ID", "living_word_pdf")
    
    print("=" * 60)
    print("DocQuest Database Upload")
    print("=" * 60)
    print(f"Classified JSON: {classified_json}")
    print(f"AI Answers JSON: {ai_answers_json}")
    print(f"Database: {db_path}")
    print(f"Document ID: {document_id}")
    print()
    
    # Check if classified questions file exists
    if not os.path.exists(classified_json):
        print(f"❌ Error: Classified questions file not found: {classified_json}")
        print("\n💡 Tip: Run classify_text.py first to generate classified_output.json")
        return 1
    
    # Load classified questions
    print(f"📖 Loading classified questions...")
    with open(classified_json, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    print(f"✅ Loaded {len(questions)} questions")
    
    # Load AI answers if available
    ai_answers = {}
    if os.path.exists(ai_answers_json):
        print(f"🤖 Loading AI-generated answers...")
        with open(ai_answers_json, 'r', encoding='utf-8') as f:
            ai_answers = json.load(f)
        print(f"✅ Loaded {len(ai_answers)} AI answers")
    else:
        print(f"⚠️  Warning: AI answers file not found: {ai_answers_json}")
        print(f"   Questions will be uploaded without AI answers")
    
    # Connect to database
    print(f"\n💾 Connecting to database...")
    conn = sqlite3.connect(db_path)
    
    # Create schema
    print(f"🏗️  Creating database schema...")
    create_database_schema(conn)
    
    # Upload document
    print(f"📄 Uploading document information...")
    upload_document(conn, document_id, "Living Word.pdf", len(questions))
    
    # Upload questions and answers
    print(f"📝 Uploading questions with answers...")
    uploaded, matched = upload_questions_with_answers(conn, questions, ai_answers, document_id)
    
    # Get statistics
    stats = get_statistics(conn)
    
    # Close connection
    conn.close()
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ Upload Complete!")
    print("=" * 60)
    print(f"📊 Database Statistics:")
    print(f"   Total Questions: {stats['total_questions']}")
    print(f"   Total Options: {stats['total_options']}")
    print(f"   Questions with Correct Answers: {stats['has_correct_answer']}")
    print(f"   AI Answered: {stats['ai_answered']}")
    print(f"   AI Correct Matches: {stats['ai_correct']}")
    if stats['ai_answered'] > 0:
        accuracy = (stats['ai_correct'] / stats['ai_answered']) * 100
        print(f"   AI Accuracy: {accuracy:.1f}%")
    print(f"\n💾 Database: {db_path}")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())