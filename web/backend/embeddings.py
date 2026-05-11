"""
向量嵌入服务 - 使用 sentence-transformers 生成技能 embedding
"""
import os
import numpy as np

# embedding dimension for bge-base-en-v1.5
EMBEDDING_DIM = 768


class EmbeddingService:
    """轻量级嵌入服务，支持通过 EMBEDDING_MODEL env var 配置模型"""

    _model = None

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        # Only load model once (on first instance)
        if EmbeddingService._model is None:
            self._load_model()

    @property
    def model_name(self) -> str:
        return self._model_name

    def _load_model(self):
        """延迟加载模型"""
        if EmbeddingService._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # Use the configured model name
                EmbeddingService._model = SentenceTransformer(self._model_name)
            except ImportError:
                EmbeddingService._model = None
        return EmbeddingService._model

    def encode(self, texts) -> np.ndarray:
        """生成文本嵌入向量"""
        model = self._load_model()
        if model is None:
            # Fallback: 返回随机向量用于测试
            if isinstance(texts, str):
                return np.random.randn(EMBEDDING_DIM).astype(np.float32)
            return np.random.randn(len(texts), EMBEDDING_DIM).astype(np.float32)
        return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    def compute_similarity(self, embedding1: bytes, embedding2: bytes) -> float:
        """计算两个嵌入向量的余弦相似度"""
        vec1 = np.frombuffer(embedding1, dtype=np.float32)
        vec2 = np.frombuffer(embedding2, dtype=np.float32)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))


_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service (lazy initialization, respects EMBEDDING_MODEL env var)"""
    global _embedding_service
    if _embedding_service is None:
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        _embedding_service = EmbeddingService(model_name)
    return _embedding_service


def get_embedding(text: str) -> list:
    """Convenience wrapper: encode a single text string"""
    return get_embedding_service().encode(text)


def text_to_embedding(text: str) -> bytes:
    """将文本转换为 embedding bytes"""
    service = get_embedding_service()
    vec = service.encode(text)
    return vec.tobytes()


def cosine_similarity(vec1: bytes, vec2: bytes) -> float:
    """计算两个 embedding 向量的余弦相似度"""
    v1 = np.frombuffer(vec1, dtype=np.float32)
    v2 = np.frombuffer(vec2, dtype=np.float32)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))


def rrf_fusion(results_by_source: list, k: int = 60) -> list:
    """
    Reciprocal Rank Fusion - 合并多个排序结果

    Args:
        results_by_source: 每个源的排序 ID 列表
        k: RRF 公式的常量参数

    Returns:
        融合后的排序列表
    """
    scores = {}
    for results in results_by_source:
        for rank, item_id in enumerate(results):
            # item_id is (skill_id, score) tuple
            if isinstance(item_id, tuple):
                item_id = item_id[0]
            if item_id not in scores:
                scores[item_id] = 0.0
            scores[item_id] += 1.0 / (k + rank + 1)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
