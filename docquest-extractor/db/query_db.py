#!/usr/bin/env python3
"""
Quick script to query and verify database contents
"""
import sqlite3
import os
from pathlib import Path


def query_database(db_path):
    """
    Query and display database statistics and sample data
    """
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("=" * 70)
    print("📊 Database Query Results")
    print("=" * 70)
    
    # Document info
    print("\n📄 Documents:")
    cursor = conn.execute("SELECT * FROM documents")
    for row in cursor:
        print(f"   ID: {row['id']}")
        print(f"   Filename: {row['filename']}")
        print(f"   Total Questions: {row['total_questions']}")
        print(f"   Status: {row['status']}")
    
    # Overall stats
    print("\n📊 Overall Statistics:")
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM questions")
    total_questions = cursor.fetchone()['count']
    print(f"   Total Questions: {total_questions}")
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM options")
    total_options = cursor.fetchone()['count']
    print(f"   Total Options: {total_options}")
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM questions WHERE ai_generated_answer IS NOT NULL")
    ai_answered = cursor.fetchone()['count']
    print(f"   AI Answered: {ai_answered} ({ai_answered/total_questions*100:.1f}%)")
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM questions WHERE correct_answer_label IS NOT NULL")
    has_correct = cursor.fetchone()['count']
    print(f"   Has Correct Answer: {has_correct}")
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM questions WHERE ai_answer_matched = 1")
    ai_correct = cursor.fetchone()['count']
    print(f"   AI Correct Matches: {ai_correct}")
    if ai_answered > 0:
        print(f"   AI Accuracy: {ai_correct/ai_answered*100:.1f}%")
    
    # Sample questions
    print("\n📝 Sample Questions (First 3):")
    cursor = conn.execute("""
        SELECT id, question_text, ai_generated_answer, correct_answer_label, ai_answer_matched
        FROM questions
        LIMIT 3
    """)
    
    for i, row in enumerate(cursor, 1):
        print(f"\n   Question {i}: {row['id']}")
        print(f"   Text: {row['question_text'][:80]}...")
        print(f"   AI Answer: {row['ai_generated_answer']}")
        print(f"   Correct Answer: {row['correct_answer_label']}")
        print(f"   Match: {'✅' if row['ai_answer_matched'] else '❌'}")
        
        # Get options for this question
        opt_cursor = conn.execute(
            "SELECT label, text, is_correct, is_ai_answer FROM options WHERE question_id = ?",
            (row['id'],)
        )
        print(f"   Options:")
        for opt in opt_cursor:
            markers = []
            if opt['is_correct']:
                markers.append("✓ Correct")
            if opt['is_ai_answer']:
                markers.append("🤖 AI")
            marker_str = f" [{', '.join(markers)}]" if markers else ""
            print(f"      {opt['label']}) {opt['text'][:50]}...{marker_str}")
    
    conn.close()
    print("\n" + "=" * 70)


def main():
    script_dir = Path(__file__).parent
    db_path = os.getenv("DB_PATH", str(script_dir / "docquest.db"))
    query_database(db_path)


if __name__ == "__main__":
    main()
