"""PDF/DOCX 문서화 — 표준 RFP·과업지시서 본문만 출력 (프롬프트·원본 JSON 비공개)."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
FONT_CANDIDATES = [
    ROOT / "assets" / "fonts" / "NanumGothic.ttf",
    Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
    Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
]

_FONT_NAME = "Helvetica"
_FONT_READY = False

# 표준 RFP 섹션 출력 순서
RFP_SECTION_ORDER = (
    ("사업개요", "1. 사업개요"),
    ("추진배경및필요성", "2. 추진배경 및 필요성"),
    ("현황및문제점", "3. 현황 및 문제점"),
    ("기초체력진단요약", "4. 기초체력 진단 요약"),
    ("사업목표", "5. 사업 목표"),
    ("과업범위", "6. 과업 범위"),
    ("세부과업내용", "7. 세부 과업 내용"),
    ("기능요구사항", "8. 기능 요구사항"),
    ("데이터요구사항", "9. 데이터 요구사항"),
    ("보안요구사항", "10. 보안 요구사항"),
    ("추진일정", "11. 추진 일정"),
    ("역할분담", "12. 역할 분담"),
    ("산출물", "13. 산출물"),
    ("검수및테스트기준", "14. 검수 및 테스트 기준"),
    ("제안요청및평가기준", "15. 제안 요청 및 평가 기준"),
    ("제출서류", "16. 제출 서류"),
)

_PRIVATE_KEYS = {"_meta", "_prompt", "prompt", "raw_prompt", "system_prompt"}


def _ensure_font() -> str:
    global _FONT_NAME, _FONT_READY
    if _FONT_READY:
        return _FONT_NAME
    for path in FONT_CANDIDATES:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont("KRDocFont", str(path)))
                _FONT_NAME = "KRDocFont"
                _FONT_READY = True
                return _FONT_NAME
            except Exception:
                continue
    _FONT_READY = True
    return _FONT_NAME


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _as_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, dict):
        lines = []
        for k, v in value.items():
            if isinstance(v, (list, tuple)):
                lines.append(f"{k}:")
                lines.extend(f"  - {x}" for x in v)
            else:
                lines.append(f"{k}: {v}")
        return lines
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            if isinstance(item, dict):
                bits = [f"{k}={v}" for k, v in item.items()]
                out.append("- " + ", ".join(bits))
            else:
                out.append(f"- {item}")
        return out
    return [str(value)]


def document_lines(title: str, result: dict[str, Any]) -> list[str]:
    """사람이 읽는 문서 본문 줄 목록 (프롬프트·메타 제외)."""
    lines = [
        title,
        f"작성시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"문서유형: {result.get('document_type') or 'AX 지원 문서'}",
        "",
    ]
    if result.get("title") and result["title"] != title:
        lines.append(str(result["title"]))
        lines.append("")
    if result.get("summary"):
        lines.append("[요약]")
        lines.extend(_as_lines(result["summary"]))
        lines.append("")

    basis = result.get("fitness_basis") or {}
    if basis:
        lines.append("[기초체력 반영]")
        if basis.get("industry"):
            lines.append(f"업종: {basis['industry']}")
        if basis.get("ai_areas"):
            lines.append("AI 적용 영역: " + " · ".join(basis["ai_areas"]))
        if basis.get("ai_problems"):
            lines.append("해결 문제: " + " · ".join(basis["ai_problems"]))
        if basis.get("level"):
            lines.append(f"준비도: {basis.get('label') or basis['level']}")
        lines.append("")

    sections = result.get("sections") or {}
    if isinstance(sections, dict) and sections:
        for key, heading in RFP_SECTION_ORDER:
            body = sections.get(key)
            if body in (None, "", [], {}):
                continue
            lines.append(heading)
            lines.extend(_as_lines(body))
            lines.append("")
        # 정의 외 섹션
        known = {k for k, _ in RFP_SECTION_ORDER}
        for key, body in sections.items():
            if key in known or body in (None, "", [], {}):
                continue
            lines.append(str(key))
            lines.extend(_as_lines(body))
            lines.append("")
    else:
        # 일반 결과물
        for key, value in result.items():
            if key in _PRIVATE_KEYS or key in {
                "summary",
                "title",
                "document_type",
                "sections",
                "fitness_basis",
            }:
                continue
            lines.append(f"[{key}]")
            lines.extend(_as_lines(value))
            lines.append("")

    risks = result.get("human_review_risks") or []
    if risks:
        lines.append("[담당자 검토 필요]")
        lines.extend(_as_lines(risks))

    return lines


def to_pdf_bytes(title: str, result: dict[str, Any]) -> bytes:
    font = _ensure_font()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "KRTitle",
        parent=styles["Title"],
        fontName=font,
        fontSize=16,
        leading=22,
        spaceAfter=10,
    )
    h_style = ParagraphStyle(
        "KRHeading",
        parent=styles["Heading2"],
        fontName=font,
        fontSize=11,
        leading=16,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "KRBody",
        parent=styles["Normal"],
        fontName=font,
        fontSize=9.5,
        leading=14,
    )

    story: list[Any] = []
    for i, line in enumerate(document_lines(title, result)):
        safe = _esc(line) or " "
        if i == 0:
            story.append(Paragraph(safe, title_style))
        elif line.startswith("[") or (len(line) > 2 and line[0].isdigit() and ". " in line[:4]):
            story.append(Paragraph(safe, h_style))
        else:
            story.append(Paragraph(safe, body_style))
        story.append(Spacer(1, 2))
    doc.build(story)
    return buf.getvalue()


def to_docx_bytes(title: str, result: dict[str, Any]) -> bytes:
    document = Document()
    for i, line in enumerate(document_lines(title, result)):
        if i == 0:
            document.add_heading(line, level=1)
        elif line.startswith("[") or (len(line) > 2 and line[0].isdigit() and ". " in line[:4]):
            document.add_heading(line.lstrip("[").rstrip("]"), level=2)
        else:
            document.add_paragraph(line)
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()
