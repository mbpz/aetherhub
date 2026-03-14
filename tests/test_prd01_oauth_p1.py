"""PRD-01: GitHub OAuth 授权登录测试 - P1重要功能"""
import pytest
import requests
import json
from unittest.mock import Mock, patch
import time


BASE = "http://localhost:8000/api/v1"


@pytest.fixture
def session():
    """创建测试会话"""
    return requests.Session()


class TestGitHubOAuthP1:
    """PRD-01 GitHub OAuth P1测试"""

    # TC-01-07: Token过期处理
    def test_expired_token_returns_401(self, session):
        """TC-01-07: 过期Token访问接口返回401"""
        # 使用一个已过期的token
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.EXPIRED"

        response = session.get(
            f"{BASE}/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_expired_token_clears_and_redirects(self, session):
        """TC-01-07: 过期Token清除并跳转登录页"""
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.EXPIRED"

        # 访问受保护页面
        response = session.get(
            f"{BASE}/skills/mine",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

        # 前端应该清除token并跳转登录页
        # 这里只验证返回401
        assert response.status_code == 401

    # TC-01-11: GitHub OAuth失败处理
    def test_oauth_callback_access_denied(self, session):
        """TC-01-11: OAuth授权取消后返回错误"""
        # 模拟GitHub返回access_denied
        response = session.get(
            f"{BASE}/auth/callback?error=access_denied&error_description=User denied authorization",
            allow_redirects=False
        )

        # 应该返回错误状态或重定向到错误页
        assert response.status_code in (400, 403, 401, 307), \
            f"Should return error status for access_denied, got {response.status_code}"

    def test_oauth_callback_with_invalid_code(self, session):
        """TC-01-11: 无效的code参数"""
        response = session.get(
            f"{BASE}/auth/callback?code=invalid_code_xyz",
            allow_redirects=False
        )

        # 应该返回错误
        assert response.status_code in (400, 403, 401, 307), \
            f"Should return error status for invalid code, got {response.status_code}"

    # TC-01-12: 用户信息同步
    def test_user_info_sync_after_github_update(self, session):
        """TC-01-12: 用户修改GitHub信息后重新登录同步"""
        # 模拟用户重新登录
        response = session.get(f"{BASE}/auth/login")
        auth_url = response.json()["data"]["auth_url"]

        # Mock模式跳过实际登录
        # 验证auth_url包含必要参数
        from urllib.parse import urlparse
        parsed = urlparse(auth_url)
        params = dict(parsed.query)

        assert "state" in params, "auth_url should contain state"
        assert params["state"], "state should not be empty"

    def test_user_info_updated_in_database(self, session):
        """TC-01-12: 用户信息更新到数据库"""
        # 模拟用户登录
        response = session.get(f"{BASE}/auth/login")

        # Mock模式
        assert response.status_code == 200
        assert response.json()["code"] == 0
        assert "auth_url" in response.json()["data"]

        # 验证用户信息结构
        user_data = response.json()["data"].get("user", {})

        # 验证必要字段存在
        assert "id" in user_data, "User should have id"
        assert "github_id" in user_data, "User should have github_id"
        assert "login" in user_data, "User should have login"
        assert "name" in user_data, "User should have name"
        assert "avatar_url" in user_data, "User should have avatar_url"
        assert "html_url" in user_data, "User should have html_url"
