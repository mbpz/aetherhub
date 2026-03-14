"""
TC-05-18 回归测试：标签数量上限校验
验证修复：超过 10 个标签应返回 400，<=10 个标签应成功
"""
import requests
import json
import io
import zipfile
import sys
from urllib.parse import urlparse, parse_qs

BASE = "http://localhost:8000/api/v1"


def make_zip():
    """生成合法的 .md 文件用于上传测试"""
    buf = io.BytesIO()
    buf.write(b"# Test Skill\nA skill for testing.\n")
    buf.seek(0)
    return buf


def make_file_tuple(fname="SKILL.md"):
    return (fname, make_zip(), "text/markdown")


def get_token():
    """
    Mock 登录流程：
    1. GET /api/v1/auth/login  →  拿 auth_url (含 state)
    2. GET auth_url (mock-callback)  →  302 重定向到前端 /auth/callback?token=xxx
    3. 从重定向 Location 里解析 token
    """
    s = requests.Session()

    # Step 1: 获取 auth_url
    r1 = s.get(f"{BASE}/auth/login")
    assert r1.status_code == 200, f"login endpoint failed: {r1.status_code} {r1.text}"
    data = r1.json()
    auth_url = data["data"]["auth_url"]
    print(f"  auth_url: {auth_url}")

    # Step 2: 访问 mock-callback（不跟随重定向，截取 Location）
    r2 = s.get(auth_url, allow_redirects=False)
    location = r2.headers.get("location", "")
    print(f"  mock-callback redirect → {location}")

    # Step 3: 从 Location 解析 token
    parsed = urlparse(location)
    params = parse_qs(parsed.query)
    token_list = params.get("token", [])
    if not token_list:
        # 若有 error 参数
        error = params.get("error", ["unknown"])[0]
        raise RuntimeError(f"Mock login failed, error={error}")

    token = token_list[0]
    print(f"  JWT obtained (first 20 chars): {token[:20]}...")
    return token


def make_headers(token):
    return {"Authorization": f"Bearer {token}"}


results = []

print("=" * 60)
print("TC-05-18 回归测试：标签数量上限校验")
print("=" * 60)

# 获取 token
print("\n[认证] Mock 登录...")
try:
    token = get_token()
    headers = make_headers(token)
    # 验证
    me = requests.get(f"{BASE}/auth/me", headers=headers)
    print(f"  auth/me: {me.status_code} - login={me.json().get('data', {}).get('login', '?')}")
except Exception as e:
    print(f"  ❌ 登录失败: {e}")
    sys.exit(2)

# Case 1: 11 个标签 → 应返回 400
print("\n[Case 1] 提交 11 个标签（超限，预期 400）...")
tags_11 = json.dumps([f"tag{i}" for i in range(1, 12)])
resp = requests.post(
    f"{BASE}/skills",
    headers=headers,
    data={
        "name": "tc0518-eleven-tags",
        "version": "1.0.0",
        "description": "Tag limit test with 11 tags",
        "category": "utility",
        "tags": tags_11,
    },
    files={"files": make_file_tuple()},
)
print(f"  Status: {resp.status_code}")
print(f"  Body:   {resp.text[:300]}")

if resp.status_code == 400:
    try:
        body = resp.json()
        code = (body.get("detail") or {}).get("code") or body.get("code", "n/a")
    except Exception:
        code = "parse_error"
    print(f"  ✅ PASS — 返回 400，error_code={code}")
    results.append(("TC-05-18a [11 tags → 400]", "PASS", None))
else:
    msg = f"预期 400，实际 {resp.status_code}: {resp.text[:200]}"
    print(f"  ❌ FAIL — {msg}")
    results.append(("TC-05-18a [11 tags → 400]", "FAIL", msg))

# Case 2: 10 个标签（边界值）→ 应成功
print("\n[Case 2] 提交 10 个标签（边界值，预期 201）...")
tags_10 = json.dumps([f"tag{i}" for i in range(1, 11)])
resp2 = requests.post(
    f"{BASE}/skills",
    headers=headers,
    data={
        "name": "tc0518-ten-tags",
        "version": "1.0.0",
        "description": "Tag limit test with exactly 10 tags",
        "category": "utility",
        "tags": tags_10,
    },
    files={"files": make_file_tuple()},
)
print(f"  Status: {resp2.status_code}")
print(f"  Body:   {resp2.text[:300]}")

if resp2.status_code in (200, 201):
    print(f"  ✅ PASS — 10 个标签创建成功")
    results.append(("TC-05-18b [10 tags → 201]", "PASS", None))
else:
    msg = f"预期 200/201，实际 {resp2.status_code}: {resp2.text[:200]}"
    print(f"  ❌ FAIL — {msg}")
    results.append(("TC-05-18b [10 tags → 201]", "FAIL", msg))

# Case 3: 0 个标签 → 应成功
print("\n[Case 3] 提交 0 个标签（预期 201）...")
resp3 = requests.post(
    f"{BASE}/skills",
    headers=headers,
    data={
        "name": "tc0518-zero-tags",
        "version": "1.0.0",
        "description": "Tag limit test with 0 tags",
        "category": "utility",
        "tags": "[]",
    },
    files={"files": make_file_tuple()},
)
print(f"  Status: {resp3.status_code}")
if resp3.status_code in (200, 201):
    print(f"  ✅ PASS — 空标签创建成功")
    results.append(("TC-05-18c [0 tags → 201]", "PASS", None))
else:
    msg = f"预期 200/201，实际 {resp3.status_code}: {resp3.text[:200]}"
    print(f"  ❌ FAIL — {msg}")
    results.append(("TC-05-18c [0 tags → 201]", "FAIL", msg))

# Summary
print("\n" + "=" * 60)
print("测试结果汇总")
print("=" * 60)
passes = sum(1 for _, s, _ in results if s == "PASS")
fails = sum(1 for _, s, _ in results if s == "FAIL")
for name, status, err in results:
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} {status}  {name}")
    if err:
        print(f"       原因: {err}")

print(f"\n共 {len(results)} 条，PASS={passes}，FAIL={fails}")
sys.exit(0 if fails == 0 else 1)
