"""
title: PaperlessNGX Document Search Tool (async, snippet-first, adjustable)
author: Alexander Klingspor, based off Jonas Leine
funding_url: https://github.com/Slatibartfas/PaperlessNGXFunction/
version: 1.4.0
license: MIT
"""
import json
import os
import httpx
from dotenv import load_dotenv
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from pydantic import BaseModel, Field
from typing import Callable, Any, Optional, List, Dict, AsyncIterator

load_dotenv()


def trim_content(content, max_chars):
    if not content:
        return ""
    return content[:max_chars] + ("..." if len(content) > max_chars else "")


class DocumentEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Document):
            return {"page_content": obj.page_content, "metadata": obj.metadata}
        return super().default(obj)


class PaperlessDocumentLoader(BaseLoader):
    """
    Async Paperless document loader that retrieves documents via REST API with optional filters.
    """

    def __init__(self, documentTypeName: Optional[str] = None, documentTagName: Optional[str] = None,
                 correspondent: Optional[str] = None, url: Optional[str] = None,
                 token: Optional[str] = None, created_year: Optional[int] = None,
                 created_month: Optional[int] = None, event_emitter: Callable[[str], Any] = None,
                 max_docs: int = 10, snippet_length: int = 1500) -> None:
        self.url = url.rstrip("/") + "/api/documents/"
        self.token = token or ""
        self.documentTypeName = documentTypeName
        self.documentTagName = documentTagName
        self.correspondent = correspondent
        self.created_year = created_year
        self.created_month = created_month
        self.event_emitter = event_emitter
        self.max_docs = max_docs
        self.snippet_length = snippet_length

    async def lazy_load(self) -> AsyncIterator[dict]:
        """
        Yields dicts with 'id', 'title', 'created', 'correspondent', 'snippet', etc.
        """
        querystring = {}
        if self.documentTypeName:
            querystring["document_type__name__icontains"] = self.documentTypeName
        if self.documentTagName:
            querystring["tags__name__icontains"] = self.documentTagName
        if self.correspondent:
            querystring["correspondent__name__icontains"] = self.correspondent
        if self.created_year:
            querystring["created_year"] = self.created_year
        if self.created_month:
            querystring["created__month"] = self.created_month

        headers = {"Authorization": f"Token {self.token}"}
        next_url = self.url
        total_docs = 0
        page_num = 0

        async with httpx.AsyncClient(timeout=15) as client:
            while next_url and total_docs < self.max_docs:
                try:
                    resp = await client.get(
                        next_url,
                        headers=headers,
                        params=querystring if next_url == self.url else {}
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    if self.event_emitter:
                        await self.event_emitter(f"Error retrieving documents: {e}")
                    break

                docs = data.get('results', [])
                for result in docs:
                    if total_docs >= self.max_docs:
                        break
                    snippet = trim_content(result.get("content", ""), self.snippet_length)
                    docdict = {
                        "id": result["id"],
                        "title": result.get("title", ""),
                        "created": result.get("created", ""),
                        "correspondent": result.get("correspondent", ""),
                        "document_type": result.get("document_type", ""),
                        "snippet": snippet,
                        "source": f"{self.url.replace('/api', '')}{result['id']}",
                    }
                    yield docdict
                    total_docs += 1

                page_num += 1

                if self.event_emitter:
                    await self.event_emitter(
                        f"Loaded page {page_num}, total previewed documents: {total_docs}"
                    )

                next_url = data.get("next")

    async def get_full_content_by_id(self, document_id: int) -> Optional[dict]:
        """
        Loads the full content and metadata for a single document by its ID.
        """
        headers = {"Authorization": f"Token {self.token}"}
        url = self.url + str(document_id) + "/"
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                result = resp.json()
                return {
                    "id": result["id"],
                    "title": result.get("title", ""),
                    "created": result.get("created", ""),
                    "correspondent": result.get("correspondent", ""),
                    "document_type": result.get("document_type", ""),
                    "content": result.get("content", ""),
                    "source": f"{self.url.replace('/api', '')}{result['id']}",
                }
            except Exception as e:
                return {"error": f"Error retrieving document {document_id}: {e}"}


class EventEmitter:
    def __init__(self, event_emitter: Callable[[dict], Any] = None):
        self.event_emitter = event_emitter

    async def progress_update(self, description):
        await self.emit(description)

    async def error_update(self, description):
        await self.emit(description, "error", True)

    async def success_update(self, description):
        await self.emit(description, "success", True)

    async def emit(self, description="Unknown State", status="in_progress", done=False):
        if self.event_emitter:
            await self.event_emitter(
                {"type": "status", "data": {"status": status, "description": description, "done": done}}
            )


class Tools:
    class Valves(BaseModel):
        PAPERLESS_URL: str = Field(
            default="https://paperless.yourdomain.com/",
            description="The domain of your Paperless service",
        )
        PAPERLESS_TOKEN: str = Field(
            default="", description="The token to read docs from Paperless"
        )
        SNIPPET_LENGTH: int = Field(
            default=1500,
            description="The maximum number of characters per document snippet",
        )
        MAX_SNIPPETS: int = Field(
            default=10,
            description="Maximum number of document snippets to show per search",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def search_paperless_snippets(self, documentTypeName: Optional[str] = None,
                                        documentTagName: Optional[str] = None,
                                        correspondent: Optional[str] = None,
                                        created_year: Optional[int] = None,
                                        created_month: Optional[int] = None,
                                        __event_emitter__: Callable[[dict], Any] = None) -> str:
        """
        Search for Paperless documents and return snippet previews with metadata and IDs.
        """
        emitter = EventEmitter(__event_emitter__)

        try:
            await emitter.progress_update("Collecting document previews...")

            loader = PaperlessDocumentLoader(
                documentTypeName=documentTypeName,
                documentTagName=documentTagName,
                correspondent=correspondent,
                url=self.valves.PAPERLESS_URL,
                token=self.valves.PAPERLESS_TOKEN,
                created_month=created_month,
                created_year=created_year,
                event_emitter=(lambda desc: emitter.progress_update(desc)),
                max_docs=self.valves.MAX_SNIPPETS,
                snippet_length=self.valves.SNIPPET_LENGTH,
            )

            results = []
            async for doc in loader.lazy_load():
                results.append(doc)

            if not results:
                msg = "No documents found."
                await emitter.error_update(msg)
                return msg

            await emitter.success_update(
                f"{len(results)} previews loaded. For full text, provide the document ID!"
            )
            return json.dumps(results, ensure_ascii=False)

        except Exception as e:
            msg = f"Error: {e}"
            await emitter.error_update(msg)
            return msg

    async def get_paperless_document_full(self, document_id: int,
                                          __event_emitter__: Callable[[dict], Any] = None) -> str:
        """
        Load the full content of a single document by ID.
        """
        emitter = EventEmitter(__event_emitter__)
        try:
            await emitter.progress_update(f"Loading full text for document {document_id}...")
            loader = PaperlessDocumentLoader(
                url=self.valves.PAPERLESS_URL,
                token=self.valves.PAPERLESS_TOKEN
            )
            doc = await loader.get_full_content_by_id(document_id)
            if doc and "content" in doc:
                await emitter.success_update(f"Full text loaded: {doc['title']}")
                return json.dumps(doc, ensure_ascii=False)
            else:
                msg = doc.get("error", f"No document found for ID {document_id}")
                await emitter.error_update(msg)
                return msg
        except Exception as e:
            msg = f"Error: {e}"
            await emitter.error_update(msg)
            return msg

if __name__ == '__main__':
    print("Paperless async snippet tool loaded. Run via OpenWebUI or your async environment.")
