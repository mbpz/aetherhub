import csv
from typing import List, Optional

class CsvProcessor:
    """CSV 数据处理器"""
    
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
