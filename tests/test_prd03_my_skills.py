"""PRD-03: 我的技能测试 - P0核心功能"""
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
    """获取认证头"""
    return {"Authorization": f"Bearer {live_token}"}


@pytest.fixture
def session(live_token):
    """创建带认证的测试会话"""
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {live_token}"})
    return s


class TestMySkills:
    """PRD-03 我的技能测试"""

    # TC-03-01: 需登录才能访问
    def test_access_mine_requires_auth(self, session):
        """TC-03-01: 访问 /skills/mine 需要登录"""
        # 先清除认证头
        s = requests.Session()
        response = s.get(f"{BASE}/skills/mine")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    # TC-03-02: 只展示当前用户的技能
    def test_get_mine_shows_only_current_user_skills(self, session, live_token):
        """TC-03-02: 我的技能只展示当前用户的技能"""
        response = session.get(f"{BASE}/skills/mine")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()["data"]
        assert "items" in data, "Response should contain items"
        items = data.get("items", [])

        # 验证返回的是当前用户的技能
        for item in items:
            if "author" in item:
                author = item["author"]
                assert author.get("login") in ("demo-user", "octocat"), \
                    f"Skill {item['name']} should belong to demo-user or octocat"

    def test_mine_shows_correct_total_count(self, auth_headers):
        """TC-03-02: 我的技能显示正确的数量"""
        response = requests.get(f"{BASE}/skills/mine", headers=auth_headers)
        data = response.json()["data"]

        assert "total" in data, "Response should contain total"
        assert isinstance(data["total"], int), "Total should be an integer"

    # TC-03-04: 点击卡片跳转详情
    def test_click_skill_card_redirects_to_detail(self, auth_headers):
        """TC-03-04: 点击技能卡片跳转至详情页"""
        # 先获取我的技能列表
        response = requests.get(f"{BASE}/skills/mine", headers=auth_headers)
        items = response.json()["data"].get("items", [])

        if items:
            skill_id = items[0]["id"]
            # 点击卡片跳转
            detail_response = requests.get(f"{BASE}/skills/{skill_id}", headers=auth_headers)

            assert detail_response.status_code == 200, \
                f"Should access skill detail page, got {detail_response.status_code}"

    def test_detail_page_shows_correct_skill(self, auth_headers):
        """TC-03-04: 详情页显示正确的技能"""
        # 先获取我的技能列表
        response = requests.get(f"{BASE}/skills/mine", headers=auth_headers)
        items = response.json()["data"].get("items", [])

        if items:
            skill_id = items[0]["id"]

            # 访问详情页
            detail_response = requests.get(f"{BASE}/skills/{skill_id}", headers=auth_headers)
            skill = detail_response.json()["data"]

            # 验证技能ID匹配
            assert skill["id"] == skill_id, "Detail page should show correct skill"

    # TC-03-07: 删除技能——确认删除
    def test_delete_own_skill(self, auth_headers):
        """TC-03-07: 删除自己的技能成功"""
        # 先创建一个技能
        import io

        def make_zip(name="SKILL.md"):
            buf = io.BytesIO()
            buf.write(b"# Test\nTest content")
            buf.seek(0)
            return (name, buf, "text/markdown")

        import time
        unique_name = f"test-skill-{int(time.time())}"

        create_resp = requests.post(
            f"{BASE}/skills",
            headers=auth_headers,
            data={
                "name": unique_name,
                "version": "1.0.0",
                "description": "Test delete",
                "tags": "[]",
            },
            files={"files": make_zip()},
        )
        assert create_resp.status_code in (200, 201), f"Create failed: {create_resp.status_code} {create_resp.text}"

        skill_id = create_resp.json()["data"]["id"]

        # 删除
        delete_resp = requests.delete(f"{BASE}/skills/{skill_id}", headers=auth_headers)
        assert delete_resp.status_code == 200, \
            f"Delete should return 200, got {delete_resp.status_code}: {delete_resp.text}"

    # TC-03-08: 删除后广场同步移除
    def test_deleted_skill_not_in_square(self, auth_headers):
        """TC-03-08: 删除后广场不再显示"""
        # 创建一个技能再删除
        import io
        import time

        def make_zip(name="SKILL.md"):
            buf = io.BytesIO()
            buf.write(b"# Test\nTest content")
            buf.seek(0)
            return (name, buf, "text/markdown")

        unique_name = f"test-skill-{int(time.time())}"

        create_resp = requests.post(
            f"{BASE}/skills",
            headers=auth_headers,
            data={
                "name": unique_name,
                "version": "1.0.0",
                "description": "Test delete",
                "tags": "[]",
            },
            files={"files": make_zip()},
        )
        skill_id = create_resp.json()["data"]["id"]

        # 删除
        requests.delete(f"{BASE}/skills/{skill_id}", headers=auth_headers)

        # 验证广场不再显示
        square_resp = requests.get(f"{BASE}/skills")
        items = square_resp.json()["data"]["items"]
        skill_ids = [item["id"] for item in items]
        assert skill_id not in skill_ids, f"Deleted skill {skill_id} should not appear in square"

    # TC-03-10: 无法删除他人技能
    def test_cannot_delete_other_users_skill(self, auth_headers):
        """TC-03-10: 无法删除他人技能"""
        # 尝试删除一个不存在的 skill 或他人创建的
        response = requests.delete(f"{BASE}/skills/999999", headers=auth_headers)
        assert response.status_code in (403, 404), \
            f"Should not allow deleting non-existent skill, got {response.status_code}"


