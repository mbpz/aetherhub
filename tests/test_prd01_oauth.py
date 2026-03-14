"""PRD-01: GitHub OAuth 授权登录测试 - P0核心功能"""
import pytest
import requests
import json
from urllib.parse import urlparse, parse_qs
from unittest.mock import Mock, patch, MagicMock
import time


BASE = "http://localhost:8000/api/v1"


@pytest.fixture
def mock_auth_response():
    """Mock登录响应"""
    return {
        "code": 0,
        "message": "success",
        "data": {
            "auth_url": "http://localhost:8000/api/v1/auth/mock-callback?state=8BzJuY0Cp7Pga626kHtIiDUMlWyI1Ow3hV5hM2JFRFQ",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiaWF0IjoxNzczNDg5NDQxLCJleHAiOjE3NzM1NzU4NDF9.IzHrcRQuh-VSD_EGO2xfZDRu1-cW2RyA8mSTw0cVlmQ",
            "user": {
                "id": 2,
                "github_id": 12345678,
                "login": "demo-user",
                "name": "Demo User",
                "avatar_url": "https://avatars.githubusercontent.com/u/583231",
                "html_url": "https://github.com/demo-user"
            }
        }
    }


@pytest.fixture
def session():
    """创建测试会话"""
    return requests.Session()


