# file_parser.py
"""
文档解析：docx / pdf / txt / xlsx 提取文本
"""
import io
from docx import Document
import PyPDF2
import pandas as pd


def extract_text(file_bytes: bytes, filename: str) -> str:
    """解析文件，返回文本"""
    lower_name = filename.lower()
    stream = io.BytesIO(file_bytes)

    if lower_name.endswith(".txt"):
        return stream.read().decode("utf-8", errors="ignore")
    elif lower_name.endswith(".docx"):
        doc = Document(stream)
        return "\n".join([p.text for p in doc.paragraphs])
    elif lower_name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(stream)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    elif lower_name.endswith((".xlsx", ".xls")):
        sheets = pd.read_excel(stream, sheet_name=None)
        out = []
        for name, df in sheets.items():
            out.append(f"===== 工作表 {name} =====")
            out.append(df.to_string())
        return "\n".join(out)
    else:
        return "不支持的文件类型"
