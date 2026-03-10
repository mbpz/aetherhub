"""ISMP 协议测试"""
import pytest
from aetherhub.ismp.protocol import ISMPProtocol
from aetherhub.codex.engine import CodexEngine
from aetherhub.verification.z3_verifier import Z3Verifier


@pytest.fixture
def codex():
    return CodexEngine()


@pytest.fixture
def z3():
    return Z3Verifier()


@pytest.fixture
def ismp(codex, z3):
    return ISMPProtocol(codex, None, z3)


class TestISMP:
    def test_semantic_vectorization(self, ismp):
        """测试语义向量化"""
        intent = "将 /data/users.csv 导出"
        vector = ismp.semantic_vectorization(intent)

        assert vector["verb"] == "write"
        assert vector["object"] == "file"
        assert vector["target"] == "/data/users.csv"

    def test_capability_mapping(self, ismp):
        """测试能力空间匹配"""
        vector = {"verb": "write", "object": "file", "target": "/tmp/data.txt"}
        skills = ismp.capability_mapping(vector)

        assert "read_file" in skills
        assert "write_file" in skills

    def test_constraint_injection(self, ismp):
        """测试约束注入"""
        vector = {"object": "file", "target": "/etc/passwd"}
        code = "def process(): pass"
        constraints = ismp.dynamic_constraint_injection(vector, code)

        assert "file" in constraints["resource_type"]
        assert len(constraints["rules"]) > 0

    def test_full_process(self, ismp):
        """测试完整流程"""
        intent = "将 /data/users.csv 导出"
        artifact = ismp.process(intent)

        assert artifact["artifact_id"] is not None
        assert len(artifact["atomic_skills"]) > 0
        assert artifact["code"] is not None
        assert artifact["constraints"]["resource_type"] == "file"
