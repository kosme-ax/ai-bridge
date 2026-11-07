from __future__ import annotations

import io
import json
from datetime import datetime
from typing import Any

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _plain(result: dict[str, Any]) -> str:
    lines = [
        f"생성시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"모델: {((result.get('_meta') or {}).get('model_name'))}",
        f"모드: {((result.get('_meta') or {}).get('mode'))}",
        "",
        result.get("summary") or "",
        "",
        json.dumps({k: v for k, v in result.items() if k != "_meta"}, ensure_ascii=False, indent=2),
    ]
    return "\n".join(lines)


def to_pdf_bytes(title: str, result: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    for line in _plain(result).splitlines():
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(safe or " ", styles["Normal"]))
        story.append(Spacer(1, 4))
    doc.build(story)
    return buf.getvalue()


def to_docx_bytes(title: str, result: dict[str, Any]) -> bytes:
    document = Document()
    document.add_heading(title, level=1)
    for line in _plain(result).splitlines():
        document.add_paragraph(line)
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()
