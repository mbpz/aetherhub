"""
向量嵌入服务 - 使用 sentence-transformers 生成技能 embedding
"""
import os
import numpy as np

# embedding dimension for bge-base-en-v1.5
EMBEDDING_DIM = 768


class EmbeddingService:
    """轻量级嵌入服务，使用 CPU-optimized 模型"""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_model(self):
        """延迟加载模型"""
        if EmbeddingService._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # 使用轻量级 CPU 模型
                EmbeddingService._model = SentenceTransformer("all-MiniLM-L6-v2")
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


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


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
