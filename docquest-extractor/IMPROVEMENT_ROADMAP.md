# 🎯 Roadmap to 95% Accuracy

## Current Status vs Target

| Stage | Current | Target | Gap |
|-------|---------|--------|-----|
| PDF Parsing | 100% | 100% | ✅ None |
| Classification | 97.5% | 99% | 1.5% |
| AI Answering | 83.7% | 95% | 11.3% |
| PDF Highlighting | ~98% | 99% | 1% |
| **Overall** | **79.9%** | **95%** | **15.1%** |

---

## 🔧 IMPROVEMENT STRATEGIES

### 1️⃣ IMPROVE CLASSIFICATION (97.5% → 99%)

#### Current Issues:
- Missing 19 questions (2.5%)
- 106 questions have ≠4 options (14.2%)
- Page boundary issues
- Orphaned options

#### Solutions:

**A. Enhance Question Detection**
```python
# Add to classify_text.py

# Better question detection patterns
Q_START_RE = re.compile(
    r'^'
    r'(?P<num>\d{1,3})'  # Question number
    r'[\.\):\-]\s*'       # Separator
    r'(?P<text>.{10,})'   # Substantial text (min 10 chars)
    r'(?:\?|\.{3}|:)$'    # Question markers
)

# Add assertion-reason detection
ASSERTION_RE = re.compile(
    r'Assertion\s*[:\(].*?Reason\s*[:\(]',
    re.IGNORECASE | re.DOTALL
)

# Add integer-type question detection
INTEGER_TYPE_RE = re.compile(
    r'(?:integer|numerical|calculate|value)',
    re.IGNORECASE
)
```

**B. Handle Edge Cases**
```python
# Add context-aware option stitching
def stitch_cross_page_questions(blocks):
    """Stitch questions that span multiple pages"""
    for i in range(len(blocks) - 1):
        current = blocks[i]
        next_block = blocks[i + 1]
        
        # Check if question continues on next page
        if (current['page'] + 1 == next_block['page'] and
            current['content'].endswith('...') or
            not current['content'].endswith('?')):
            # Merge blocks
            pass
```

**C. Validate Question Structure**
```python
def validate_question_structure(question):
    """Ensure each question has proper structure"""
    issues = []
    
    # Check for question text
    if not question.get('question_text'):
        issues.append('Missing question text')
    
    # Check option count
    options = question.get('options', [])
    if len(options) < 2:
        issues.append(f'Too few options: {len(options)}')
    elif len(options) > 10:
        issues.append(f'Too many options (likely merged): {len(options)}')
    
    # Check option labels are sequential
    labels = [opt['label'] for opt in options]
    # Should be 1,2,3,4 or A,B,C,D
    
    return len(issues) == 0, issues
```

---

### 2️⃣ IMPROVE AI ANSWERING (83.7% → 95%)

#### Current Issues:
- 121 questions unanswered (16.3%)
- Model timeouts
- Cloud model connectivity issues
- Complex question formatting

#### Solutions:

**A. Use Better Model Configuration**
```bash
# Option 1: Use reliable local model with better prompting
ollama pull qwen2.5:14b
ollama pull llama3.1:70b  # If you have GPU

# Option 2: Use multiple models for consensus
# Run with 2-3 different models and use voting
```

**B. Enhanced Prompting Strategy**
```python
# Update auto_answer_with_ollama.py

def format_question_prompt_v2(question_text, options):
    """Enhanced prompt with better structure"""
    
    # Analyze question type
    is_assertion = 'assertion' in question_text.lower() and 'reason' in question_text.lower()
    is_match = 'match' in question_text.lower() or 'column' in question_text.lower()
    is_multiple = 'select all' in question_text.lower() or 'choose correct' in question_text.lower()
    
    # Build context-aware prompt
    prompt = f"""You are an expert in biology. Answer this multiple choice question.

Question Type: {'Assertion-Reason' if is_assertion else 'Matching' if is_match else 'Single Correct'}

Question: {question_text}

Options:
"""
    
    for opt in options:
        prompt += f"{opt['label']}) {opt['text']}\n"
    
    prompt += """
CRITICAL INSTRUCTIONS:
1. Read the question VERY carefully
2. Analyze each option thoroughly
3. Choose the MOST correct answer
4. Respond with ONLY the option label (1, 2, 3, 4 or A, B, C, D)
5. No explanation, no punctuation, just the label

Your answer (label only):"""
    
    return prompt
```

