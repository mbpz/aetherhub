# AetherHub 测试管理流程

**版本**: v1.0
**创建日期**: 2026-03-14
**状态**: 已启动

---

## 📋 流程概述

AetherHub 采用**测试驱动开发 (TDD)** 流程，确保所有功能都有完整的测试覆盖。

```
PRD → 测试用例设计 → 创建GitHub Issues → 编写测试 → 执行测试 → 修复问题 → 验证通过 → 关闭Issue
```

---

## 📁 文档结构

```
aetherhub/
├── docs/
│   ├── PRD-01-github-oauth.md           # PRD文档
│   ├── PRD-02-skill-square.md           # PRD文档
│   ├── PRD-03-my-skills.md              # PRD文档
│   ├── TEST-CASES.md                    # 测试用例设计（详细）
│   ├── TEST-ISSUES.md                   # Issue列表（待创建）
│   └── TEST-MANAGEMENT.md               # 本文档
├── tests/
│   ├── test_codex.py                    # Codex引擎测试
│   ├── test_ismp.py                     # ISMP协议测试
│   ├── test_full.py                     # 完整功能测试
│   ├── test_tc05_18.py                  # TC-05-18回归测试
│   └── test_web.py                      # Web API自动化测试
└── scripts/
    └── create_test_issues.py            # 批量创建GitHub Issues
```

---

## 🚀 快速开始

### 1. 配置GitHub Token

```bash
# 方法1: 临时设置
export GITHUB_TOKEN=your_github_token_here

# 方法2: 永久设置（添加到 ~/.zshrc 或 ~/.bashrc）
echo 'export GITHUB_TOKEN=your_github_token_here' >> ~/.zshrc
source ~/.zshrc
```

### 2. 创建GitHub Issues

```bash
cd aetherhub
python3 scripts/create_test_issues.py
```

### 3. 运行测试

```bash
cd aetherhub
source venv/bin/activate

# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_web.py -v

# 生成覆盖率报告
pytest tests/ --cov=aetherhub --cov-report=html --cov-report=term-missing
```

### 4. 生成测试报告

```bash
# HTML覆盖率报告
open htmlcov/index.html

# JSON报告
pytest tests/ --junitxml=test-results.xml
```

---

## 📊 测试用例优先级

| 优先级 | 说明 | 数量 | 优先处理 |
|--------|------|------|----------|
| **P0** | 核心功能，阻塞其他功能 | 12 | ✅ 必须 |
| **P1** | 重要功能，影响用户体验 | 24 | ⚡ 尽快 |
| **P2** | 边界情况，优化体验 | 2 | 🎯 可选 |

---

## 🔄 Issue管理流程

### 创建Issue

```bash
# 自动创建所有P0优先级的Issue
python3 scripts/create_test_issues.py
```

### Issue模板

每个Issue包含：
- **标题**: `[TC-XX-YY] 测试用例名称`
- **标签**: `test-case`, `priority:P0/P1/P2`
- **内容**:
  - 测试用例信息（PRD、优先级、类型、状态）
  - 前置条件
  - 测试步骤
  - 预期结果
  - 验收标准
  - 相关文档链接

### Issue状态

- **待测试**: Issue创建后，测试用例编写中
- **测试通过**: 所有验收标准已满足
- **测试失败**: 需要修复问题
- **已关闭**: Issue已解决

---

## 📝 编写测试用例

### 测试文件结构

```python
"""模块测试"""
import pytest
from aetherhub.module import Function

class TestModule:
    """模块测试类"""

    def test_case_name(self):
        """测试用例描述"""
        # 前置条件
        obj = Function()

        # 测试步骤
        result = obj.method()

        # 验证结果
        assert result == expected_value
```

### 测试命名规范

- **文件名**: `test_<module>.py`
- **类名**: `Test<Module>`
- **方法名**: `test_<feature>_<scenario>`

示例：
- `test_web.py` - Web功能测试
- `TestSkillSquare` - 技能广场测试类
- `test_search_with_results` - 搜索有结果测试

---

## 🐛 修复问题流程

### 1. 从Issue中提取问题

```bash
# 查看失败的测试
pytest tests/ -v

# 查看特定Issue
gh issue view 123
```

### 2. 修复代码

```python
# 修复bug
def buggy_function():
    return 1 / 0  # 错误

def fixed_function():
    try:
        return 1 / 0
    except ZeroDivisionError:
        return 0  # 修复
```

### 3. 运行测试验证

```bash
pytest tests/ -v
```

### 4. 更新Issue

```bash
# 标记Issue为测试通过
gh issue comment 123 --body "✅ 测试通过，问题已修复"

# 关闭Issue
gh issue close 123
```

---

## 📈 测试覆盖率目标

| 指标 | 目标值 |
|------|--------|
| 代码覆盖率 | ≥ 80% |
| 分支覆盖率 | ≥ 75% |
| 行覆盖率 | ≥ 85% |

### 查看覆盖率

```bash
# 生成HTML报告
pytest tests/ --cov=aetherhub --cov-report=html

# 查看终端输出
pytest tests/ --cov=aetherhub --cov-report=term-missing
```

---

## 🛠️ 测试工具

### pytest

```bash
# 安装
pip install pytest pytest-cov

# 运行测试
pytest tests/

# 运行特定测试
pytest tests/test_web.py::test_search_with_results -v

# 显示详细输出
pytest tests/ -vv

# 显示打印输出
pytest tests/ -s
```

### pytest-cov

```bash
# 安装
pip install pytest-cov

# 生成覆盖率报告
pytest tests/ --cov=aetherhub --cov-report=html
```

### pytest-html

```bash
# 安装
pip install pytest-html

# 生成HTML报告
pytest tests/ --html=test-report.html
```

---

## 📚 参考文档

- [PRD-01: GitHub OAuth 授权登录](../docs/PRD-01-github-oauth.md)
- [PRD-02: Skill 公开广场](../docs/PRD-02-skill-square.md)
- [PRD-03: 我的技能](../docs/PRD-03-my-skills.md)
- [测试用例设计](../docs/TEST-CASES.md)
- [Issue列表](../docs/TEST-ISSUES.md)

---

## 🎯 下一步行动

### 立即执行

1. ✅ 创建测试用例设计文档
2. ✅ 创建Issue管理文档
3. ✅ 创建批量创建Issues脚本
4. ⏳ 设置GitHub Token
5. ⏳ 运行脚本创建Issues
6. ⏳ 编写测试用例
7. ⏳ 执行测试
8. ⏳ 修复问题

### 第一周目标

- [ ] 创建所有P0优先级Issue (12个)
- [ ] 编写并运行所有P0测试用例
- [ ] 确保P0测试通过率100%
- [ ] 修复所有P0相关问题

### 第二周目标

- [ ] 创建所有P1优先级Issue (24个)
- [ ] 编写并运行所有P1测试用例
- [ ] 确保P1测试通过率≥95%

---

## 📞 联系方式

如有问题，请：
1. 查看相关PRD文档
2. 查看测试用例设计文档
3. 创建GitHub Issue反馈

---

**文档结束**
