from typing import List, Dict
import os
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import RAGChunk, Scene
from app.config import get_settings

settings = get_settings()


class RAGService:
    """Service for RAG (Retrieval Augmented Generation) with FAISS"""

    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.index: faiss.IndexFlatIP
        self.metadata_path = f"{settings.FAISS_INDEX_PATH}_metadata.json"
        self.index_path = f"{settings.FAISS_INDEX_PATH}.bin"
        self.chunk_metadata: List[dict] = []
        self._load_or_create_index()

    def _load_or_create_index(self) -> None:
        """Load existing FAISS index or create new one"""
        os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH) or ".", exist_ok=True)

        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            # Load existing index
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path) as f:
                self.chunk_metadata = json.load(f)
        else:
            # Create new index (768-dim for all-MiniLM-L6-v2)
            self.index = faiss.IndexFlatIP(384)  # Inner product similarity
            self.chunk_metadata = []

    def _save_index(self) -> None:
        """Persist FAISS index and metadata to disk"""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "w") as f:
            json.dump(self.chunk_metadata, f)

    def _chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks (by token count approximation)"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    def embed_text(self, text: str) -> np.ndarray:
        """Embed text to 384-dim vector"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype("float32")

    async def index_scene(self, scene: Scene, db: AsyncSession) -> None:
        """
        Index a scene by chunking its content and adding embeddings to FAISS.
        Also stores chunks in DB for retrieval mapping.
        """
        # Remove old chunks for this scene
        from sqlalchemy import delete
        await db.execute(
            delete(RAGChunk).where(
                (RAGChunk.source_id == scene.id) &
                (RAGChunk.source_type == "scene")
            )
        )

        chunks = self._chunk_text(f"{scene.title or ''}\n{scene.content}")
        embeddings = np.array(
            [self.embed_text(chunk) for chunk in chunks], dtype="float32"
        )

        # Add to FAISS index
        for i, chunk in enumerate(chunks):
            faiss_idx = self.index.ntotal
            self.index.add(embeddings[i : i + 1])

            # Store metadata
            metadata = {
                "id": f"{scene.id}_{i}",
                "story_id": scene.story_id,
                "source_id": scene.id,
                "source_type": "scene",
                "text": chunk,
                "faiss_index": faiss_idx,
            }
            self.chunk_metadata.append(metadata)

            # Store in DB
            rag_chunk = RAGChunk(
                id=metadata["id"],
                story_id=scene.story_id,
                source_id=scene.id,
                source_type="scene",
                chunk_text=chunk,
                faiss_index=faiss_idx,
            )
            db.add(rag_chunk)

        await db.commit()
        self._save_index()

    async def retrieve(
        self,
        query: str,
        story_id: str,
        top_k: int = 5,
    ) -> List[str]:
        """
        Retrieve top-k relevant chunks for a query, filtered by story_id.
        """
        query_embedding = self.embed_text(query)
        query_embedding = query_embedding.reshape(1, -1)

        # Search in FAISS
        distances, indices = self.index.search(query_embedding, top_k * 2)

        # Filter by story_id and deduplicate
        results = []
        seen_sources = set()
        for idx in indices[0]:
            if idx >= len(self.chunk_metadata):
                continue

            metadata = self.chunk_metadata[idx]
            if metadata["story_id"] == story_id:
                source = metadata["source_id"]
                if source not in seen_sources:
                    results.append(metadata["text"])
                    seen_sources.add(source)
                    if len(results) >= top_k:
                        break

        return results

    async def reindex_story(self, story_id: str, db: AsyncSession) -> None:
        """
        Reindex all scenes in a story (called after major changes).
        """
        result = await db.execute(
            select(Scene).filter(Scene.story_id == story_id)
        )
        scenes = result.scalars().all()

        for scene in scenes:
            await self.index_scene(scene, db)
