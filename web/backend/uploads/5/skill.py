import os
import shutil
from datetime import datetime
from pathlib import Path

class FileOrganizer:
    """文件整理工具"""
    
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
