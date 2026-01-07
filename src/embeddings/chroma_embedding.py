from chromadb.api.types import EmbeddingFunction
from src.embeddings.embedding_manager import get_embedding_model


class SentenceTransformerEmbedding(EmbeddingFunction):
    def __init__(self):
        self.model = get_embedding_model()

    def __call__(self, texts):
        return self.model.encode(texts).tolist()

    def name(self) -> str:
        return "sentence-transformer-embedding"
