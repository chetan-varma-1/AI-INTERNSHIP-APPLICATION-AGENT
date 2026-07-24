""" Semantic search over indexed internships"""

from __future__ import annotations

from typing import Any

from rag.config import RAGConfig
from rag.embedding_service import EmbeddingService, OllamaEmbeddingService
from models.rag_models import InternshipJob,SearchResult
from rag.vector_store import ChromaVectorStore, VectorStore

class InternshipRetriever:
    """Embeds queries and retrieves match internship listings."""
    def __init__(
            self,
            config: RAGConfig | None = None, 
            embedding_service: EmbeddingService | None = None,
            vector_store: VectorStore | None = None,
    ) -> None:
        self._config = config or RAGConfig()
        self._embeddings = embedding_service or OllamaEmbeddingService(self._config)
        self._store = vector_store or ChromaVectorStore(self._config)

    def search(
            self,
            query: str,
            top_k: int | None = None,
            filters: dict[str, str] | None = None,
    ) -> list[SearchResult]:
        """Return top-k internships semantically similar to the query"""
        k = top_k or self._config.default_top_k
        query_vector = self._embeddings.embed_query(query)
        raw = self._store.similarity_search(query_vector,k,where=filters)
        return self._parse_results(raw) 

    def search_by_skills(self, skills: list[str], top_k: int | None = None ) -> list[SearchResult]:
        """Search internships metioning specific skills."""
        query = f"Internship required skills: {','.join(skills)}" 
        return self.search(query, top_k=top_k)

    def search_by_location(self, location: str, top_k: int | None = None ) -> list[SearchResult]:
            """Search internships metioning specific location."""
            
            return self.search(query= f"Internship in {location}", top_k=top_k)

    def _parse_results(self,raw:dict[str, Any]) -> list[SearchResult]:
         ids = raw.get("ids", [[]])[0]
         documents = raw.get("documents", [[]])[0]
         metadatas = raw.get("metadatas", [[]])[0]
         distances = raw.get("distances",[[]])[0] 
         results: list[SearchResult] = []
         for job_id, doc, meta, distance in zip(ids, documents, metadatas, distances):
              metadata = {k:str(v) for k,v in (meta or {}).items()}
              job = _metadata_to_job(metadata) if metadata else None
              results.append(
                   SearchResult(
                        job_id=job_id,
                        score =1.0 - float(distance),
                        document=doc or " ",
                        metadata=metadata,
                        job=job,
                )
              )
         return results




def _metadata_to_job(metadata:dict[str,str]) -> InternshipJob:
     skills = [s.strip() for s in metadata.get("skills"," ").split(",")]
     return InternshipJob(
          title=metadata.get("title"," "),
          company=metadata.get("company"," "),
          description=metadata.get("description"," "),
          skills_required=skills,
          location=metadata.get("location"," "),
          apply_url=metadata.get("apply_url"," "),
          source=metadata.get("source"," "),
          job_type=metadata.get("job_type"," "),
          stipend=metadata.get("job_type"," "),
          duration=metadata.get("duration"," "),
     )
     
     