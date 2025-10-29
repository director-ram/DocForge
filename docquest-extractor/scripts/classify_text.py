#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classifier & Structurer — raw_blocks.json -> classified_output.json

State-machine based classifier that processes PDF text blocks into structured questions.
Handles options, answers, and explanations with proper boundary detection.

FIX: Prevents merging of sequential questions by properly detecting question boundaries
even when encountering orphaned options or incomplete question structures.
"""

import argparse
import json
import os
import re
from typing import List, Dict, Any, Optional, Tuple


def safe_load_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_dump_json(path: str, data: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ----------------------------
# Regex patterns (tunable)
# ----------------------------
Q_START_RE = re.compile(
    r"""^\s*(?:Q(?:uestion)?\s*[-:.]?\s*)?    # optional 'Q' or 'Question'
         (\d{1,4})?                          # optional explicit number
         [\).:]?\s*                          # ) or . or : after number
         (.*)$                               # the rest
     """,
    re.IGNORECASE | re.VERBOSE,
)

# Option markers: A) / (A) / a. / 1) / (1) / I) / (i)
OPT_RE = re.compile(
    r"""^\s*
        (?:\(?\s*([A-Da-d])\s*\)?|           # letter A-D
           \(?\s*([1-9])\s*\)?|              # number 1-9
           \(?\s*((?:i|v|x|I|V|X)+)\s*\)?)   # roman
        [\).\:\-]?\s+(.+)$                   # then text
    """,
    re.VERBOSE,
)

ANS_RE = re.compile(
    r"""^\s*(?:Ans(?:wer)?|Key|Correct\s*(?:Option|Answer))\s*[:.\-–]\s*(.+)$""",
    re.IGNORECASE,
)

EXP_RE = re.compile(
    r"""^\s*(?:Exp(?:lanation)?|Sol(?:ution)?)\s*[:.\-–]?\s*(.*)$""",
    re.IGNORECASE,
)

# Helpful signals for question detection
QUESTION_LURE = re.compile(
    r"(which of the following|choose the|correct statement|match the|assertion|reason)",
    re.IGNORECASE
)


def normalize(s: str) -> str:
    """Normalize text by removing soft hyphens and extra whitespace."""
    s = s.replace("\u00ad", "")  # soft hyphen
    s = s.replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_option(line: str) -> Optional[Tuple[str, str]]:
    """Parse an option line like '(1) Text' or 'A) Text' into (label, text)."""
    m = OPT_RE.match(line)
    if not m:
        return None
    label = m.group(1) or m.group(2) or m.group(3)
    text = m.group(4) if (m.lastindex is not None and m.lastindex >= 4) else ""
    if not text:
        return None
    # Normalize label to uppercase letter if possible
    lab = str(label).strip()
    if lab.isalpha():
        lab = lab.upper()
    return lab, normalize(text)


def parse_answer_labels(s: str) -> List[str]:
    """Extract answer labels from string like '(A)', 'A,D', '2 & 4', etc."""
    s = s.strip()
    s = re.sub(r"^\((.+)\)$", r"\1", s)  # Remove surrounding parentheses

    # Split by common separators
    parts = re.split(r"[,\s;/&]+|and", s, flags=re.IGNORECASE)
    parts = [p for p in parts if p]

    out = []
    for p in parts:
        p = p.strip()
        p = re.sub(r"^\((.+)\)$", r"\1", p)  # Strip parens

        # Try letter
        if re.fullmatch(r"[A-Da-d]", p):
            out.append(p.upper())
            continue
        # Try number
        if re.fullmatch(r"\d{1,2}", p):
            out.append(p)
            continue
        # Try roman
        if re.fullmatch(r"(?:i|v|x|I|V|X)+", p):
            out.append(p.upper())
            continue
    return out


def label_to_index(labels: List[str], lab: str) -> Optional[int]:
    """Map an answer label to its index in the options list."""
    if lab in labels:
        return labels.index(lab)
    
    # Map letters like 'A'->0, numbers '1'->0
    if re.fullmatch(r"[A-D]", lab) and len(labels) <= 6:
        try:
            return ord(lab) - ord('A')
        except Exception:
            return None
    
    if re.fullmatch(r"\d{1,2}", lab):
        idx = int(lab) - 1
        if 0 <= idx < len(labels):
            return idx
    
    # Roman fallback: I->0, II->1, ...
    roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
    if lab in roman_map:
        idx = roman_map[lab] - 1
        if 0 <= idx < len(labels):
            return idx
    
    return None


def stitch_wrap(prev: str, cur: str) -> Optional[str]:
    """Try to join 'cur' to 'prev' when it's probably a wrapped continuation."""
    if not prev:
        return None
    
    # Don't merge if current line starts like an option
    if re.match(r"^\(?[A-Da-d1-9IVXivx]\)?[\).\:\-]\s", cur):
        return None
    
    # Don't merge if it's an answer/explanation marker
    if re.match(r"^\s*(Ans|Key|Correct|Exp|Sol)", cur, re.IGNORECASE):
        return None
    
    # If cur starts lowercase and prev doesn't end with punctuation → likely continuation
    if cur[:1].islower() and not re.search(r"[.:;!?]\s*$", prev):
        return prev + " " + cur
    
    # If cur is short and doesn't look like a new block, merge
    if len(cur) < 40 and not re.match(r"^\s*\d+[\).\s]", cur):
        return prev + " " + cur
    
    return None


