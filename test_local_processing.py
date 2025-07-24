#!/usr/bin/env python3
"""
Test script to demonstrate local PDF processing functionality
"""

import os
import sys
import time
from extractor_optimized import process_pdf_directory

def test_local_processing():
    """Test the local processing functionality"""
    input_dir = "input"
    output_dir = "output"
    
    print(f"Testing PDF outline extraction...")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Ensure directories exist
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    start_time = time.time()
    
    # Process PDFs (will handle empty directory gracefully)
    process_pdf_directory(input_dir, output_dir)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"\n✅ Processing completed in {processing_time:.2f} seconds")
    
    # Check results
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    json_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.json')]
    
    print(f"Found {len(pdf_files)} PDF files in input directory")
    print(f"Generated {len(json_files)} JSON files in output directory")
    
    if pdf_files:
        print("\nPDF files found:")
        for pdf in pdf_files:
            print(f"  - {pdf}")
            
    if json_files:
        print("\nJSON files generated:")
        for json_file in json_files:
            print(f"  - {json_file}")
    
    return len(pdf_files) == len(json_files)

if __name__ == "__main__":
    success = test_local_processing()
    print(f"\n{'✅ Test passed!' if success else '❌ Test failed!'}")
