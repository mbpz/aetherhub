"""PRD-03: 我的技能测试 - P1重要功能"""
import pytest
import requests
import json
from urllib.parse import urlparse, parse_qs


BASE = "http://localhost:8000/api/v1"


def get_live_token():
    """获取有效的真实 token"""
    s = requests.Session()
    r = s.get(f"{BASE}/auth/login")
    auth_url = r.json()["data"]["auth_url"]
    r2 = s.get(auth_url, allow_redirects=False)
    location = r2.headers.get("location", "")
    params = parse_qs(urlparse(location).query)
    return params.get("token", [None])[0]


@pytest.fixture
def live_token():
    """获取有效的真实 token"""
    token = get_live_token()
    if not token:
        pytest.fail("Failed to obtain live token from mock-callback")
    return token


@pytest.fixture
def auth_headers(live_token):
    return {"Authorization": f"Bearer {live_token}"}


class TestMySkillsP1:
    """PRD-03 我的技能 P1测试"""

    # TC-03-03: 技能卡片显示公开状态
    def test_skill_card_shows_public_status(self, auth_headers):
        """TC-03-03: 技能卡片显示公开状态标识"""
        response = requests.get(f"{BASE}/skills/mine", headers=auth_headers)
        items = response.json()["data"]["items"]

        if items:
            item = items[0]
            assert "is_public" in item, "Skill should have is_public field"
            assert isinstance(item["is_public"], bool), "is_public should be boolean"

    def test_skill_card_shows_star_count_and_time(self, auth_headers):
        """TC-03-03: 技能卡片显示Star数和上传时间"""
        response = requests.get(f"{BASE}/skills/mine", headers=auth_headers)
        items = response.json()["data"]["items"]

        if items:
            item = items[0]
            assert "star_count" in item, "Skill should have star_count"
            assert isinstance(item["star_count"], int), "star_count should be integer"
            assert "created_at" in item, "Skill should have created_at"
            assert item["created_at"], "created_at should not be empty"

    # TC-03-05/06: 删除确认对话框/取消操作 → 跳过（前端UI测试）
    # TC-03-11/12: 加载状态 → 跳过（前端UI测试）

    def test_mine_page_shows_all_user_skills(self, auth_headers):
        """TC-03-03: 我的技能页面显示所有用户技能"""
        response = requests.get(f"{BASE}/skills/mine", headers=auth_headers)
        data = response.json()["data"]
        items = data.get("items", [])

        # 验证返回的是当前用户的技能
        for item in items:
            assert "author" in item, "Skill should have author"
            assert item["author"].get("login") in ("demo-user", "octocat"), \
                f"Skill {item['name']} should belong to demo-user or octocat"

    def test_mine_page_shows_skill_details(self, auth_headers):
        """TC-03-03: 我的技能页面显示技能详情"""
        response = requests.get(f"{BASE}/skills/mine", headers=auth_headers)
        items = response.json()["data"]["items"]

        if items:
            item = items[0]
            assert "id" in item, "Skill should have id"
            assert "name" in item, "Skill should have name"
            assert "version" in item, "Skill should have version"
            assert "category" in item, "Skill should have category"
            assert "description" in item, "Skill should have description"
            assert "author" in item, "Skill should have author"

    def test_mine_page_pagination(self, auth_headers):
        """TC-03-11: 我的技能页面分页"""
        # 获取第一页
        response1 = requests.get(f"{BASE}/skills/mine?page=1&size=10", headers=auth_headers)
        data1 = response1.json()["data"]

        # 获取第二页
        response2 = requests.get(f"{BASE}/skills/mine?page=2&size=10", headers=auth_headers)
        data2 = response2.json()["data"]

        assert response1.status_code == 200
        assert response2.status_code == 200

        # 验证分页字段
        assert "total" in data1, "Should have total"
        assert "page" in data1, "Should have page"
        assert "size" in data1, "Should have size"
        assert "pages" in data1, "Should have pages"

    def test_mine_page_empty_state_shows_guide(self, auth_headers):
        """TC-03-09: 空状态显示引导（验证空列表结构）"""
        response = requests.get(f"{BASE}/skills/mine", headers=auth_headers)
        data = response.json()["data"]
        items = data.get("items", [])

        # 验证空状态结构
        assert "total" in data, "Should have total"
        assert "items" in data, "Should have items"
        assert isinstance(data["items"], list), "Items should be a list"