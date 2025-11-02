#!/usr/bin/env python3
"""
Script to parse PDF files and extract raw text blocks with metadata
Compatible with classify_text.py input format
"""
import argparse
import json
import fitz  # PyMuPDF
import os
from pathlib import Path


def extract_text_blocks(pdf_path, strip_headers=False, strip_footers=False):
    """
    Extract text blocks from a PDF file with bounding boxes and position metadata
    Output format matches the classifier's expected input
    """
    text_blocks = []
    doc = fitz.open(pdf_path)
    pdf_name = Path(pdf_path).name
    
    line_idx = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Extract text with bounding box information
        text_dict = page.get_text("dict")
        
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                # Extract text from spans
                line_text = ""
                for span in line.get("spans", []):
                    line_text += span.get("text", "")
                
                line_text = line_text.strip()
                
                # Skip empty lines
                if not line_text:
                    continue
                
                # Get bounding box
                bbox = line.get("bbox", [0, 0, 0, 0])
                
                # Skip headers/footers if requested (simple heuristic)
                if strip_headers and bbox[1] < 100:  # top 100 pixels
                    continue
                if strip_footers and bbox[3] > page.rect.height - 100:  # bottom 100 pixels
                    continue
                
                # Create block in the format expected by classifier
                text_block = {
                    "page": page_num + 1,  # 1-indexed
                    "bbox": list(bbox),
                    "text": line_text,
                    "line_idx": line_idx,
                    "col": 0,  # Could be enhanced with column detection
                    "source_pdf": pdf_name
                }
                
                text_blocks.append(text_block)
                line_idx += 1
    
    doc.close()
    return text_blocks


def save_raw_blocks(blocks, output_path):
    """
    Save extracted text blocks to a JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(blocks, file, indent=2, ensure_ascii=False)


def main():
    """
    Main function to parse PDF and save raw blocks
    """
    parser = argparse.ArgumentParser(description="Parse PDF and extract raw text blocks")
    parser.add_argument("pdf", nargs='?', default="input.pdf", help="Input PDF file path")
    parser.add_argument("--out", default="data/raw_blocks.json", help="Output JSON file path")
    parser.add_argument("--strip-headers", action="store_true", help="Skip header text")
    parser.add_argument("--strip-footers", action="store_true", help="Skip footer text")
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"Error: Input PDF '{args.pdf}' not found")
        return
    
    print(f"Extracting text blocks from {args.pdf}")
    blocks = extract_text_blocks(args.pdf, args.strip_headers, args.strip_footers)
    
    print(f"Extracted {len(blocks)} text lines")
    save_raw_blocks(blocks, args.out)
    
    print(f"[ok] Saved to {args.out}")


if __name__ == "__main__":
    main()