**C. Implement Retry Logic with Fallback**
```python
def ask_ollama_with_retry(model, prompt, max_retries=3, timeout=60):
    """Try multiple times with increasing timeout"""
    
    models_fallback = [
        model,                    # Primary model
        'gemma2:9b',             # Fast fallback
        'phi4:14b',              # Accurate fallback
        'mistral:latest'         # Another option
    ]
    
    for retry_model in models_fallback:
        for attempt in range(max_retries):
            try:
                current_timeout = timeout * (attempt + 1)
                response = ask_ollama(retry_model, prompt, timeout=current_timeout)
                
                if response:
                    return response
                    
            except TimeoutError:
                print(f"  [retry {attempt+1}] Timeout with {retry_model}, trying again...")
                continue
            except Exception as e:
                print(f"  [retry {attempt+1}] Error: {e}")
                continue
        
        print(f"  [fallback] Switching to {models_fallback[models_fallback.index(retry_model)+1]}...")
    
    return None
```

**D. Parallel Processing with Rate Limiting**
```python
import concurrent.futures
from time import sleep
import threading

def answer_questions_parallel(questions, model, max_workers=3):
    """Process multiple questions in parallel with rate limiting"""
    
    answers = {}
    rate_limiter = threading.Semaphore(max_workers)
    
    def process_question(q):
        with rate_limiter:
            temp_id = q['temp_id']
            prompt = format_question_prompt_v2(q['question_text'], q['options'])
            
            answer = ask_ollama_with_retry(model, prompt)
            sleep(1)  # Rate limit
            
            return temp_id, answer
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_question, q) for q in questions]
        
        for future in concurrent.futures.as_completed(futures):
            temp_id, answer = future.result()
            if answer:
                answers[temp_id] = answer
    
    return answers
```

**E. Handle Special Question Types**
```python
def extract_answer_label_enhanced(response, options, question_text):
    """Enhanced extraction with special case handling"""
    
    # Check for assertion-reason questions
    if 'assertion' in question_text.lower() and 'reason' in question_text.lower():
        # These typically have complex option patterns
        # A) Both assertion and reason are true...
        # Look for option letter at start
        pass
    
    # Check for integer-type questions
    if 'integer' in question_text.lower():
        # Extract numeric answer
        numbers = re.findall(r'\b\d+\b', response)
        if numbers:
            return numbers[0]
    
    # Check for matching questions
    if 'match' in question_text.lower():
        # Extract option letter (A, B, C, D)
        pass
    
    # Standard extraction (existing logic)
    return extract_answer_label(response, options)
```

---

### 3️⃣ IMPROVE PDF HIGHLIGHTING (98% → 99%)

#### Current Issues:
- ~13 highlights fail (2%)
- Text matching problems
- Special characters
- Multi-line options

#### Solutions:

**A. Enhanced Text Normalization**
```python
def normalize_text_advanced(text):
    """Advanced text normalization for better matching"""
    import unicodedata
    
    # Remove unicode variations
    text = unicodedata.normalize('NFKD', text)
    
    # Replace special spaces
    text = text.replace('\xa0', ' ')  # Non-breaking space
    text = text.replace('\u2009', ' ')  # Thin space
    text = text.replace('\u200b', '')  # Zero-width space
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # Normalize dashes
    text = text.replace('–', '-').replace('—', '-')
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text
```

**B. Fuzzy Text Matching**
```python
from difflib import SequenceMatcher

def fuzzy_search_in_pdf(page, search_text, threshold=0.85):
    """Search for text with fuzzy matching"""
    
    page_text = page.get_text("text")
    words = page_text.split()
    
    search_words = search_text.split()
    best_match = None
    best_ratio = 0
    
    # Sliding window search
    for i in range(len(words) - len(search_words) + 1):
        window = ' '.join(words[i:i+len(search_words)])
        ratio = SequenceMatcher(None, search_text, window).ratio()
        
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_match = window
    
    if best_match:
        return page.search_for(best_match)
    
    return []
```

**C. Multi-Line Option Handling**
```python
def highlight_multiline_option(page, option_text, label):
    """Handle options that span multiple lines"""
    
    # Try full text first
    instances = page.search_for(f"{label}) {option_text}")
    if instances:
        return highlight_instances(page, instances)
    
    # Try first line only
    first_line = option_text.split('\n')[0]
    instances = page.search_for(f"{label}) {first_line}")
    if instances:
        return highlight_instances(page, instances)
    
    # Try without punctuation
    option_clean = re.sub(r'[^\w\s]', '', option_text[:50])
    instances = page.search_for(option_clean)
    if instances:
        return highlight_instances(page, instances)
    
    return False
```

