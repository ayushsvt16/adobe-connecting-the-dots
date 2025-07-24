import argparse
import json
import os
from extractor import extract_outline

def process_folder(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(output_dir, output_filename)

            try:                
                result = extract_outline(input_path)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"Saved: {output_filename}")
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch extract outlines from PDFs")
    parser.add_argument("--input", default="input", help="Input folder containing PDF files")
    parser.add_argument("--output", default="output", help="Output folder for JSON results")
    args = parser.parse_args()

    process_folder(args.input, args.output)



#!/usr/bin/env python3
# """
# Docker entry point for PDF outline extraction
# Processes all PDFs from /app/input and saves results to /app/output
# """

# import os
# import sys
# import time
# from extractor_optimized import process_pdf_directory

# def main():
#     input_dir = "/app/input"
#     output_dir = "/app/output"
    
#     # Check if input directory exists
#     if not os.path.exists(input_dir):
#         print(f"Error: Input directory {input_dir} does not exist")
#         sys.exit(1)
    
#     # Check if there are any PDF files
#     pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
#     if not pdf_files:
#         print(f"No PDF files found in {input_dir}")
#         sys.exit(1)
    
#     print(f"Starting PDF outline extraction...")
#     print(f"Input directory: {input_dir}")
#     print(f"Output directory: {output_dir}")
    
#     start_time = time.time()
    
#     # Process all PDFs
#     process_pdf_directory(input_dir, output_dir)
    
#     end_time = time.time()
#     processing_time = end_time - start_time
    
#     print(f"\n✅ Processing completed in {processing_time:.2f} seconds")
#     print(f"Processed {len(pdf_files)} PDF files")

# if __name__ == "__main__":
#     main()
