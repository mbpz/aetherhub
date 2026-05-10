"""
技能模板路由：预定义的技能模板市场
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from ..deps import get_db, get_optional_user, require_user
from ..models import Skill, SkillFile, User
import json
import os
import shutil

router = APIRouter(prefix="/templates", tags=["templates"])

# 预定义模板（硬编码，无需数据库）
TEMPLATES = [
    {
        "id": "data-processor",
        "name": "data-processor",
        "description": "Read/Filter/Write pattern - 读取数据、过滤处理、写入输出",
        "category": "数据处理",
        "tags": ["data", "processor", "filter", "read", "write"],
        "readme": """# Data Processor Skill

A skill that reads data from a source, applies filtering/transformation, and writes to output.

## Usage

```python
from data_processor import process

data = process(input_data)
```

## Files

- `processor.py` - Main processing logic
- `filters.py` - Filter functions
- `writer.py` - Output writing
""",
        "skill_md": """# Skill: data-processor

## Capability
- Read data from files/APIs/databases
- Apply filtering based on rules
- Transform and aggregate data
- Write results to files or APIs

## Pattern
1. InputReader - reads raw data
2. FilterChain - applies filters
3. OutputWriter - writes results
""",
        "files": [
            {"filename": "processor.py", "content": "# Data processor\ndef process(input_data):\n    return input_data\n"},
            {"filename": "filters.py", "content": "# Filter functions\ndef filter_by(items, condition):\n    return [item for item in items if condition(item)]\n"},
            {"filename": "writer.py", "content": "# Output writer\ndef write(data, destination):\n    with open(destination, 'w') as f:\n        f.write(str(data))\n"},
        ],
    },
    {
        "id": "web-scraper",
        "name": "web-scraper",
        "description": "HTTP request + parse + store - 网页抓取向导",
        "category": "网络工具",
        "tags": ["web", "scraper", "http", "parse", "crawl"],
        "readme": """# Web Scraper Skill

A skill that fetches web pages, parses content, and stores results.

## Usage

```python
from web_scraper import scrape

results = scrape(url="https://example.com")
```

## Files

- `scraper.py` - HTTP fetching
- `parser.py` - HTML/content parsing
- `storage.py` - Data storage
""",
        "skill_md": """# Skill: web-scraper

## Capability
- Fetch web pages via HTTP
- Parse HTML/JSON content
- Extract structured data
- Store results to database or files

## Pattern
1. HTTPClient - fetches pages
2. ContentParser - parses HTML/JSON
3. DataStore - persists results
""",
        "files": [
            {"filename": "scraper.py", "content": "# Web scraper\nimport urllib.request\n\ndef fetch(url):\n    with urllib.request.urlopen(url) as response:\n        return response.read().decode('utf-8')\n"},
            {"filename": "parser.py", "content": "# HTML parser\nfrom html.parser import HTMLParser\n\nclass ContentParser(HTMLParser):\n    def __init__(self):\n        super().__init__()\n        self.content = []\n    \n    def handle_data(self, data):\n        self.content.append(data.strip())\n"},
            {"filename": "storage.py", "content": "# Storage\nimport json\n\ndef store(data, filepath):\n    with open(filepath, 'w') as f:\n        json.dump(data, f, indent=2)\n"},
        ],
    },
    {
        "id": "file-aggregator",
        "name": "file-aggregator",
        "description": "Read multiple files, combine output - 多文件聚合",
        "category": "文件操作",
        "tags": ["file", "aggregate", "combine", "merge", "read"],
        "readme": """# File Aggregator Skill

A skill that reads multiple files, combines their content, and outputs aggregated results.

## Usage

```python
from aggregator import aggregate

result = aggregate(file_pattern="data/*.txt")
```

## Files

- `aggregator.py` - Main aggregation logic
- `reader.py` - File reading utilities
- `combiner.py` - Content combination
""",
        "skill_md": """# Skill: file-aggregator

## Capability
- Read multiple files by pattern
- Filter and sort file contents
- Combine into single output
- Handle different file encodings

## Pattern
1. FileFinder - locates files by pattern
2. ContentReader - reads file contents
3. Combiner - merges content
""",
        "files": [
            {"filename": "aggregator.py", "content": "# File aggregator\nimport glob\n\ndef aggregate(file_pattern):\n    files = glob.glob(file_pattern)\n    results = []\n    for f in files:\n        with open(f, 'r') as file:\n            results.append(file.read())\n    return results\n"},
            {"filename": "reader.py", "content": "# File reader\ndef read_file(filepath, encoding='utf-8'):\n    with open(filepath, 'r', encoding=encoding) as f:\n        return f.read()\n\ndef read_lines(filepath):\n    with open(filepath, 'r') as f:\n        return f.readlines()\n"},
            {"filename": "combiner.py", "content": "# Combiner\ndef combine(contents, separator='\\n'):\n    return separator.join(contents)\n\ndef combine_json(items):\n    import json\n    return json.dumps(items, indent=2)\n"},
        ],
    },
]


class TemplateModel(BaseModel):
    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    readme: str
    skill_md: str
    files: List[dict]


def ok(data=None, message="success"):
    return {"code": 0, "message": message, "data": data}


@router.get("")
async def list_templates(
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """获取可用技能模板列表"""
    templates = TEMPLATES
    if category:
        templates = [t for t in templates if t["category"] == category]
    return ok(templates)


@router.get("/{template_id}")
async def get_template(template_id: str):
    """获取模板详情"""
    for t in TEMPLATES:
        if t["id"] == template_id:
            return ok(t)
    return {"code": 4004, "message": "Template not found", "data": None}


@router.post("/{template_id}/clone")
async def clone_template(
    template_id: str,
    name: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """克隆模板到用户的技能"""
    # 找到模板
    template = None
    for t in TEMPLATES:
        if t["id"] == template_id:
            template = t
            break

    if not template:
        return {"code": 4004, "message": "Template not found", "data": None}

    # 检查名称是否已存在
    skill_name = name or template["name"]
    existing = db.query(Skill).filter(Skill.name == skill_name).first()
    if existing:
        return {"code": 4009, "message": f"Skill name '{skill_name}' already exists", "data": None}

    # 创建技能
    skill = Skill(
        name=skill_name,
        description=template["description"],
        readme=template["readme"],
        skill_md=template["skill_md"],
        version="1.0.0",
        category=template["category"],
        tags=json.dumps(template["tags"], ensure_ascii=False),
        is_public=True,
        author_id=current_user.id,
    )
    db.add(skill)
    db.flush()

    # 创建文件
    skill_upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", str(skill.id))
    os.makedirs(skill_upload_dir, exist_ok=True)

    for file_info in template["files"]:
        filename = file_info["filename"]
        content = file_info["content"]
        file_path = os.path.join(skill_upload_dir, filename)
        with open(file_path, "w", encoding="utf-8") as fp:
            fp.write(content)

        file_record = SkillFile(
            skill_id=skill.id,
            filename=filename,
            file_path=file_path,
            file_size=len(content.encode("utf-8")),
            mime_type="text/x-python" if filename.endswith(".py") else "text/plain",
        )
        db.add(file_record)

    db.commit()
    db.refresh(skill)

    return ok({
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "tags": skill.get_tags(),
    }, "Template cloned successfully")
