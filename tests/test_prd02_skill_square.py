"""PRD-02: Skill 公开广场测试 - P0核心功能"""
import pytest
import requests
import json
from unittest.mock import Mock, patch


BASE = "http://localhost:8000/api/v1"


@pytest.fixture
def session():
    """创建测试会话"""
    return requests.Session()


class TestSkillSquare:
    """PRD-02 Skill 公开广场测试"""

    # TC-02-01: 首页默认展示技能列表
    def test_get_skills_returns_list(self, session):
        """TC-02-01: GET /skills 返回技能列表"""
        response = session.get(f"{BASE}/skills")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()["code"] == 0, f"Expected code 0, got {response.json().get('code')}"

        data = response.json()["data"]
        assert "items" in data, "Response should contain items"
        assert "total" in data, "Response should contain total"

    def test_skills_list_is_public_no_login_required(self, session):
        """TC-02-01: 技能列表无需登录即可访问"""
        response = session.get(f"{BASE}/skills")

        assert response.status_code == 200, "Should be accessible without login"

    def test_skills_list_shows_skill_cards(self, session):
        """TC-02-01: 技能列表展示技能卡片"""
        response = session.get(f"{BASE}/skills")
        items = response.json()["data"]["items"]

        if items:
            item = items[0]
            # 验证技能卡片包含必要字段
            assert "id" in item, "Skill should have id"
            assert "name" in item, "Skill should have name"
            assert "version" in item, "Skill should have version"
            assert "category" in item, "Skill should have category"
            assert "description" in item, "Skill should have description"
            assert "author" in item, "Skill should have author"

    # TC-02-02: 技能卡片信息完整性
    def test_skill_card_has_complete_info(self, session):
        """TC-02-02: 技能卡片信息完整性"""
        response = session.get(f"{BASE}/skills")
        items = response.json()["data"]["items"]

        if items:
            item = items[0]

            # 验证版本号格式
            import re
            version = item.get("version", "")
            assert re.match(r"^\d+\.\d+\.\d+$", version), f"Version {version} should match x.y.z format"

            # 验证作者信息
            author = item.get("author", {})
            assert "login" in author, "Author should have login"
            assert "avatar_url" in author, "Author should have avatar_url"

    def test_skill_description_truncated(self, session):
        """TC-02-02: 技能描述截断显示"""
        response = session.get(f"{BASE}/skills")
        items = response.json()["data"]["items"]

        if items:
            item = items[0]
            description = item.get("description", "")

            # 描述应该有合理长度（不是太长）
            assert len(description) < 500, f"Description should be truncated, got {len(description)} chars"

    def test_skill_tags_display(self, session):
        """TC-02-02: 技能标签显示"""
        response = session.get(f"{BASE}/skills")
        items = response.json()["data"]["items"]

        if items:
            item = items[0]
            tags = item.get("tags", [])

            # 标签应该是列表
            assert isinstance(tags, list), "Tags should be a list"

            # 如果有标签，验证标签内容
            if tags:
                for tag in tags:
                    assert isinstance(tag, str), "Each tag should be a string"

    def test_skill_card_shows_star_count(self, session):
        """TC-02-02: 技能卡片显示Star数"""
        response = session.get(f"{BASE}/skills")
        items = response.json()["data"]["items"]

        if items:
            item = items[0]
            star_count = item.get("star_count", 0)

            assert isinstance(star_count, int), "Star count should be an integer"
            assert star_count >= 0, "Star count should be non-negative"

    def test_skill_card_shows_relative_time(self, session):
        """TC-02-02: 技能卡片显示相对时间"""
        response = session.get(f"{BASE}/skills")
        items = response.json()["data"]["items"]

        if items:
            item = items[0]
            created_at = item.get("created_at", "")

            # created_at应该是ISO格式时间
            assert created_at, "created_at should not be empty"
            # 可以验证是有效的ISO时间字符串
            import re
            assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", created_at), "created_at should be in ISO format"

    # TC-02-03: 点击卡片跳转详情页
    def test_skill_card_click_redirects_to_detail(self, session):
        """TC-02-03: 技能卡片跳转至详情页"""
        response = session.get(f"{BASE}/skills")
        items = response.json()["data"]["items"]

        if items:
            skill_id = items[0]["id"]
            # 模拟点击卡片
            detail_response = session.get(f"{BASE}/skills/{skill_id}")

            assert detail_response.status_code == 200, f"Should access skill detail page, got {detail_response.status_code}"

    def test_skill_detail_url_contains_id(self, session):
        """TC-02-03: 详情页URL包含技能ID"""
        response = session.get(f"{BASE}/skills")
        items = response.json()["data"]["items"]

        if items:
            skill_id = items[0]["id"]
            # 访问详情页
            detail_response = session.get(f"{BASE}/skills/{skill_id}")

            # 响应应该成功
            assert detail_response.status_code == 200

    # TC-02-04: 关键词搜索（有结果）
    def test_search_skills_with_matching_keyword(self, session):
        """TC-02-04: 关键词搜索返回匹配结果"""
        # 先搜索一个存在的关键词（如"csv"）
        response = session.get(f"{BASE}/skills?q=csv")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()["data"]
        items = data.get("items", [])

        # 验证所有结果都包含关键词
        for item in items:
            name_lower = item.get("name", "").lower()
            description_lower = item.get("description", "").lower()
            assert "csv" in name_lower or "csv" in description_lower, \
                f"Skill {item['name']} should contain 'csv' in name or description"

    def test_search_url_updates_with_query(self, session):
        """TC-02-04: 搜索后URL更新"""
        response = session.get(f"{BASE}/skills?q=csv")
        assert response.status_code == 200

    def test_search_shows_filtered_count(self, session):
        """TC-02-04: 搜索显示过滤后的数量"""
        response = session.get(f"{BASE}/skills?q=csv")

        data = response.json()["data"]
        total = data.get("total", 0)

        assert total >= 0, "Total should be non-negative"
        assert total == len(data.get("items", [])), "Total should match number of items"

    # TC-02-06: 分类筛选
    def test_filter_by_category(self, session):
        """TC-02-06: 按分类筛选"""
        # 搜索一个存在的分类（如"数据处理"）
        response = session.get(f"{BASE}/skills?q=数据处理")

        if response.json()["data"]["items"]:
            first_category = response.json()["data"]["items"][0].get("category", "")

            # 用这个分类筛选
            filtered_response = session.get(f"{BASE}/skills?category={first_category}")

            assert filtered_response.status_code == 200, f"Expected 200, got {filtered_response.status_code}"

            filtered_items = filtered_response.json()["data"]["items"]

            # 验证所有结果都是这个分类
            for item in filtered_items:
                assert item.get("category") == first_category, \
                    f"Skill {item['name']} should have category {first_category}"

    def test_category_filter_url_updates(self, session):
        """TC-02-06: 分类筛选URL更新"""
        response = session.get(f"{BASE}/skills?category=数据处理")

        assert response.status_code == 200

    # TC-02-08: 分页功能
    def test_pagination_with_page_and_size(self, session):
        """TC-02-08: 分页功能"""
        # 获取第一页
        response1 = session.get(f"{BASE}/skills?page=1&size=10")
        items1 = response1.json()["data"]["items"]
        total1 = response1.json()["data"]["total"]

        # 获取第二页
        response2 = session.get(f"{BASE}/skills?page=2&size=10")
        items2 = response2.json()["data"]["items"]

        assert response1.status_code == 200, "First page should succeed"
        assert response2.status_code == 200, "Second page should succeed"

        # 验证分页参数
        if total1 > 10:
            # 验证两页内容不重叠
            ids1 = {item["id"] for item in items1}
            ids2 = {item["id"] for item in items2}
            assert ids1.isdisjoint(ids2), "Pages should not overlap"

    def test_pagination_url_updates(self, session):
        """TC-02-08: 分页URL更新"""
        response = session.get(f"{BASE}/skills?page=2&size=20")

        assert response.status_code == 200

    def test_pagination_shows_total_pages(self, session):
        """TC-02-08: 分页显示总页数"""
        response = session.get(f"{BASE}/skills?page=1&size=20")

        data = response.json()["data"]
        pages = data.get("pages", 0)

        assert pages >= 1, "Should have at least 1 page"
        assert pages == (data["total"] + 19) // 20, "Pages should be calculated correctly"


class TestSkillSquareEdgeCases:
    """PRD-02 边界情况测试"""

    def test_empty_skills_list(self, session):
        """TC-02-11: 无技能时空状态"""
        # 搜索不存在的关键词
        response = session.get(f"{BASE}/skills?q=nonexistent_xyz_123")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()["data"]
        items = data.get("items", [])
        total = data.get("total", 0)

        assert total == 0, "Total should be 0"
        assert len(items) == 0, "Items should be empty"

    def test_invalid_page_number(self, session):
        """测试无效页码"""
        response = session.get(f"{BASE}/skills?page=9999&size=10")

        # 应该返回200，但items为空
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()["data"]
        assert data.get("items", []) == [], "Invalid page should return empty items"

    def test_too_large_page_size(self, session):
        """测试过大的每页大小"""
        # 某些实现可能限制最大size
        response = session.get(f"{BASE}/skills?page=1&size=1000")

        # 应该返回200或422
        assert response.status_code in (200, 422), f"Expected 200 or 422, got {response.status_code}"
