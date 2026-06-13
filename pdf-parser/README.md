# uok-doc-parser

Structured document parsing service based on [Docling](https://github.com/DS4SD/docling) (IBM).

Converts PDF, DOCX, PPTX, HTML, Markdown files into structured sections with headings, content types, and document metadata. Used by `uok-be` file-processing pipeline for smart syllabus assets.

## API

### `POST /parse`

Parses a document and returns structured output.

**Request:** `multipart/form-data`
- `file` — binary file
- `mimetype` — MIME type (e.g. `application/pdf`)

**Response:**
```json
{
  "markdown": "# Chapter 1\n\n## 1.1 Introduction\n...",
  "sections": [
    {
      "heading": "1.1 Introduction",
      "heading_level": 2,
      "section_path": "Chapter 1 > 1.1 Introduction",
      "content": "...",
      "content_type": "paragraph"
    }
  ],
  "metadata": {
    "title": "...",
    "author": "...",
    "page_count": 42,
    "has_tables": true,
    "has_figures": false
  }
}
```

### `GET /health`

Returns `200 OK` when Docling models are loaded and the service is ready.

## Running locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## Docker

```bash
docker build -t uok-doc-parser .
docker run -p 8002:8002 --memory 4g uok-doc-parser
```

Note: First build downloads Docling models (~2GB). Subsequent builds use the Docker cache.

## Configuration in uok-be

Set `DOC_PARSER_URL=http://localhost:8002` in `uok-be/.env`.

In Docker Compose the service name is `doc-parser` and the URL is `http://doc-parser:8002`.
