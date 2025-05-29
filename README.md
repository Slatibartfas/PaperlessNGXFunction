# Paperless Document Search Tool (Async, Snippet-First)

A powerful OpenWebUI tool for searching, previewing, and extracting content from your [Paperless](https://github.com/paperless-ngx/paperless-ngx) DMS.  
Features async requests, snippet-first search to avoid LLM token overload, and configurable parameters via environment or UI.

---

## Features

* **Snippet-first retrieval** – returns a preview (snippet) of each document, preventing LLM context/token issues.  
* **View full content on demand** – load the complete text of any document by its ID.  
* **Fully async** – never blocks the UI, even for large archives.  
* **Highly configurable** – adjust the number and length of snippets via simple valves.

---

## Installation

1. Clone or copy this repository (or script) into your OpenWebUI tools directory.  
2. Install requirements (if not already installed):

~~~bash
pip install httpx python-dotenv pydantic
~~~

3. Set environment variables (`.env` in the tool directory or in your system):

~~~env
PAPERLESS_URL=https://paperless.yourdomain.com/
PAPERLESS_TOKEN=your_token_here
SNIPPET_LENGTH=1500
MAX_SNIPPETS=10
~~~

---

## Configuration

| Variable        | Description                                 | Default |
|-----------------|---------------------------------------------|---------|
| `PAPERLESS_URL` | Your Paperless base URL                     | — |
| `PAPERLESS_TOKEN` | Your Paperless API token                  | — |
| `SNIPPET_LENGTH` | Max characters per snippet (preview)       | 1500 |
| `MAX_SNIPPETS`   | Max number of snippets per search          | 10 |

---

## Usage

### 1. Search for snippets (previews)

Call the tool’s `search_paperless_snippets()` function (via OpenWebUI, API, or directly in code).

*Returns a list of document previews containing `id`, `title`, `created`, `correspondent`, `document_type`, `snippet`, and `source`.*

Example response:

~~~json
[
  {
    "id": 123,
    "title": "Invoice May 2024",
    "created": "2024-05-10T08:13:42Z",
    "correspondent": "ACME Corp",
    "document_type": "Invoice",
    "snippet": "Dear customer, your invoice for May …",
    "source": "https://paperless.yourdomain.com/documents/123"
  }
]
~~~

### 2. Load full content for a specific document

Call `get_paperless_document_full(document_id=...)` to receive the entire content and metadata.

---

## Example (Python)

~~~python
from tools.paperless_tool import Tools

tools = Tools()

# Search for up to 10 document previews (snippets up to 1500 chars)
results_json = await tools.search_paperless_snippets(documentTypeName="Invoice")

# Load full content for document with ID 123
full_doc_json = await tools.get_paperless_document_full(document_id=123)
~~~

---

## Tips

* Tune `SNIPPET_LENGTH` and `MAX_SNIPPETS` for optimal performance and LLM compatibility.  
* For very large archives, keep `MAX_SNIPPETS` low to avoid UI/model overload.  
* Snippet search is ideal for “Find my …” use cases; full text is fetched only on request.

---

## License

MIT

---

## Credits

* **Original author:** Jonas Leine  
* **OpenWebUI adaptation & optimisation:** ChatGPT/Alex

---

## Contributing

Pull requests are welcome! If you add features (e.g. extra filters, fuzzy search, richer metadata), please open an issue or PR.
