import fitz
from typing import Dict, Any, List, Set, Tuple
import re
from collections import defaultdict
import os
import json
from difflib import SequenceMatcher
import numpy as np
from dataclasses import dataclass

@dataclass
class TextBlock:
    text: str
    y_pos: float
    page_num: int
    font_size: float
    is_bold: bool

class HeaderFooterDetector:
    def __init__(self, page_height: float, tolerance: float = 10.0):
        self.page_height = page_height
        self.tolerance = tolerance
        self.top_clusters = defaultdict(list)
        self.bottom_clusters = defaultdict(list)
        self.footer_patterns = [
            r'^Page\s+\d+(\s+of\s+\d+)?$',
            r'^\d+$',
            r'^Chapter\s+\d+$',
            r'^\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*$',  # Dates
            r'^[A-Za-z0-9\s]{1,10}$',  # Very short repeating phrases
            r'^\s*[ivx]+\s*$',  # Roman numerals
            r'^[A-Za-z0-9\s\-_]{1,20}\s+\|\s+\d+$'  # Common footer formats with separators
        ]

    def cluster_key(self, y_pos: float) -> int:
        """Round y-position to nearest tolerance value for clustering"""
        return round(y_pos / self.tolerance) * self.tolerance
        
    def add_text_block(self, block: TextBlock):
        """Add text block to appropriate cluster based on position"""
        y_pos = block.y_pos
        key = self.cluster_key(y_pos)
        
        # Classify as header (top 15% of page) or footer (bottom 15%)
        if y_pos < (self.page_height * 0.15):
            self.top_clusters[key].append(block)
        elif y_pos > (self.page_height * 0.85):
            self.bottom_clusters[key].append(block)
            
    def text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity ratio between two text strings"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def merge_fragments(self, text1: str, text2: str) -> str:
        """Merge text fragments if they form a continuous word/phrase"""
        # Try different overlapping patterns
        if text1.endswith(text2[:min(len(text1), len(text2))]):
            return text1 + text2[min(len(text1), len(text2)):]
        if text2.startswith(text1[-min(len(text1), len(text2)):]):
            return text1 + text2[min(len(text1), len(text2)):]
        return ""
        
    def is_header_footer(self, block: TextBlock) -> bool:
        """Determine if text block is likely header/footer"""
        y_pos = block.y_pos
        text = block.text.strip()
        
        # Skip empty, very short, or numeric-only text
        if not text or text.isdigit() or len(text) < 3:
            return True
            
        # Check position
        if y_pos < (self.page_height * 0.10) or y_pos > (self.page_height * 0.90):
            key = self.cluster_key(y_pos)
            
            # Get relevant cluster
            cluster = self.top_clusters[key] if y_pos < (self.page_height * 0.10) else self.bottom_clusters[key]
            
            # Count similar texts in cluster
            similar_count = sum(1 for b in cluster 
                              if (self.text_similarity(b.text, text) > 0.85 
                                  and abs(b.y_pos - y_pos) < 20 
                                  and b.page_num != block.page_num))
            
            # If text appears similarly in multiple pages at same position, likely header/footer
            if similar_count >= 2:
                return True
                
        # Check common header/footer patterns
        patterns = [
            r'^Page\s+\d+(\s+of\s+\d+)?$',
            r'^\d+$',
            r'^Chapter\s+\d+$',
            r'^\s*\d{1,2}/\d{1,2}/\d{2,4}\s*$',
            r'^[A-Za-z0-9\s]{1,20}$'  # Short repeating phrases
        ]
        
        return any(re.match(p, text) for p in patterns)

def merge_fragmented_text(fragments: List[str]) -> str:
    """Merge fragmented heading text pieces"""
    merged = []
    for text in fragments:
        if not merged or not (merged[-1].endswith(text[:1]) or text.startswith(merged[-1][-1])):
            merged.append(text)
    return " ".join(merged)

def extract_outline(pdf_path: str) -> Dict[str, Any]:
    """Extract structured outline from PDF with improved header/footer detection"""
    doc = fitz.open(pdf_path)
    outline = []
    seen_headings = set()
    
    # Initialize header/footer detector with first page height
    detector = HeaderFooterDetector(doc[0].rect.height) if len(doc) > 0 else None
    
    # First pass: collect text blocks for header/footer detection
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
                    
                max_size = max(span["size"] for span in line["spans"])
                is_bold = any("Bold" in span.get("font", "") for span in line["spans"])
                
                text_block = TextBlock(
                    text=text,
                    y_pos=line["bbox"][1],
                    page_num=page_num,
                    font_size=max_size,
                    is_bold=is_bold
                )
                
                if detector:
                    detector.add_text_block(text_block)

    # Second pass: collect and merge text fragments
    page_fragments = defaultdict(list)
    merged_blocks = []
    
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
                
                # Group fragments by vertical position and font properties
                key = (page_num, round(y_pos), max_size, is_bold)
                page_fragments[key].append(TextBlock(
                    text=text,
                    y_pos=y_pos,
                    page_num=page_num,
                    font_size=max_size,
                    is_bold=is_bold
                ))
    
    # Merge fragments within each group
    for blocks in page_fragments.values():
        if len(blocks) == 1:
            merged_blocks.append(blocks[0])
            continue
            
        # Sort blocks by x-position (assumed to be reading order)
        blocks.sort(key=lambda b: b.text)
        merged_text = blocks[0].text
        
        # Try to merge subsequent fragments
        for block in blocks[1:]:
            merged = detector.merge_fragments(merged_text, block.text)
            if merged:
                merged_text = merged
            else:
                # If can't merge, treat as separate heading
                merged_blocks.append(blocks[0])
                merged_text = block.text
        
        if merged_text:
            merged_blocks.append(TextBlock(
                text=merged_text,
                y_pos=blocks[0].y_pos,
                page_num=blocks[0].page_num,
                font_size=blocks[0].font_size,
                is_bold=blocks[0].is_bold
            ))

    # Third pass: extract headings from merged blocks
    title = ""
    for block in merged_blocks:
                
            for line in block["lines"]:
                if not line.get("spans"):
                    continue
                    
                text = " ".join(span["text"].strip() for span in line["spans"]).strip()
                if not text or text in seen_headings:
                    continue
                    
                max_size = max(span["size"] for span in line["spans"])
                is_bold = any("Bold" in span.get("font", "") for span in line["spans"])
                
                text_block = TextBlock(
                    text=text,
                    y_pos=line["bbox"][1],
                    page_num=page_num,
                    font_size=max_size,
                    is_bold=is_bold
                )
                
                # Skip headers/footers
                if detector and detector.is_header_footer(text_block):
                    continue
                
                # Determine heading level
                level = None
                if max_size >= 16 or (max_size >= 14 and is_bold):
                    level = "H1"
                elif max_size >= 14 or (max_size >= 12 and is_bold):
                    level = "H2"
                elif max_size >= 12 or is_bold:
                    level = "H3"
                    
                if level:
                    # Set title from first H1 on first page
                    if not title and page_num == 0 and level == "H1":
                        title = text
                    outline.append({
                        "level": level,
                        "text": text,
                        "page": page_num + 1
                    })
                    seen_headings.add(text)

    doc.close()
    return {
        "title": title,
        "outline": outline
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
        input_directory = sys.argv[1]
        output_directory = sys.argv[2] if len(sys.argv) > 2 else "output"
        
        process_pdf_directory(input_directory, output_directory)
    else:
        print("Usage: python script.py <input_directory> [output_directory]")
