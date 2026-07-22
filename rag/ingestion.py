"""Ingest internship listings into the vector store."""

from __future__ import annotations

import logging
from typing import Protocol

from Scapper.mock_scapper import MockScraper
from rag.config import RAGConfig
from rag.embedding_service import EmbeddingService, OllamaEmbeddingService
from models.rag_models import InternshipJob
from rag.vector_store import ChromaVectorStore, VectorStore

logger = logging.getLogger(__name__)

BATCH_SIZE = 32

class JobSource(Protocol):
    """Any scaraper that returns raw job dictionaries."""

    def scrape(self) -> list[dict]: ...

class IngestionPipeline:
    """ loads jobs, embeds them, and persists to ChromDB"""

    def __init__(
            self,
            config: RAGConfig | None = None,
            job_source: JobSource | None = None,
            embedding_service: EmbeddingService | None = None,
            vector_store: VectorStore | None = None,
    ) -> None:
        self._config = config or RAGConfig()
        self._job_source = job_source or MockScraper()
        self._embeddings = embedding_service or OllamaEmbeddingService()
        self._store = vector_store or ChromaVectorStore(self._config)

    def run(self, *,reset: bool = False) -> int:
        """Ingest all jobs. Returns number of numbers indexed."""
        jobs = self._load_jobs()
        if not jobs:
            logger.warning("No internship jobs found to ingest.")
            return 0
        
        if reset: 
            self._store.reset()

        indexed = 0
        for batch in _chunk(jobs, BATCH_SIZE):
            ids = [job.document_id for job in batch]
            documents = [job.to_document_text() for job in batch]
            metadatas = [job.to_metadata() for job in batch]
            embeddings = self._embeddings.embed_documents(documents)
            self._store.upsert(ids, embeddings, documents, metadatas)
            indexed += len(batch)
            logger.info("Indexed %s /  %s internshps",indexed, len(jobs))
        
        return indexed

    def _load_jobs(self):
        pass

def _chunk()-> None:
    pass