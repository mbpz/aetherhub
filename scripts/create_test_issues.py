#!/usr/bin/env python3
"""
批量创建GitHub Issues管理测试用例

使用方法:
1. 配置GITHUB_TOKEN环境变量
2. 运行脚本: python scripts/create_test_issues.py
"""

import os
import sys
import json
import time
from typing import List, Dict, Any

# 配置
REPO_OWNER = "mbpz"
REPO_NAME = "aetherhub"
BASE_URL = "https://api.github.com"

# 测试用例数据
TEST_CASES = [
    # PRD-01: GitHub OAuth 授权登录
    {
        "id": "TC-01-01",
        "title": "登录按钮可见性",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P0
- **类型**: UI测试
- **状态**: 待测试

## 前置条件

用户未登录，访问首页

## 测试步骤

1. 访问首页 `/`
2. 观察导航栏

## 预期结果

- 导航栏右侧显示"GitHub 登录"按钮
- 按钮带有GitHub图标
- 按钮颜色为主色调，可点击

## 验收标准

- [ ] 登录按钮可见
- [ ] 按钮带有GitHub图标
- [ ] 按钮颜色正确
- [ ] 按钮可点击

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P0""",
        "labels": ["test-case", "priority:P0", "PRD-01"]
    },
    {
        "id": "TC-01-02",
        "title": "GitHub OAuth 跳转",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P0
- **类型**: API测试
- **状态**: 待测试

## 前置条件

用户未登录

## 测试步骤

1. 访问 `/api/v1/auth/login`
2. 检查响应

## 预期结果

- 返回200，包含auth_url
- auth_url包含client_id、scope、state参数

## 验收标准

- [ ] 返回200状态码
- [ ] 包含auth_url字段
- [ ] auth_url包含client_id
- [ ] auth_url包含scope
- [ ] auth_url包含state

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P0, PRD-01""",
        "labels": ["test-case", "priority:P0", "PRD-01"]
    },
    {
        "id": "TC-01-03",
        "title": "OAuth 授权后回调处理",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P0
- **类型**: 集成测试
- **状态**: 待测试

## 前置条件

用户在GitHub完成授权

## 测试步骤

1. 访问 `/auth/callback?code=xxx&state=xxx`
2. 检查Token生成和跳转

## 预期结果

- 成功获取用户信息
- 前端收到JWT Token
- 自动跳转至首页

## 验收标准

- [ ] 成功获取用户信息
- [ ] 生成JWT Token
- [ ] Token存储在LocalStorage
- [ ] 自动跳转至首页

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P0, PRD-01""",
        "labels": ["test-case", "priority:P0", "PRD-01"]
    },
    {
        "id": "TC-01-04",
        "title": "登录后导航栏状态",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P0
- **类型**: UI测试
- **状态**: 待测试

## 前置条件

用户成功登录

## 测试步骤

1. 观察导航栏

## 预期结果

- "GitHub 登录"按钮消失
- 显示用户GitHub头像
- 显示"上传技能"按钮

## 验收标准

- [ ] 登录按钮消失
- [ ] 显示用户头像
- [ ] 显示"上传技能"按钮

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P0, PRD-01""",
        "labels": ["test-case", "priority:P0", "PRD-01"]
    },
    {
        "id": "TC-01-05",
        "title": "用户信息下拉菜单",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P0
- **类型**: UI测试
- **状态**: 待测试

## 前置条件

用户已登录

## 测试步骤

1. 点击头像
2. 观察下拉菜单

## 预期结果

- 菜单显示用户名
- 显示"我的技能"选项
- 显示"退出登录"选项

## 验收标准

- [ ] 菜单正确显示
- [ ] 显示用户名
- [ ] 显示"我的技能"选项
- [ ] 显示"退出登录"选项

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P0, PRD-01""",
        "labels": ["test-case", "priority:P0", "PRD-01"]
    },
    {
        "id": "TC-01-06",
        "title": "登录状态持久化",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P0
- **类型**: 功能测试
- **状态**: 待测试

## 前置条件

用户已登录

## 测试步骤

1. 刷新页面(F5)
2. 检查登录状态

## 预期结果

- 登录状态保持
- 不需要重新登录

## 验收标准

- [ ] 登录状态保持
- [ ] 不需要重新登录

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P0, PRD-01""",
        "labels": ["test-case", "priority:P0", "PRD-01"]
    },
    {
        "id": "TC-01-07",
        "title": "Token 过期处理",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P1
- **类型**: API测试
- **状态**: 待测试

## 前置条件

Token已过期

## 测试步骤

1. 访问需要鉴权的接口

## 预期结果

- 返回401
- 前端清除过期Token
- 跳转登录页

## 验收标准

- [ ] 返回401状态码
- [ ] 前端清除过期Token
- [ ] 跳转登录页

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P1, PRD-01""",
        "labels": ["test-case", "priority:P1", "PRD-01"]
    },
    {
        "id": "TC-01-08",
        "title": "退出登录",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P0
- **类型**: 功能测试
- **状态**: 待测试

## 前置条件

用户已登录

## 测试步骤

1. 点击"退出登录"
2. 检查状态

## 预期结果

- LocalStorage中的Token被清除
- 导航栏恢复登录按钮
- 跳转至首页

## 验收标准

- [ ] Token被清除
- [ ] 导航栏恢复登录按钮
- [ ] 跳转至首页

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P0, PRD-01""",
        "labels": ["test-case", "priority:P0", "PRD-01"]
    },
    {
        "id": "TC-01-09",
        "title": "未登录访问受保护页面",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P0
- **类型**: API测试
- **状态**: 待测试

## 前置条件

用户未登录

## 测试步骤

1. 访问 `/skills/mine`
2. 访问 `/skills/upload`

## 预期结果

- 返回401
- 重定向至登录页

## 验收标准

- [ ] 返回401状态码
- [ ] 重定向至登录页

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P0, PRD-01""",
        "labels": ["test-case", "priority:P0", "PRD-01"]
    },
    {
        "id": "TC-01-10",
        "title": "OAuth state防CSRF",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P0
- **类型**: 安全测试
- **状态**: 待测试

## 前置条件

无state的OAuth回调

## 测试步骤

1. 访问 `/auth/callback?code=xxx`

## 预期结果

- 返回403或4003
- 不创建用户会话

## 验收标准

- [ ] 返回403或4003
- [ ] 不创建用户会话

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P0, security, PRD-01""",
        "labels": ["test-case", "priority:P0", "security", "PRD-01"]
    },
    {
        "id": "TC-01-11",
        "title": "GitHub OAuth失败处理",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P1
- **类型**: 边界测试
- **状态**: 待测试

## 前置条件

用户在GitHub取消授权

## 测试步骤

1. 访问 `/auth/callback?error=access_denied`

## 预期结果

- 显示"授权已取消"提示
- 不崩溃

## 验收标准

- [ ] 显示"授权已取消"提示
- [ ] 不崩溃

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P1, PRD-01""",
        "labels": ["test-case", "priority:P1", "PRD-01"]
    },
    {
        "id": "TC-01-12",
        "title": "用户信息同步",
        "body": """## 测试用例信息

- **PRD**: PRD-01 GitHub OAuth 授权登录
- **优先级**: P1
- **类型**: 数据同步测试
- **状态**: 待测试

## 前置条件

用户修改GitHub信息后重新登录

## 测试步骤

1. 重新通过GitHub登录
2. 检查数据库中的信息

## 预期结果

- 数据库中的name、avatar_url等字段更新

## 验收标准

- [ ] 数据库中的name字段更新
- [ ] 数据库中的avatar_url字段更新

## 相关文档

- [PRD-01](../docs/PRD-01-github-oauth.md)
- [测试用例设计](../docs/TEST-CASES.md)

## 标签

test-case, priority:P1, PRD-01""",
        "labels": ["test-case", "priority:P1", "PRD-01"]
    },
]

def create_github_issue(token: str, repo: str, issue_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建GitHub Issue"""
    url = f"{BASE_URL}/repos/{repo}/issues"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "title": issue_data["title"],
        "body": issue_data["body"],
        "labels": issue_data["labels"]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"创建Issue失败: {issue_data['id']} - {e}")
        return None

def main():
    """主函数"""
    # 从环境变量获取GitHub Token
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        print("错误: 未设置GITHUB_TOKEN环境变量")
        print("请运行: export GITHUB_TOKEN=your_token_here")
        sys.exit(1)

    repo = f"{REPO_OWNER}/{REPO_NAME}"

    print(f"开始创建GitHub Issues...")
    print(f"仓库: {repo}")
    print(f"测试用例数量: {len(TEST_CASES)}")
    print()

    created_issues = []
    failed_issues = []

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] 创建Issue: {test_case['id']} - {test_case['title']}")

        issue = create_github_issue(github_token, repo, test_case)

        if issue:
            created_issues.append(issue)
            print(f"  ✅ 成功创建: #{issue['number']} - {issue['html_url']}")
        else:
            failed_issues.append(test_case)
            print(f"  ❌ 创建失败")

        # 避免API限流
        if i % 10 == 0:
            time.sleep(2)

    print()
    print("=" * 60)
    print(f"创建完成!")
    print(f"成功: {len(created_issues)} 个")
    print(f"失败: {len(failed_issues)} 个")
    print("=" * 60)

    if created_issues:
        print("\n成功创建的Issues:")
        for issue in created_issues:
            print(f"  #{issue['number']}: {issue['title']}")
            print(f"    {issue['html_url']}")

    if failed_issues:
        print("\n创建失败的Issues:")
        for issue in failed_issues:
            print(f"  {issue['id']}: {issue['title']}")

    return len(failed_issues) == 0

if __name__ == "__main__":
    import requests

    success = main()
    sys.exit(0 if success else 1)
