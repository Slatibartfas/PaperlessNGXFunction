Paperless Document Search Tool (Async, Snippet-First)
A powerful OpenWebUI tool for searching, previewing, and extracting content from your Paperless DMS.
Features async requests, snippet-first search to avoid LLM token overload, and configurable parameters via environment or UI.

Features
Snippet-first retrieval: Returns a preview (snippet) of each document, avoiding LLM context/token issues.

View full content on demand: Easily load the full content of any document by its ID.

Fully async: Never blocks the UI, even for large archives.

Highly configurable: Adjust the number and length of snippets returned using simple valves.

Installation
Clone or copy this repository (or script) into your OpenWebUI tools directory.

Install requirements (if not already installed):

bash
Kopieren
Bearbeiten
pip install httpx python-dotenv pydantic
Set environment variables (.env in the tool directory or in your system):

env
Kopieren
Bearbeiten
PAPERLESS_URL=https://paperless.yourdomain.com/
PAPERLESS_TOKEN=your_token_here
SNIPPET_LENGTH=1500
MAX_SNIPPETS=10
Configuration
All major parameters can be set via environment variables, config files, or directly via the OpenWebUI valves panel:

Variable	Description	Default
PAPERLESS_URL	Your Paperless base URL	(required)
PAPERLESS_TOKEN	Your Paperless API token	(required)
SNIPPET_LENGTH	Max chars per snippet (preview)	1500
MAX_SNIPPETS	Max number of snippets per search	10

Usage
1. Search for snippets (previews):

Call the tool’s search_paperless_snippets() function
(either via OpenWebUI, API, or directly in code)

Returns a list of document previews, each with: id, title, created, correspondent, document_type, snippet (preview), and source.

Example output (JSON):

json
Kopieren
Bearbeiten
[
  {
    "id": 123,
    "title": "Invoice May 2024",
    "created": "2024-05-10T08:13:42Z",
    "correspondent": "ACME Corp",
    "document_type": "Invoice",
    "snippet": "Dear customer, your invoice for May ...",
    "source": "https://paperless.yourdomain.com/documents/123"
  },
  ...
]
2. Load full content for a specific document:

Call the tool’s get_paperless_document_full(document_id=...) function.

Returns the entire content and metadata for the document.

Example (Python)
python
Kopieren
Bearbeiten
from tools.paperless_tool import Tools

tools = Tools()

# Search for up to 10 document previews (snippets up to 1500 chars)
results_json = await tools.search_paperless_snippets(documentTypeName="Invoice")

# Load full content for document with ID 123
full_doc_json = await tools.get_paperless_document_full(document_id=123)
Tips
Adjust SNIPPET_LENGTH and MAX_SNIPPETS to fine-tune performance and LLM compatibility.

For very large Paperless archives, keep MAX_SNIPPETS low to avoid UI/model overload.

Snippet search is ideal for chat-driven "Find my ..." use cases; full text is only loaded when the user requests it.

License
MIT

Credits
Original author: Jonas Leine

Optimization & OpenWebUI adaptation: Alexander Klingspor

Contributing
PRs welcome! If you add new features (e.g., filtering by more Paperless fields, fuzzy search, better metadata, etc.), please open an issue or pull request.