**D. Regex-Based Pattern Matching**
```python
def search_with_regex(page, pattern):
    """Search using regex patterns for complex matching"""
    
    text_dict = page.get_text("dict")
    
    for block in text_dict.get("blocks", []):
        for line in block.get("lines", []):
            line_text = ""
            for span in line.get("spans", []):
                line_text += span.get("text", "")
            
            if re.search(pattern, line_text):
                # Get bounding box and highlight
                bbox = line.get("bbox")
                if bbox:
                    highlight = page.add_highlight_annot(bbox)
                    highlight.set_colors(stroke=CORRECT_ANSWER_COLOR)
                    highlight.update()
                    return True
    
    return False
```

---

### 4️⃣ IMPLEMENTATION PLAN

#### Phase 1: Quick Wins (Expected: +5-7%)
```bash
# 1. Fix classifier edge cases
python scripts/classify_text.py --in data/raw_blocks.json --out data/classified_output.json --validate

# 2. Use better AI model with retry
python scripts/auto_answer_with_ollama.py --model phi4:14b --retry 3 --parallel 3

# 3. Enhanced highlighting
python scripts/generate_answered_pdf.py "Living Word.pdf" "output.pdf" --fuzzy-match --threshold 0.85
```

#### Phase 2: Advanced Improvements (Expected: +5-8%)
```bash
# 1. Multi-model consensus
python scripts/answer_with_consensus.py --models gemma2:9b,phi4:14b,mistral:latest

# 2. Question type detection
python scripts/classify_text.py --detect-types --handle-assertions

# 3. Validation and correction
python scripts/validate_and_fix.py
```

#### Phase 3: Fine-Tuning (Expected: +2-3%)
```bash
# 1. Manual review of failures
python scripts/review_failures.py

# 2. Custom model fine-tuning
# Fine-tune on biology MCQs

# 3. Iterative improvement
python scripts/analyze_errors.py
python scripts/fix_specific_cases.py
```

---

### 5️⃣ RECOMMENDED IMMEDIATE ACTIONS

**🚀 Priority 1 (Do This First)**
```bash
# Use better model with retry logic
python scripts/auto_answer_with_ollama.py --model phi4:14b --retry 3 --timeout 90
```

**⚡ Priority 2 (High Impact)**
```bash
# Run classifier validation
python scripts/validate_classification.py

# Fix questions with ≠4 options
python scripts/fix_merged_questions.py
```

**🎯 Priority 3 (Polish)**
```bash
# Enhanced PDF highlighting
python scripts/generate_answered_pdf.py --fuzzy-match --multi-line

# Review and fix failures manually
python scripts/review_dashboard.py
```

---

### 6️⃣ MONITORING & METRICS

Create a monitoring script:
```python
# monitor_accuracy.py
def calculate_accuracy_metrics():
    return {
        'parsing': {
            'blocks_extracted': 5223,
            'success_rate': 100.0
        },
        'classification': {
            'expected': 763,
            'found': 744,
            'success_rate': 97.5,
            'quality': 85.8  # 4-option questions
        },
        'answering': {
            'total': 744,
            'answered': 623,
            'success_rate': 83.7
        },
        'highlighting': {
            'attempted': 623,
            'successful': 610,
            'success_rate': 97.9
        },
        'overall': {
            'end_to_end': 79.9
        }
    }
```

---

## 📊 EXPECTED OUTCOMES

| Phase | Classification | AI Answering | Highlighting | Overall |
|-------|---------------|--------------|--------------|---------|
| Current | 97.5% | 83.7% | 98% | **79.9%** |
| Phase 1 | 98% | 89% | 99% | **86%** |
| Phase 2 | 99% | 94% | 99% | **92%** |
| Phase 3 | 99% | 96% | 99% | **94-95%** |

---

## 🎯 TARGET: 95% OVERALL ACCURACY

**Key Success Factors:**
1. ✅ Better AI model (phi4:14b or llama3.1:70b)
2. ✅ Retry logic with fallback models
3. ✅ Enhanced text matching (fuzzy + regex)
4. ✅ Question type detection
5. ✅ Validation and error correction
6. ✅ Parallel processing with rate limiting

**Timeline:**
- Phase 1: 2-3 hours
- Phase 2: 1 day
- Phase 3: 2-3 days
- **Total: 3-4 days to 95% accuracy**

---

## 📝 NEXT STEPS

1. **Run improved answering** with phi4:14b model
2. **Validate classification** and fix merged questions
3. **Implement retry logic** for failed questions
4. **Use fuzzy matching** for PDF highlighting
5. **Monitor progress** and iterate

Let me know which phase you'd like to start with! 🚀