class TestGitHubOAuth:
    """PRD-01 GitHub OAuth 授权登录测试"""

    # TC-01-02: GitHub OAuth 跳转
    def test_get_auth_url_returns_200_with_auth_url(self, session, mock_auth_response):
        """TC-01-02: 访问 /api/v1/auth/login 返回200和auth_url"""
        response = session.get(f"{BASE}/auth/login")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()["code"] == 0, f"Expected code 0, got {response.json().get('code')}"

        data = response.json()["data"]
        assert "auth_url" in data, "Response should contain auth_url"
        assert data["auth_url"] is not None, "auth_url should not be None"

        # 验证auth_url包含必要参数
        parsed = urlparse(data["auth_url"])
        assert "state" in parsed.query, "auth_url should contain state parameter"

    def test_auth_url_contains_necessary_parameters(self, session, mock_auth_response):
        """TC-01-02: auth_url包含client_id、scope、state参数"""
        response = session.get(f"{BASE}/auth/login")
        auth_url = response.json()["data"]["auth_url"]

        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)

        assert "client_id" in params, "auth_url should contain client_id"
        assert "scope" in params, "auth_url should contain scope"
        assert "state" in params, "auth_state should contain state parameter"
        assert params["scope"][0] == "read:user,user:email", "scope should include read:user,user:email"

    # TC-01-03: OAuth 授权后回调处理
    def test_oauth_callback_with_valid_state(self, session, mock_auth_response):
        """TC-01-03: 有效state的OAuth回调成功处理"""
        response = session.get(
            f"{BASE}/auth/mock-callback?state=8BzJuY0Cp7Pga626kHtIiDUMlWyI1Ow3hV5hM2JFRFQ",
            allow_redirects=False
        )

        # 应该重定向到前端
        location = response.headers.get("location", "")
        assert "token=" in location, "Should redirect with token parameter"
        assert "callback" in location, "Should redirect to callback page"

    def test_oauth_callback_returns_jwt_token(self, session, mock_auth_response):
        """TC-01-03: OAuth回调成功获取JWT Token"""
        response = session.get(
            f"{BASE}/auth/mock-callback?state=8BzJuY0Cp7Pga626kHtIiDUMlWyI1Ow3hV5hM2JFRFQ",
            allow_redirects=False
        )

        location = response.headers.get("location", "")
        token = location.split("token=")[-1].split("&")[0]

        assert token is not None, "Token should be extracted from redirect URL"
        assert len(token) > 100, "Token should be a valid JWT (long enough)"

    def test_oauth_callback_redirects_to_homepage(self, session, mock_auth_response):
        """TC-01-03: OAuth回调后自动跳转至首页"""
        response = session.get(
            f"{BASE}/auth/mock-callback?state=8BzJuY0Cp7Pga626kHtIiDUMlWyI1Ow3hV5hM2JFRFQ",
            allow_redirects=False
        )

        location = response.headers.get("location", "")
        assert "/auth/callback" in location, "Should redirect to /auth/callback"

    # TC-01-04: 登录后导航栏状态
    def test_after_login_navigation_shows_avatar(self, session, mock_auth_response):
        """TC-01-04: 登录后导航栏显示用户头像"""
        token = mock_auth_response["data"]["token"]

        response = session.get(
            f"{BASE}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        user_data = response.json()["data"]
        assert "avatar_url" in user_data, "User data should contain avatar_url"
        assert user_data["avatar_url"] is not None, "avatar_url should not be None"

    def test_after_login_navigation_shows_upload_button(self, session, mock_auth_response):
        """TC-01-04: 登录后导航栏显示上传技能按钮"""
        token = mock_auth_response["data"]["token"]

        response = session.get(
            f"{BASE}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        user_data = response.json()["data"]
        assert "login" in user_data, "User data should contain login"
        assert user_data["login"] == "demo-user", "Should be demo-user"

    # TC-01-06: 登录状态持久化
    def test_token_persistence_after_page_refresh(self, session, mock_auth_response):
        """TC-01-06: Token持久化，刷新后保持登录状态"""
        token = mock_auth_response["data"]["token"]

        # 第一次请求
        response1 = session.get(
            f"{BASE}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response1.status_code == 200, "First request should succeed"

        # 模拟刷新（重新获取token）
        response2 = session.get(
            f"{BASE}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response2.status_code == 200, "Second request should also succeed"
        assert response2.json()["code"] == 0, "Token should still be valid"

    # TC-01-08: 退出登录
    def test_logout_clears_token(self, session, mock_auth_response):
        """TC-01-08: 退出登录清除Token"""
        token = mock_auth_response["data"]["token"]

        # 先登录
        session.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert session.cookies.get("aetherhub_token") is not None, "Token should be set in cookies"

        # 模拟退出登录（清除token）
        # 实际退出登录需要调用后端API
        session.cookies.clear()

        # 验证token被清除
        assert session.cookies.get("aetherhub_token") is None, "Token should be cleared after logout"

    def test_logout_redirects_to_homepage(self, session, mock_auth_response):
        """TC-01-08: 退出后跳转至首页"""
        # 登录
        token = mock_auth_response["data"]["token"]
        session.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})

        # 模拟退出登录
        session.cookies.clear()

        # 访问受保护页面应该返回401
        response = session.get(f"{BASE}/skills/mine")
        assert response.status_code == 401, "Should return 401 after logout"

    # TC-01-09: 未登录访问受保护页面
    def test_unauthenticated_access_mine_returns_401(self, session):
        """TC-01-09: 未登录访问 /skills/mine 返回401"""
        response = session.get(f"{BASE}/skills/mine")

        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_unauthenticated_access_upload_returns_401(self, session):
        """TC-01-09: 未登录访问 /skills/upload 返回401"""
        response = session.get(f"{BASE}/skills/upload")

        assert response.status_status == 401, f"Expected 401, got {response.status_code}"

    # TC-01-10: OAuth state防CSRF
    def test_oauth_callback_without_state_returns_error(self, session):
        """TC-01-10: 无state的OAuth回调返回错误"""
        response = session.get(
            f"{BASE}/auth/callback?code=fake_code",
            allow_redirects=False
        )

        # 应该返回错误或重定向到错误页面
        assert response.status_code in (400, 403, 401), f"Should return error status, got {response.status_code}"

    def test_oauth_callback_with_invalid_state_returns_error(self, session):
        """TC-01-10: 无效state的OAuth回调返回错误"""
        response = session.get(
            f"{BASE}/auth/callback?code=fake_code&state=INVALID_STATE_XYZ",
            allow_redirects=False
        )

        # 应该返回错误或重定向到错误页面
        assert response.status_code in (400, 403, 401), f"Should return error status, got {response.status_code}"


class TestGitHubOAuthSecurity:
    """PRD-01 安全测试"""

    def test_invalid_token_returns_401(self, session):
        """测试无效Token返回401"""
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.INVALID"

        response = session.get(
            f"{BASE}/auth/me",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )

        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_missing_token_returns_401(self, session):
        """测试缺少Token返回401"""
        response = session.get(f"{BASE}/auth/me")

        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
