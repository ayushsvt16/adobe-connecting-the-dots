from typing import Dict, Any, List
import fitz
import json
import os
from collections import defaultdict
import re

def extract_title_from_first_page(page) -> str:
    """Extract title from the first page"""
    blocks = page.get_text("dict")["blocks"]
    max_font_size = 0
    title = ""
    
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if span["size"] > max_font_size and len(span["text"].strip()) > 3:
                    max_font_size = span["size"]
                    title = span["text"].strip()
    return title

def is_footer_text(text: str, y_pos: float, page_height: float, position_text_map: dict, page_num: int) -> bool:
    """Check if text is likely a footer"""
    # Check if text matches common footer patterns
    footer_patterns = [
        r'^Page\s+\d+(\s+of\s+\d+)?$',
        r'^\d+$',
        r'^Chapter\s+\d+$',
        r'^\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*$',
        r'^[A-Za-z0-9\s]{1,10}$',
        r'^\s*[ivx]+\s*$',
        r'^[A-Za-z0-9\s\-_]{1,20}\s+\|\s+\d+$'
    ]
    
    if any(re.match(pattern, text.lower()) for pattern in footer_patterns):
        return True
    
    # Check position (top 10% or bottom 10% of page)
    margin = page_height * 0.1
    if y_pos > (page_height - margin) or y_pos < margin:
        # Check if similar text appears in same position on other pages
        pos_key = round(y_pos / 10) * 10
        similar_texts = position_text_map.get(pos_key, [])
        similar_count = sum(1 for t, p in similar_texts 
                          if p != page_num and len(t) > 3 
                          and (t in text or text in t))
        return similar_count >= 2
        
    return False

def merge_fragments(fragments: List[str]) -> str:
    """Merge text fragments that might be split"""
    if not fragments:
        return ""
    result = fragments[0]
    for i in range(1, len(fragments)):
        if fragments[i] in result or result in fragments[i]:
            continue
        if any(result.endswith(fragments[i][:j]) or 
               fragments[i].startswith(result[-j:]) 
               for j in range(1, min(len(result), len(fragments[i])) + 1)):
            result += fragments[i][min(len(result), len(fragments[i])):]
    return result

def extract_outline(pdf_path: str) -> Dict[str, Any]:
    """
    Extract structured outline from PDF
    """
    try:
        doc = fitz.open(pdf_path)
        outline = []
        title = ""
        position_text_map = defaultdict(list)
        
        # First pass: collect text positions
        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    y_pos = round(line["bbox"][1] / 10) * 10
                    text = " ".join(span["text"].strip() for span in line["spans"]).strip()
                    if text:
                        position_text_map[y_pos].append((text, page_num))
        
        # Extract title from first page
        if len(doc) > 0:
            title = extract_title_from_first_page(doc[0])

        # Group text by position for fragment merging
        text_groups = defaultdict(list)
        seen_headings = set()

        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    if not line.get("spans"):
                        continue
                    
                    text = " ".join(span["text"].strip() for span in line["spans"]).strip()
                    if not text:
                        continue
                        
                    y_pos = line["bbox"][1]
                    max_size = max(span["size"] for span in line["spans"])
                    is_bold = any("Bold" in span.get("font", "") for span in line["spans"])
                    
                    # Skip likely headers/footers
                    if is_footer_text(text, y_pos, page.rect.height, position_text_map, page_num):
                        continue
                        
                    # Group similar text by position and size
                    group_key = (page_num, round(y_pos/5)*5, max_size)
                    text_groups[group_key].append(text)

        # Process grouped text
        for (page_num, _, size), texts in text_groups.items():
            merged_text = merge_fragments(texts)
            if not merged_text or merged_text in seen_headings or len(merged_text) < 3:
                continue
                
            # Determine heading level
            if size >= 16:
                level = "H1"
            elif size >= 14:
                level = "H2"
            elif size >= 12:
                level = "H3"
            else:
                continue
                
            outline.append({
                "level": level,
                "text": merged_text,
                "page": page_num + 1
            })
            seen_headings.add(merged_text)

        doc.close()
        return {
            "title": title,
            "outline": outline
        }

    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return {
            "title": "",
            "outline": []
        }

def process_pdf_directory(input_dir: str, output_dir: str):
    """
    Process all PDFs in input directory and save results to output directory
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all PDF files
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in input directory")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        output_file = os.path.splitext(pdf_file)[0] + '.json'
        output_path = os.path.join(output_dir, output_file)
        
        print(f"Processing: {pdf_file}")
        
        # Extract outline
        result = extract_outline(pdf_path)
        
        # Save result
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved: {output_file}")

if __name__ == "__main__":
    # For local testing
    import sys
    if len(sys.argv) > 1:
        result = extract_outline(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        process_pdf_directory("/app/input", "/app/output")
