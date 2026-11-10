from __future__ import annotations

import io

import pandas as pd


def read_upload(name: str, raw: bytes) -> str:
    """업로드 파일을 텍스트로 추출. 영구 저장하지 않는다."""
    lower = name.lower()
    if lower.endswith((".txt", ".md", ".csv")):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("cp949", errors="ignore")
        if lower.endswith(".csv"):
            try:
                return pd.read_csv(io.BytesIO(raw)).to_csv(index=False)
            except Exception:
                return text
        return text
    if lower.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if lower.endswith(".docx"):
        from docx import Document

        doc = Document(io.BytesIO(raw))
        return "\n".join(p.text for p in doc.paragraphs if p.text)
    if lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(raw)).to_csv(index=False)
    return raw.decode("utf-8", errors="ignore")
