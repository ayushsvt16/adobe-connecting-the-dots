# PDF Outline Extractor

A high-performance PDF outline extraction solution that identifies document structure (title, H1, H2, H3 headings) and outputs structured JSON data.

## Approach

This solution uses a **rule-based approach** optimized for performance and accuracy:

### 1. **Multi-Criteria Heading Detection**
- **Numbered sections**: Detects `1.`, `1.1`, `1.1.1` patterns for hierarchical headings
- **Font analysis**: Uses font size and bold formatting as primary indicators
- **Keyword matching**: Identifies common heading patterns (Introduction, Overview, etc.)
- **Position context**: Considers page number and text position for better classification

### 2. **Title Extraction**
- Analyzes first page for title candidates
- Prioritizes larger, bold text that appears early in the document
- Filters out common non-title patterns (page numbers, headers, etc.)

### 3. **Performance Optimizations**
- **Minimal dependencies**: Only uses PyMuPDF for fast PDF processing
- **Efficient text processing**: Single-pass document analysis
- **Memory management**: Proper resource cleanup and garbage collection
- **Deduplication**: Prevents duplicate headings in output

## Libraries Used

- **PyMuPDF (1.23.14)**: Fast PDF parsing and text extraction
  - Chosen for its speed and minimal memory footprint
  - Provides detailed font information needed for heading detection
  - Works offline without requiring external models

## Key Features

- ✅ **Batch Processing**: Processes all PDFs from input directory
- ✅ **Fast Performance**: < 10 seconds for 50-page PDFs
- ✅ **Offline Operation**: No internet connectivity required
- ✅ **Small Footprint**: Minimal Docker image size
- ✅ **AMD64 Compatible**: Explicit platform specification
- ✅ **Multilingual Support**: Handles various character encodings

## Solution Architecture

```
Input PDFs → PyMuPDF Parser → Heading Classifier → JSON Output
     ↓              ↓               ↓              ↓
  /app/input   Font Analysis   Rule-based     /app/output
               Text Extraction  Classification
```

## Building and Running

### Docker Build
```bash
docker build --platform linux/amd64 -t pdf-extractor:latest .
```

### Docker Run
```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  pdf-extractor:latest
```

### Local Development
```bash
# Install dependencies
pip install -r requirements_minimal.txt

# Run on single file
python extractor_optimized.py input.pdf

# Process directory
python run_docker.py
```

## Input/Output Format

### Input
- PDF files in `/app/input/` directory
- Maximum 50 pages per document
- Any text-based PDF format

### Output
- JSON files in `/app/output/` directory
- One JSON file per input PDF
- Format: `filename.json` for `filename.pdf`

### JSON Structure
```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Introduction",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "1.1 Overview",
      "page": 2
    }
  ]
}
```

## Performance Specifications

- **Execution Time**: ≤ 10 seconds for 50-page PDF
- **Memory Usage**: < 1GB RAM typical
- **Model Size**: N/A (rule-based approach)
- **Platform**: Linux AMD64 (x86_64)
- **Network**: Offline operation only

## Heading Classification Logic

### H1 Headings
- Main numbered sections (`1.`, `2.`, etc.)
- Large font size (≥18pt) 
- Bold text on early pages
- Common document sections (Introduction, Conclusion, etc.)

### H2 Headings  
- Subsections (`1.1`, `2.1`, etc.)
- Medium font size (≥14pt) with bold formatting
- Standard section keywords with appropriate formatting

### H3 Headings
- Sub-subsections (`1.1.1`, `2.1.1`, etc.)
- Smaller font size (≥12pt) with bold formatting
- Contextual classification based on hierarchy

## Error Handling

- **File Access**: Graceful handling of corrupted/unreadable PDFs
- **Encoding**: Proper UTF-8 output for international characters
- **Memory**: Efficient resource management for large documents
- **Edge Cases**: Robust handling of unusual document structures

## Testing

The solution has been tested with:
- Various document types (academic papers, technical reports, forms)
- Different languages and character sets
- Edge cases (single page, no headings, malformed PDFs)
- Performance benchmarks with 50+ page documents

## Compliance

- ✅ AMD64 platform compatibility
- ✅ No GPU dependencies
- ✅ Offline operation (no network calls)
- ✅ Performance constraints met
- ✅ Memory efficiency optimized
- ✅ Proper error handling and logging
