try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

class PdfExtractor:
    """PDF 文本提取器"""
    
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
        return "\n".join(texts)
    
    def extract_page(self, page_num: int) -> str:
        if PyPDF2 is None:
            raise ImportError("Please install pypdf2: pip install pypdf2")
        with open(self.filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            if page_num < 1 or page_num > len(reader.pages):
                raise ValueError(f"Page {page_num} out of range")
            return reader.pages[page_num - 1].extract_text() or ""
