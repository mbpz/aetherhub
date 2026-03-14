"""
数据库 Seed 脚本：写入示例 Skill 数据
"""
import json
import os
import sys

from .database import SessionLocal, init_db
from .models import User, Skill, SkillFile


SEED_USER = {
    "github_id": 583231,
    "login": "octocat",
    "name": "The Octocat",
    "avatar_url": "https://avatars.githubusercontent.com/u/583231",
    "bio": "GitHub mascot & AetherHub demo user",
    "html_url": "https://github.com/octocat",
}

SEED_SKILLS = [
    {
        "name": "csv-data-processor",
        "version": "1.2.0",
        "category": "数据处理",
        "description": "读取、过滤和导出 CSV 数据的通用技能包，支持条件过滤、列选择和数据转换。",
        "tags": ["python", "csv", "数据处理"],
        "star_count": 42,
        "download_count": 156,
        "readme": """# CSV Data Processor

一个强大的 CSV 数据处理技能，支持多种操作。

## 功能特性

- 读取本地或远程 CSV 文件
- 按条件过滤数据行
- 选择指定列
- 导出为新的 CSV 文件

## 使用方法

```python
from skill import CsvProcessor

processor = CsvProcessor("data.csv")
result = processor.filter(column="age", gt=18).select(["name", "email"]).export("output.csv")
```

## 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| filepath | str | CSV 文件路径 |
| encoding | str | 文件编码，默认 utf-8 |
""",
        "skill_md": """# SKILL
name: csv-data-processor
version: 1.2.0
description: CSV 数据处理技能
author: octocat
category: 数据处理

## 触发条件
当用户需要处理 CSV 文件时

## 使用场景
- 数据清洗
- 数据过滤
- 数据导出
""",
        "files": [
            {
                "filename": "skill.py",
                "content": """import csv
from typing import List, Optional

class CsvProcessor:
    \"\"\"CSV 数据处理器\"\"\"
    
    def __init__(self, filepath: str, encoding: str = "utf-8"):
        self.filepath = filepath
        self.encoding = encoding
        self._data = []
        self._headers = []
        self._load()
    
    def _load(self):
        with open(self.filepath, "r", encoding=self.encoding) as f:
            reader = csv.DictReader(f)
            self._headers = reader.fieldnames or []
            self._data = list(reader)
    
    def filter(self, column: str, eq=None, gt=None, lt=None):
        filtered = []
        for row in self._data:
            val = row.get(column)
            if val is None:
                continue
            try:
                val_num = float(val)
                if gt is not None and val_num <= gt:
                    continue
                if lt is not None and val_num >= lt:
                    continue
            except ValueError:
                pass
            if eq is not None and val != str(eq):
                continue
            filtered.append(row)
        self._data = filtered
        return self
    
    def select(self, columns: List[str]):
        self._data = [{k: row[k] for k in columns if k in row} for row in self._data]
        self._headers = columns
        return self
    
    def export(self, output_path: str) -> str:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if self._data:
                writer = csv.DictWriter(f, fieldnames=self._headers)
                writer.writeheader()
                writer.writerows(self._data)
        return output_path
""",
                "mime_type": "text/x-python",
            },
            {
                "filename": "README.md",
                "content": "# CSV Data Processor\n\n读取、过滤和导出 CSV 数据的通用技能包。\n",
                "mime_type": "text/markdown",
            },
        ],
    },
    {
        "name": "http-request-tool",
        "version": "2.0.1",
        "category": "网络工具",
        "description": "发送 HTTP 请求的简单工具，支持 GET/POST/PUT/DELETE，自动处理 JSON 和认证。",
        "tags": ["python", "http", "api", "网络"],
        "star_count": 87,
        "download_count": 312,
        "readme": """# HTTP Request Tool

简单易用的 HTTP 请求工具，基于 httpx 封装。

## 安装依赖

```bash
pip install httpx
```

## 使用示例

```python
from skill import HttpClient

client = HttpClient(base_url="https://api.example.com")
response = client.get("/users", params={"page": 1})
print(response.json())
```
""",
        "skill_md": None,
        "files": [
            {
                "filename": "skill.py",
                "content": """import httpx
from typing import Any, Dict, Optional

class HttpClient:
    \"\"\"HTTP 请求客户端\"\"\"
    
    def __init__(self, base_url: str = "", headers: Optional[Dict] = None):
        self.base_url = base_url.rstrip("/")
        self.default_headers = headers or {}
    
    def get(self, path: str, params: Optional[Dict] = None) -> httpx.Response:
        url = self.base_url + path
        return httpx.get(url, params=params, headers=self.default_headers)
    
    def post(self, path: str, json: Any = None, data: Any = None) -> httpx.Response:
        url = self.base_url + path
        return httpx.post(url, json=json, data=data, headers=self.default_headers)
    
    def put(self, path: str, json: Any = None) -> httpx.Response:
        url = self.base_url + path
        return httpx.put(url, json=json, headers=self.default_headers)
    
    def delete(self, path: str) -> httpx.Response:
        url = self.base_url + path
        return httpx.delete(url, headers=self.default_headers)
""",
                "mime_type": "text/x-python",
            },
        ],
    },
    {
        "name": "pdf-text-extractor",
        "version": "1.0.0",
        "category": "文件操作",
        "description": "从 PDF 文件中提取文本内容，支持多页提取和格式保留。",
        "tags": ["python", "pdf", "文本提取"],
        "star_count": 31,
        "download_count": 98,
        "readme": """# PDF Text Extractor

从 PDF 文件提取文本的技能包。

## 依赖

```bash
pip install pypdf2
```

## 使用示例

```python
from skill import PdfExtractor

extractor = PdfExtractor("document.pdf")
text = extractor.extract_all()
page_text = extractor.extract_page(1)
```
""",
        "skill_md": """# SKILL
name: pdf-text-extractor
version: 1.0.0
description: PDF 文本提取技能
""",
        "files": [
            {
                "filename": "skill.py",
                "content": """try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

class PdfExtractor:
    \"\"\"PDF 文本提取器\"\"\"
    
    def __init__(self, filepath: str):
        self.filepath = filepath
    
    def extract_all(self) -> str:
        if PyPDF2 is None:
            raise ImportError("Please install pypdf2: pip install pypdf2")
        texts = []
        with open(self.filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                texts.append(page.extract_text() or "")
        return "\\n".join(texts)
    
    def extract_page(self, page_num: int) -> str:
        if PyPDF2 is None:
            raise ImportError("Please install pypdf2: pip install pypdf2")
        with open(self.filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            if page_num < 1 or page_num > len(reader.pages):
                raise ValueError(f"Page {page_num} out of range")
            return reader.pages[page_num - 1].extract_text() or ""
""",
                "mime_type": "text/x-python",
            },
            {
                "filename": "SKILL.md",
                "content": "# SKILL\nname: pdf-text-extractor\nversion: 1.0.0\n",
                "mime_type": "text/markdown",
            },
        ],
    },
    {
        "name": "ai-text-summarizer",
        "version": "1.1.0",
        "category": "AI工具",
        "description": "使用大模型 API 对长文本进行自动摘要，支持多种摘要长度和风格设置。",
        "tags": ["python", "ai", "nlp", "摘要", "llm"],
        "star_count": 120,
        "download_count": 450,
        "readme": """# AI Text Summarizer

基于大模型的文本摘要技能。

## 使用示例

```python
from skill import TextSummarizer

summarizer = TextSummarizer(api_key="your-api-key")
summary = summarizer.summarize(long_text, max_length=200)
print(summary)
```

## 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| max_length | 200 | 摘要最大字数 |
| style | "concise" | 摘要风格 |
""",
        "skill_md": """# SKILL
name: ai-text-summarizer
version: 1.1.0
description: AI 文本摘要技能
category: AI工具
tags: [python, ai, nlp]
""",
        "files": [
            {
                "filename": "skill.py",
                "content": """import json
from typing import Optional

class TextSummarizer:
    \"\"\"AI 文本摘要器（示例实现）\"\"\"
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
    
    def summarize(self, text: str, max_length: int = 200, style: str = "concise") -> str:
        # 实际使用时替换为真实 API 调用
        if len(text) <= max_length:
            return text
        # 简单截断示例
        return text[:max_length] + "..."
    
    def batch_summarize(self, texts: list, max_length: int = 200) -> list:
        return [self.summarize(t, max_length) for t in texts]
""",
                "mime_type": "text/x-python",
            },
        ],
    },
    {
        "name": "file-organizer",
        "version": "1.0.2",
        "category": "系统工具",
        "description": "按照规则自动整理文件夹中的文件，支持按扩展名、日期、大小分类。",
        "tags": ["python", "文件", "自动化", "系统"],
        "star_count": 55,
        "download_count": 203,
        "readme": """# File Organizer

自动整理文件夹的技能包。

## 使用示例

```python
from skill import FileOrganizer

organizer = FileOrganizer("/path/to/folder")
organizer.organize_by_extension()
organizer.organize_by_date()
```
""",
        "skill_md": None,
        "files": [
            {
                "filename": "skill.py",
                "content": """import os
import shutil
from datetime import datetime
from pathlib import Path

class FileOrganizer:
    \"\"\"文件整理工具\"\"\"
    
    def __init__(self, folder_path: str):
        self.folder = Path(folder_path)
    
    def organize_by_extension(self) -> dict:
        moved = {}
        for file in self.folder.iterdir():
            if file.is_file():
                ext = file.suffix.lower().lstrip(".")
                target_dir = self.folder / (ext if ext else "no_extension")
                target_dir.mkdir(exist_ok=True)
                dest = target_dir / file.name
                shutil.move(str(file), str(dest))
                moved[file.name] = str(dest)
        return moved
    
    def organize_by_date(self) -> dict:
        moved = {}
        for file in self.folder.iterdir():
            if file.is_file():
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                date_str = mtime.strftime("%Y-%m")
                target_dir = self.folder / date_str
                target_dir.mkdir(exist_ok=True)
                dest = target_dir / file.name
                shutil.move(str(file), str(dest))
                moved[file.name] = str(dest)
        return moved
""",
                "mime_type": "text/x-python",
            },
        ],
    },
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        # 创建 seed 用户
        user = db.query(User).filter(User.github_id == SEED_USER["github_id"]).first()
        if not user:
            user = User(**SEED_USER)
            db.add(user)
            db.flush()
            print(f"✅ Created seed user: {user.login}")
        else:
            print(f"ℹ️  Seed user already exists: {user.login}")

        # 创建 seed skills
        upload_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
        for skill_data in SEED_SKILLS:
            existing = db.query(Skill).filter(Skill.name == skill_data["name"]).first()
            if existing:
                print(f"ℹ️  Skill '{skill_data['name']}' already exists, skipping")
                continue

            files_data = skill_data["files"]
            readme = skill_data.get("readme")
            skill_md = skill_data.get("skill_md")

            skill = Skill(
                name=skill_data["name"],
                version=skill_data["version"],
                description=skill_data.get("description"),
                category=skill_data.get("category"),
                tags=json.dumps(skill_data.get("tags", []), ensure_ascii=False),
                readme=readme,
                skill_md=skill_md,
                author_id=user.id,
                is_public=True,
                star_count=skill_data.get("star_count", 0),
                download_count=skill_data.get("download_count", 0),
            )
            db.add(skill)
            db.flush()

            skill_dir = os.path.join(upload_base, str(skill.id))
            os.makedirs(skill_dir, exist_ok=True)

            for file_info in files_data:
                file_path = os.path.join(skill_dir, file_info["filename"])
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_info["content"])
                file_record = SkillFile(
                    skill_id=skill.id,
                    filename=file_info["filename"],
                    file_path=file_path,
                    file_size=len(file_info["content"].encode("utf-8")),
                    mime_type=file_info.get("mime_type", "text/plain"),
                )
                db.add(file_record)

            print(f"✅ Created skill: {skill.name}")

        db.commit()
        print("\n🎉 Seed data initialized successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Seed error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    seed()
