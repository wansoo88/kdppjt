# KDP Local Automation

Local pipeline for creating KDP (Kindle Direct Publishing) picture books.

## Features

- 3-stage AI story writing (draft → edit → polish)
- Automatic image prompt generation for ChatGPT/DALL-E
- PDF generation for KDP upload
- Support for manual content upload

## Requirements

- Python 3.10+
- For AI generation: Ollama (free, local)

## Installation

```bash
# Clone repository
git clone https://github.com/wansoo88/kdppjt.git
cd kdppjt

# Install dependencies
pip install -r requirements.txt

# (Optional) Install Ollama for AI generation
# https://ollama.ai
```

## Quick Start

### Option 1: AI-Generated Story

```bash
# Generate story with AI (requires Ollama)
python story_writer.py --book books/my-story --topic "A brave rabbit discovers a magical garden"

# Or use mock backend for testing
python story_writer.py --book books/my-story --topic "..." --backend mock
```

Output files:
- `books/my-story/manuscript.md` - Story text
- `books/my-story/image_prompts.md` - ChatGPT image prompts
- `books/my-story/story_data.json` - Raw data

### Option 2: Manual Upload

Create your book folder:
```
books/
  my-book/
    manuscript.md    <- Your story (required)
    cover.png        <- Cover image (required)
    config.yaml      <- Metadata (optional)
```

### Generate PDF

```bash
# After adding cover.png to your book folder
python merge.py --book books/my-story
```

Output:
- `output/my-story/interior.pdf` - Book interior
- `output/my-story/cover.pdf` - Cover for KDP

## Workflow

```
1. Write Story
   python story_writer.py --book books/my-book --topic "Your story idea"
   
2. Generate Images
   Open image_prompts.md → Copy prompts to ChatGPT → Save images
   
3. Add Cover
   Save cover image as books/my-book/cover.png
   
4. Create PDF
   python merge.py --book books/my-book
   
5. Upload to KDP
   Upload interior.pdf and cover.pdf to kdp.amazon.com
```

## Commands Reference

### story_writer.py

```bash
python story_writer.py --book <path> --topic <topic> [options]

Options:
  --book, -b     Book folder path (required)
  --topic, -t    Story topic/premise (required)
  --pages, -p    Number of pages (default: 12)
  --age          Target age range (default: 4-8)
  --backend      LLM backend: ollama, claude, mock (default: ollama)
```

### merge.py

```bash
python merge.py --book <path> [options]

Options:
  --book, -b     Book folder path (required)
  --output, -o   Output directory (default: output/<book-name>)
```

### run.py (Full Pipeline)

```bash
python run.py --config config/book_config.yaml [options]

Options:
  --config, -c   Config file path (required)
  --resume, -r   Resume from previous run
  --mock, -m     Use mock backends for testing
```

## File Structure

```
kdppjt/
├── books/                  # Your book projects
│   └── example-book/
│       ├── manuscript.md
│       ├── cover.png
│       └── config.yaml
├── output/                 # Generated PDFs
├── kdp/                    # Core library
│   ├── backends/           # AI backends (Ollama, Claude, etc.)
│   ├── pdf_assembler.py
│   └── ...
├── story_writer.py         # 3-stage story generator
├── merge.py                # Manual content merger
└── run.py                  # Full automation pipeline
```

## LLM Backends

| Backend | Cost | Setup |
|---------|------|-------|
| Ollama | Free | Install from ollama.ai |
| Claude | Paid | API key from console.anthropic.com |
| Mock | Free | Built-in, for testing |

## License

MIT
