import httpx
from typing import Any, Dict, Optional

class HttpClient:
    """HTTP 请求客户端"""
    
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