def classify_blocks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Walk through raw lines and build question groups using state machine.
    
    FIX: Properly detects new questions even with incomplete previous questions.
    This prevents merging of sequential questions.
    """
    results = []
    cur = None
    q_seq_on_page: Dict[int, int] = {}

    def new_temp_id(page: int) -> str:
        k = q_seq_on_page.get(page, 0) + 1
        q_seq_on_page[page] = k
        return f"p{page}_q{k}"

    def finalize_current():
        nonlocal cur
        if not cur:
            return
        
        # Calculate confidence score
        conf = 0.0
        if cur.get("question_text"):
            conf += 0.40
        if len(cur.get("options", [])) >= 2:
            conf += 0.20
        if cur.get("answer_index") is not None:
            conf += 0.20
        if cur.get("explanation"):
            conf += 0.10
        if len(cur.get("question_text", "")) >= 20:
            conf += 0.10
        cur["confidence"] = round(min(conf, 1.0), 2)
        cur["manual_review"] = (cur["confidence"] < 0.75)

        # Determine question type
        qt = "single_correct"
        q_text = cur.get("question_text", "")
        if re.search(r"(select.*correct.*statements|more than one|multiple)", q_text, re.IGNORECASE):
            qt = "multiple_correct"
        if re.search(r"(assertion.*reason|A\)|R\))", q_text, re.IGNORECASE):
            qt = "assertion_reason"
        if re.search(r"(integer\s*type|numerical\s*value)", q_text, re.IGNORECASE):
            qt = "integer"
        cur["question_type_hint"] = qt

        results.append(cur)
        cur = None

    # Process blocks in order
    for b in blocks:
        page = int(b.get("page", 0) or 0)
        text = normalize(b.get("text", ""))
        if not text:
            continue

        # Try to extend current section if it's a continuation
        if cur:
            # Extend last option if wrapping
            if cur.get("options"):
                last = cur["options"][-1]["text"] if cur["options"] else ""
                merged = stitch_wrap(last, text)
                if merged:
                    cur["options"][-1]["text"] = normalize(merged)
                    cur["pages"].add(page)
                    continue

            # Extend explanation if wrapping
            if cur.get("explanation"):
                merged = stitch_wrap(cur["explanation"], text)
                if merged:
                    cur["explanation"] = normalize(merged)
                    cur["pages"].add(page)
                    continue

            # Extend question if wrapping and we didn't start options yet
            if not cur.get("options"):
                merged = stitch_wrap(cur.get("question_text", ""), text)
                if merged:
                    cur["question_text"] = normalize(merged)
                    cur["pages"].add(page)
                    continue

        # Detect state switches
        
        # 1) Answer line?
        m_ans = ANS_RE.match(text)
        if cur and m_ans:
            cur["answer_raw"] = normalize(m_ans.group(1))
            # Parse labels from answer_raw
            labels = [opt["label"] for opt in cur.get("options", [])]
            found = parse_answer_labels(cur["answer_raw"])
            ans_idx = None
            ans_lab = None
            for lab in found:
                idx = label_to_index(labels, lab)
                if idx is not None:
                    ans_idx = idx
                    ans_lab = labels[idx]
                    break
            cur["answer_index"] = ans_idx
            cur["answer_label"] = ans_lab
            cur["pages"].add(page)
            continue

        # 2) Explanation start?
        m_exp = EXP_RE.match(text)
        if cur and m_exp:
            seed = normalize(m_exp.group(1) or "")
            if cur.get("explanation"):
                cur["explanation"] = normalize(cur["explanation"] + (" " + seed if seed else ""))
            else:
                cur["explanation"] = seed
            cur["pages"].add(page)
            continue

        # 3) New Question?
        # CRITICAL FIX: Check for new questions BEFORE checking for options!
        # This prevents "2. Which..." from being mistakenly treated as option "(2) Which..."
        m_q = Q_START_RE.match(text)
        looks_like_q = False
        body = ""
        
        if m_q:
            num = m_q.group(1)
            body = normalize(m_q.group(2) or "")
            
            # Detect new question if:
            # - We have a number AND (substantial body text OR question keywords OR question mark)
            # - OR we have strong question keywords regardless of number
            has_number = bool(num)
            has_substance = len(body) > 10
            has_keywords = bool(QUESTION_LURE.search(text))
            ends_with_q = text.strip().endswith("?")
            
            # Start new question if we see numbered question with substance
            if has_number and (has_substance or has_keywords or ends_with_q):
                looks_like_q = True
            # Or if we see strong question patterns
            elif has_keywords and (has_number or ends_with_q):
                looks_like_q = True

        if looks_like_q:
            # Finalize previous question (even if incomplete)
            finalize_current()
            cur = {
                "temp_id": new_temp_id(page),
                "question_text": body if body else text,
                "options": [],
                "answer_index": None,
                "answer_label": None,
                "answer_raw": None,
                "explanation": "",
                "confidence": 0.0,
                "manual_review": True,
                "question_type_hint": "single_correct",
                "source": {"pdf": b.get("source_pdf", "unknown"), "pages": []},
                "pages": set()
            }
            cur["pages"].add(page)
            continue

        # 4) Option line?
        # Now check for options AFTER we've ruled out new questions
        m_opt = parse_option(text)
        if cur and m_opt:
            lab, opt_text = m_opt
            cur.setdefault("options", []).append({"label": lab, "text": opt_text})
            cur["pages"].add(page)
            continue

        # 5) If inside a question but none matched → continuation of question text
        if cur:
            cur["question_text"] = normalize((cur.get("question_text", "") + " " + text).strip())
            cur["pages"].add(page)
            continue

        # 6) Otherwise ignore line (headers, front-matter, etc.)

    # Finalize last question
    finalize_current()

    # Convert pages set to sorted list
    for r in results:
        r["source"]["pages"] = sorted(list(r.pop("pages", set())))

    return results


def main():
    ap = argparse.ArgumentParser(
        description="Classifier & Structurer — raw_blocks.json -> classified_output.json"
    )
    ap.add_argument("--in", dest="inp", required=True, help="Input raw_blocks.json")
    ap.add_argument(
        "--out", 
        dest="out", 
        default="data/classified_output.json", 
        help="Output JSON path"
    )
    args = ap.parse_args()

    blocks = safe_load_json(args.inp)
    
    # Sort by global order
    blocks.sort(key=lambda b: (
        int(b.get("page", 0)), 
        int(b.get("col", 0)), 
        int(b.get("line_idx", 0))
    ))

    results = classify_blocks(blocks)

    # Post-pass: if a result has options but no answer, flag for manual review
    for r in results:
        if r.get("options") and r.get("answer_index") is None:
            r["manual_review"] = True

    safe_dump_json(args.out, results)
    print(f"[ok] wrote {len(results)} grouped question sets -> {args.out}")


if __name__ == "__main__":
    main()