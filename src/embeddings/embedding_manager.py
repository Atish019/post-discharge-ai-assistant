from sentence_transformers import SentenceTransformer
from config.settings import settings

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model
