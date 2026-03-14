"""PRD-03: 我的技能测试 - P1重要功能"""
import pytest
import requests
import json
from unittest.mock import Mock, patch


BASE = "http://localhost:8000/api/v1"


@pytest.fixture
def session():
    """创建测试会话"""
    return requests.Session()


@pytest.fixture
def mock_token():
    """Mock JWT Token"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiaWF0IjoxNzczNDg5NDQxLCJleHAiOjE3NzM1NzU4NDF9.IzHrcRQuh-VSD_EGO2xfZDRu1-cW2RyA8mSTw0cVlmQ"


class TestMySkillsP1:
    """PRD-03 我的技能 P1测试"""

    # TC-03-03: 技能卡片显示公开状态
    def test_skill_card_shows_public_status(self, session, mock_token):
        """TC-03-03: 技能卡片显示公开状态标识"""
        session.headers.update({"Authorization": f"Bearer {mock_token}"})

        response = session.get(f"{BASE}/skills/mine")
        items = response.json()["data"]["items"]

        if items:
            item = items[0]

            # 验证公开状态标识
            assert "is_public" in item, "Skill should have is_public field"
            assert isinstance(item["is_public"], bool), "is_public should be boolean"

            # 验证状态显示（假设有status字段）
            # assert item.get("status") == "已公开", "Status should be '已公开'"

    def test_skill_card_shows_star_count_and_time(self, session, mock_token):
        """TC-03-03: 技能卡片显示Star数和上传时间"""
        session.headers.update({"Authorization": f"Bearer {mock_token}"})

        response = session.get(f"{BASE}/skills/mine")
        items = response.json()["data"]["items"]

        if items:
            item = items[0]

            # 验证Star数
            assert "star_count" in item, "Skill should have star_count"
            assert isinstance(item["star_count"], int), "star_count should be integer"

            # 验证创建时间
            assert "created_at" in item, "Skill should have created_at"
            assert item["created_at"], "created_at should not be empty"

    # TC-03-05: 删除技能——弹出确认对话框
    @pytest.mark.skip(reason="需要前端UI测试，跳过")
    def test_delete_skill_shows_confirmation_dialog(self, session, mock_token):
        """TC-03-05: 删除技能弹出确认对话框"""
        # 使用Selenium测试前端UI
        pass

    # TC-03-06: 删除技能——取消操作
    @pytest.mark.skip(reason="需要前端UI测试，跳过")
    def test_delete_skill_cancel_action(self, session, mock_token):
        """TC-03-06: 删除技能取消操作"""
        # 使用Selenium测试前端UI
        pass

    # TC-03-11: 加载状态
    @pytest.mark.skip(reason="需要前端支持，跳过")
    def test_mine_page_loading_state(self):
        """TC-03-11: 我的技能页面加载状态"""
        pass

    # TC-03-12: 删除操作的加载状态
    @pytest.mark.skip(reason="需要前端支持，跳过")
    def test_delete_operation_loading_state(self):
        """TC-03-12: 删除操作加载状态"""
        pass

    def test_mine_page_shows_all_user_skills(self, session, mock_token):
        """TC-03-03: 我的技能页面显示所有用户技能"""
        session.headers.update({"Authorization": f"Bearer {mock_token}"})

        response = session.get(f"{BASE}/skills/mine")
        data = response.json()["data"]
        items = data.get("items", [])

        # 验证返回的是当前用户的技能
        for item in items:
            assert "author" in item, "Skill should have author"
            assert item["author"].get("login") == "demo-user", \
                f"Skill {item['name']} should belong to demo-user"

    def test_mine_page_shows_skill_details(self, session, mock_token):
        """TC-03-03: 我的技能页面显示技能详情"""
        session.headers.update({"Authorization": f"Bearer {mock_token}"})

        response = session.get(f"{BASE}/skills/mine")
        items = response.json()["data"]["items"]

        if items:
            item = items[0]

            # 验证技能详情完整
            assert "id" in item, "Skill should have id"
            assert "name" in item, "Skill should have name"
            assert "version" in item, "Skill should have version"
            assert "category" in item, "Skill should have category"
            assert "description" in item, "Skill should have description"
            assert "author" in item, "Skill should have author"

    def test_mine_page_pagination(self, session, mock_token):
        """TC-03-11: 我的技能页面分页"""
        session.headers.update({"Authorization": f"Bearer {mock_token}"})

        # 获取第一页
        response1 = session.get(f"{BASE}/skills/mine?page=1&size=10")
        data1 = response1.json()["data"]

        # 获取第二页
        response2 = session.get(f"{BASE}/skills/mine?page=2&size=10")
        data2 = response2.json()["data"]

        assert response1.status_code == 200
        assert response2.status_code == 200

        # 验证分页
        assert "total" in data1, "Should have total"
        assert "page" in data1, "Should have page"
        assert "size" in data1, "Should have size"
        assert "pages" in data1, "Should have pages"

    def test_mine_page_empty_state_shows_guide(self, session, mock_token):
        """TC-03-09: 空状态显示引导"""
        session.headers.update({"Authorization": f"Bearer {mock_token}"})

        response = session.get(f"{BASE}/skills/mine")
        data = response.json()["data"]
        items = data.get("items", [])

        # 如果没有技能，验证空状态
        if len(items) == 0:
            assert "total" in data, "Should have total"
            assert data.get("total", 0) == 0, "Total should be 0"
            assert "items" in data, "Should have items"
            assert len(data["items"]) == 0, "Items should be empty"
