# AetherHub 实现 Roadmap

**版本**: v2.1
**更新日期**: 2026-05-10
**状态**: 进行中

---

## 0. 产品定位（核心）

**一句话定位**: AI Agent 技能的"Signed Commit"——每个技能带 Z3 数学证明。

**产品本质**: Proof-Carrying Skills Marketplace（带证明的技能市场）

| 维度 | 说明 |
|------|------|
| **核心差异** | No competitor combines: 技能市场 + Z3形式化验证 + 动态生成 + Wasm沙箱 |
| **目标用户** | AI Agent开发者（需要可信赖技能）、企业安全团队（形式化验证需求）、技能创作者（证明正确性）、AI安全研究员（验证实验平台） |
| **技术护城河** | ISMP协议 → Codex动态生成 → Z3数学证明 → Wasmtime沙箱，四层纵深防御 |
| **商业化方向** | Free(10技能/100验证) → Pro($9/月无限制) → Enterprise(SSO/SLA/私有部署) |

**存储状态**: 本地文件系统 `uploads/`（非S3）
**版本管理**: `skill_versions` 表已实现，UI待完善
**CLI**: 面向开发者（`run`/`verify`/`execute`），缺少用户端工作流（login/upload/install）

---

## 1. 项目目标 vs 当前实现

### 1.1 核心引擎（蓝图定义）

| 模块 | 蓝图描述 | 当前状态 | 差距 |
|------|----------|----------|------|
| ISMP 协议 | 5-stage 意图→技能流水线 | 骨架完整 | 子模块未拆分，纯 mock |
| Codex 代码生成 | 动态技能合成，API 集成 | 纯 mock 占位函数 | 无真实 API 调用 |
| Tree-sitter 逻辑提取 | AST → Z3 数学公式 | 完全缺失 | 未安装、未实现 |
| Z3 形式化验证 | 数学级安全证明 | 半完成（solver 可用，formula stub） | extract_logic_formula 是占位符 |
| Wasmtime 执行沙箱 | 指令级隔离、安全执行 | 纯 mock | wasmtime 未安装 |
| ISMP 子模块 | semantic/capability/constraint | 全在 protocol.py 单文件 | 需拆分 |

**核心引擎完成度：~30%**

### 1.2 Web 应用

| 功能 | 状态 |
|------|------|
| GitHub OAuth + JWT | ✅ 完整（含 mock 模式） |
| 技能广场（搜索/分类/排序/分页） | ✅ 完整 |
| 技能详情（README/SKILL.md/文件） | ✅ 完整 |
| 上传技能（验证/文件/标签） | ✅ 完整 |
| 我的技能 CRUD | ✅ 完整 |
| Star/Unstar | ✅ 完整 |
| 删除确认对话框 | ✅ 完整 |
| 骨架屏/空状态/错误处理 | ✅ 完整 |
| 响应式 UI (Tailwind) | ✅ 完整 |
| Seed 数据（5个示例技能） | ✅ 完整 |
| 测试套件 PRD-01/02/03 | ✅ 30/31 通过 |

**Web 应用完成度：~95%**（但蓝图里未规划此模块）

---

## 2. 待实现功能清单

### P0 - 核心引擎补全

- [ ] ISMP 子模块拆分（semantic.py, capability.py, constraint.py）
- [ ] Tree-sitter → Z3 公式转换层
- [ ] Z3 验证器完善（修复 rules.py，反例反馈循环）
- [ ] Codex 引擎真实 API 集成
- [ ] Wasm 执行沙箱真实化
- [ ] 示例代码（examples/）

### P1 - Web 前端修复

- [ ] `web/frontend/src/lib/utils.js` 缺失（timeAgo, getCategoryColor, formatFileSize, getFileIcon）
- [ ] TC-05-18 测试验证（31/31 通过）

### P2 - 依赖安装

- [ ] `pip install tree-sitter tree-sitter-python`
- [ ] `pip install wasmtime`
- [ ] `pip install z3-solver`（确认已装）

---

## 3. 依赖安装清单

```bash
pip install tree-sitter tree-sitter-python   # AST 解析
pip install wasmtime                           # Wasm 执行沙箱
pip install z3-solver                           # 形式化验证（检查是否已装）
```

---

## 4. 实现进度

| 阶段 | 状态 |
|------|------|
| Part 1: ROADMAP.md 文档 | ✅ |
| Part 2: ISMP 子模块拆分 | 🔄 进行中 |
| Part 3: Tree-sitter → Z3 层 | ⬜ |
| Part 4: Z3 验证器完善 | ⬜ |
| Part 5: Codex 真实 API | ⬜ |
| Part 6: Wasm 沙箱 | ⬜ |
| Part 7: 示例代码 | ⬜ |
| Part 8: Web 前端 utils 修复 | ⬜ |
| Part 9: 测试 31/31 通过 | ⬜ |

---

## 5. 关键设计决策

### 5.1 ISMP 模块拆分

每个子模块独立，各自测试：
- `ismp/semantic.py` — 语义向量化（verb/object/target/condition 提取）
- `ismp/capability.py` — 能力空间（capability_space + resource_rules）
- `ismp/constraint.py` — 约束注入（从 resource_rules 生成 Z3 constraints）

### 5.2 Tree-sitter → Z3 公式

核心函数 `ast_to_z3_formula(ast)` 将 Python AST 节点映射为 Z3 表达式：
- `x = y + 1` → `x == y + 1`
- `if a > b:` → `If(a > b, ...)`
- `for i in range(n):` → 有限循环归纳表示

### 5.3 Codex 迭代修正循环

```
generate(prompt) → code
    ↓
verify(code, constraints) → sat/unsat
    ↓ sat (验证失败)
extract_counterexample() → feedback
    ↓
fix(code, feedback) → new code
    ↓
verify(new_code, constraints) → ...
```

### 5.4 Wasm 沙箱隔离

使用 wasmtime 的 WASI 接口实现：
- 内存限制：`memory_limit_mb`
- 时间限制：fuel 机制防止无限循环
- 文件系统：只读 WASI，只允许 /tmp 写入

---

## 6. 文件变更清单

```
ismp/
  protocol.py      # 修改 — 调用子模块
  semantic.py      # 新建
  capability.py    # 新建
  constraint.py    # 新建
verification/
  z3_verifier.py   # 修改 — 替换 stub
  rules.py         # 新建
  tree_sitter_parser.py  # 新建
codex/
  engine.py        # 修改 — 真实 API
  template.py      # 新建
execution/
  wasmtime.py      # 修改 — 真实 Wasm
  sandbox.py       # 新建
examples/
  example_1.py     # 新建
  example_2.py     # 新建
  example_3.py     # 新建
web/frontend/src/lib/
  utils.js         # 新建
main.py            # 修改 — 适配新模块结构
ROADMAP.md         # 新建
```