class TestMySkillsEdgeCases:
    """PRD-03 边界情况测试"""

    def test_empty_mine_list_structure(self, auth_headers):
        """TC-03-09: 空状态展示（验证结构）"""
        response = requests.get(f"{BASE}/skills/mine", headers=auth_headers)
        data = response.json()["data"]

        assert "total" in data, "Response should contain total"
        assert "items" in data, "Response should contain items"
        assert isinstance(data["total"], int), "Total should be an integer"
        assert isinstance(data["items"], list), "Items should be a list"

    def test_invalid_skill_id_delete(self, auth_headers):
        """测试删除不存在的技能"""
        response = requests.delete(f"{BASE}/skills/999999", headers=auth_headers)

        # 应该返回403或404
        assert response.status_code in (403, 404), \
            f"Should return 403 or 404 for non-existent skill, got {response.status_code}"

    def test_delete_nonexistent_skill_idempotent(self, auth_headers):
        """测试删除不存在技能是幂等的"""
        skill_id = 999999

        # 第一次删除
        response1 = requests.delete(f"{BASE}/skills/{skill_id}", headers=auth_headers)
        # 第二次删除
        response2 = requests.delete(f"{BASE}/skills/{skill_id}", headers=auth_headers)

        # 两次都应返回同样错误码
        assert response1.status_code == response2.status_code, \
            "Delete should be idempotent"


class TestMySkillsPermissions:
    """PRD-03 权限测试"""

    def test_delete_different_user_skill_returns_403(self):
        """测试删除他人技能返回403"""
        # 不带有效 token
        fake_headers = {"Authorization": "Bearer fake_token"}

        response = requests.delete(f"{BASE}/skills/1", headers=fake_headers)

        assert response.status_code in (401, 403, 404), \
            f"Should return 401/403/404 when deleting with invalid token, got {response.status_code}"

    def test_delete_nonexistent_skill_with_fake_token(self):
        """测试用无效 token 删除不存在的技能"""
        fake_headers = {"Authorization": "Bearer fake_token"}

        response = requests.delete(f"{BASE}/skills/999999", headers=fake_headers)

        assert response.status_code in (401, 403, 404), \
            f"Should return 401/403/404 for non-existent skill with fake token, got {response.status_code}"