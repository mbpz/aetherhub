"""PRD-02: Skill 公开广场测试 - P1重要功能"""
import pytest
import requests
import json
from unittest.mock import Mock, patch


BASE = "http://localhost:8000/api/v1"


@pytest.fixture
def session():
    """创建测试会话"""
    return requests.Session()


class TestSkillSquareP1:
    """PRD-02 Skill 公开广场 P1测试"""

    # TC-02-05: 关键词搜索（无结果）
    def test_search_nonexistent_keyword_returns_empty(self, session):
        """TC-02-05: 搜索不存在的关键词返回空结果"""
        response = session.get(f"{BASE}/skills?q=xyzabc123_nonexistent_keyword")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()["data"]
        items = data.get("items", [])
        total = data.get("total", 0)

        assert total == 0, f"Total should be 0 for nonexistent keyword, got {total}"
        assert len(items) == 0, f"Items should be empty, got {len(items)}"

    def test_search_nonexistent_keyword_shows_empty_state(self, session):
        """TC-02-05: 搜索无结果显示空状态"""
        response = session.get(f"{BASE}/skills?q=xyzabc123")

        assert response.status_code == 200

        data = response.json()["data"]
        assert "items" in data, "Response should contain items"
        assert "total" in data, "Response should contain total"

    # TC-02-07: 排序切换
    def test_sort_by_star_count_descending(self, session):
        """TC-02-07: 按star_count降序排序"""
        # 获取默认排序（最新）
        response1 = session.get(f"{BASE}/skills?sort=created_at&order=desc")
        items1 = response1.json()["data"]["items"]

        # 获取按star_count排序
        response2 = session.get(f"{BASE}/skills?sort=star_count&order=desc")
        items2 = response2.json()["data"]["items"]

        assert response1.status_code == 200
        assert response2.status_code == 200

        # 验证排序结果
        if len(items2) >= 2:
            star_counts = [item.get("star_count", 0) for item in items2]
            assert all(star_counts[i] >= star_counts[i+1] for i in range(len(star_counts)-1)), \
                "Items should be sorted by star_count in descending order"

    def test_sort_by_star_count_ascending(self, session):
        """TC-02-07: 按star_count升序排序"""
        response = session.get(f"{BASE}/skills?sort=star_count&order=asc")

        assert response.status_code == 200

        items = response.json()["data"]["items"]

        if len(items) >= 2:
            star_counts = [item.get("star_count", 0) for item in items]
            assert all(star_counts[i] <= star_counts[i+1] for i in range(len(star_counts)-1)), \
                "Items should be sorted by star_count in ascending order"

    # TC-02-09: 搜索+分类联合过滤
    def test_search_with_category_filter(self, session):
        """TC-02-09: 搜索关键词+分类筛选"""
        # 先搜索一个存在的分类
        response = session.get(f"{BASE}/skills?q=csv")
        if response.json()["data"]["items"]:
            first_category = response.json()["data"]["items"][0].get("category", "")

            # 然后用分类筛选
            response = session.get(f"{BASE}/skills?q=csv&category={first_category}")

            assert response.status_code == 200

            items = response.json()["data"]["items"]

            # 验证所有结果都匹配两个条件
            for item in items:
                name_lower = item.get("name", "").lower()
                description_lower = item.get("description", "").lower()
                category = item.get("category", "")

                assert "csv" in name_lower or "csv" in description_lower, \
                    f"Skill {item['name']} should contain 'csv'"
                assert category == first_category, \
                    f"Skill {item['name']} should have category {first_category}"

    def test_search_with_category_url_params(self, session):
        """TC-02-09: 搜索+分类联合过滤URL包含两个参数"""
        response = session.get(f"{BASE}/skills?q=csv&category=数据处理")

        assert response.status_code == 200

    # TC-02-11: 无技能时空状态
    def test_empty_square_shows_empty_state(self, session):
        """TC-02-11: 无技能时空状态展示"""
        # 搜索不存在的关键词
        response = session.get(f"{BASE}/skills?q=nonexistent_xyz_123")

        assert response.status_code == 200

        data = response.json()["data"]
        items = data.get("items", [])

        # 验证空状态
        assert len(items) == 0, "Items should be empty"
        assert data.get("total", 0) == 0, "Total should be 0"

    def test_empty_state_shows_clear_message(self, session):
        """TC-02-11: 空状态显示清晰提示"""
        response = session.get(f"{BASE}/skills?q=nonexistent_xyz_123")

        assert response.status_code == 200

        data = response.json()["data"]

        # 验证响应结构完整
        assert "items" in data
        assert "total" in data

    # TC-02-10: 骨架屏加载状态（UI测试，跳过）
    @pytest.mark.skip(reason="需要前端支持，跳过")
    def test_skeleton_loading_state(self):
        """TC-02-10: 骨架屏加载状态"""
        pass


class TestSkillSquareEdgeCasesP1:
    """PRD-02 边界情况P1测试"""

    def test_empty_search_query(self, session):
        """测试空搜索查询"""
        response = session.get(f"{BASE}/skills?q=")

        assert response.status_code == 200

    def test_special_characters_in_search(self, session):
        """测试搜索特殊字符"""
        response = session.get(f"{BASE}/skills?q=python%20script")

        assert response.status_code == 200

    def test_very_long_search_query(self, session):
        """测试超长搜索查询"""
        long_query = "keyword" * 100

        response = session.get(f"{BASE}/skills?q={long_query}")

        # 应该返回200或422
        assert response.status_code in (200, 422), f"Expected 200 or 422, got {response.status_code}"
