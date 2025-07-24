import fitz
import re
import json
import os
from typing import Dict, List, Any

def classify_heading_level(text: str, font_size: float, is_bold: bool, 
                          page_num: int, y_position: float) -> str:
    """
    Classify heading level based on multiple criteria
    """
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Skip very short text or common non-headings
    if len(text) < 3 or text.lower() in ['page', 'of', 'and', 'the', 'for']:
        return None
    
    # Check for numbered headings (strongest indicator)
    if re.match(r'^\d+\.\s', text):  # "1. Introduction"
        return "H1"
    elif re.match(r'^\d+\.\d+\s', text):  # "1.1 Overview"
        return "H2"
    elif re.match(r'^\d+\.\d+\.\d+\s', text):  # "1.1.1 Details"
        return "H3"
    
    # Check for common heading patterns
    heading_keywords = [
        r'^(introduction|overview|conclusion|summary|references|appendix|acknowledgements)',
        r'^(table of contents|revision history|abstract|executive summary)',
        r'^(chapter|section|part)\s+\d+',
        r'^(background|methodology|results|discussion|future work)'
    ]
    
    text_lower = text.lower()
    for pattern in heading_keywords:
        if re.search(pattern, text_lower):
            if font_size >= 16 or is_bold:
                return "H1"
            else:
                return "H2"
    
    # Font size and formatting based classification
    if font_size >= 18:
        return "H1"
    elif font_size >= 14 and is_bold:
        return "H1" if page_num <= 2 else "H2"  # First pages more likely to have H1
    elif font_size >= 13:
        return "H2" if is_bold else "H3"
    elif font_size >= 12 and is_bold:
        return "H3"
    
    return None

def extract_title_from_first_page(page) -> str:
    """
    Extract document title from first page
    """
    title_candidates = []
    blocks = page.get_text("dict")["blocks"]
    
    for block in blocks:
        if "lines" not in block:
            continue
            
        for line in block["lines"]:
            line_text = " ".join(span["text"].strip() for span in line["spans"]).strip()
            if not line_text:
                continue
            
            # Get text properties
            max_size = max(span["size"] for span in line["spans"]) if line["spans"] else 0
            is_bold = any("Bold" in span.get("font", "") for span in line["spans"])
            
            # Title heuristics
            if (len(line_text.split()) >= 3 and 
                not line_text.endswith(":") and
                not re.match(r'^\d+\.', line_text) and
                (max_size >= 16 or is_bold) and
                not line_text.lower().startswith(('page', 'chapter', 'section'))):
                
                title_candidates.append((line_text, max_size, is_bold))
    
    # Return the largest/boldest title candidate
    if title_candidates:
        title_candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)  # Sort by bold, then size
        return title_candidates[0][0]
    
    return ""

def extract_outline(pdf_path: str) -> Dict[str, Any]:
    """
    Extract structured outline from PDF
    """
    try:
        doc = fitz.open(pdf_path)
        outline = []
        title = ""
        seen_headings = set()
        
        # Extract title from first page
        if len(doc) > 0:
            title = extract_title_from_first_page(doc[0])
        
        # Process each page
        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    line_text = " ".join(span["text"].strip() for span in line["spans"]).strip()
                    if not line_text or line_text in seen_headings:
                        continue
                    
                    # Get text properties
                    max_size = max(span["size"] for span in line["spans"]) if line["spans"] else 0
                    is_bold = any("Bold" in span.get("font", "") for span in line["spans"])
                    y_position = line["bbox"][1] if "bbox" in line else 0
                    
                    # Classify heading level
                    level = classify_heading_level(line_text, max_size, is_bold, page_num, y_position)
                    
                    if level:
                        outline.append({
                            "level": level,
                            "text": line_text,
                            "page": page_num + 1
                        })
                        seen_headings.add(line_text)
        
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
