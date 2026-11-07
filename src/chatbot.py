"""상단 AI 상담 챗봇 — 기초체력·과업·견적·정책을 대화로 안내."""

from __future__ import annotations

import json
from typing import Any

from src.llm import generate_chat
from src.policies import POLICIES, recommend_policies

CHAT_SYSTEM = """당신은 AI-Bridge 상담 도우미입니다.
중진공 AX 지원 업무를 돕는 Streamlit 앱의 가이드입니다.

앱 기능:
1) 기초체력 — 데이터 Fitness 8문항 자가진단, 등급·교육 링크
2) 과업지시서 — K-Doctor 진단 이후 AX 과업지시서 초안
3) 견적 비교 — 공급사 견적 비교 (단가 차이만으로 부적정 단정 금지)
4) 정책연계 — 기술자금·스마트화·지역주도형 AI 대전환 등 추천
5) 더보기 — CSV 검증, K-Doctor 연동, 시스템 분석, 모델 비교

규칙:
- 한국어, 짧고 토스처럼 친절하게.
- 확인되지 않은 시장가·절감률을 만들지 말 것.
- 사용자가 화면 메뉴로 가도록 안내하고, 필요하면 질문으로 정보 수집.
- 정책 일정·조건은 요약만 하고 공식 공고 확인을 권고.
- 로그인·DB 없음을 묻으면: 세션만 사용, 업로드 비저장이라고 안내.
"""


def build_context(
    *,
    company: dict[str, Any] | None,
    fitness: dict[str, Any] | None,
    last_title: str,
    last_result: dict[str, Any] | None,
    page: str,
) -> str:
    kd = (company or {}).get("kdoctor") or {}
    recs = recommend_policies(fitness=fitness, company=company, context="general", limit=3)
    blob = {
        "current_page": page,
        "company": {
            "name": (company or {}).get("name"),
            "industry": (company or {}).get("industry"),
            "kdoctor": {
                "diagnosis_id": kd.get("diagnosis_id"),
                "ax_level": kd.get("ax_level"),
                "summary": kd.get("summary"),
                "priority_tasks": kd.get("priority_tasks"),
            },
        },
        "fitness": {
            "label": (fitness or {}).get("label"),
            "level": (fitness or {}).get("level"),
            "total": (fitness or {}).get("total"),
            "tip": (fitness or {}).get("tip"),
        }
        if fitness
        else None,
        "last_title": last_title,
        "last_summary": (last_result or {}).get("summary"),
        "policy_catalog": [
            {
                "name": p["name"],
                "period": p["period"],
                "contact": p["contact"],
                "apply": p["apply"],
            }
            for p in POLICIES
        ],
        "recommended_now": [{"name": r["name"], "why": r.get("why")} for r in recs],
    }
    return json.dumps(blob, ensure_ascii=False)


def _mock_reply(user_text: str, context_json: str) -> str:
    text = user_text.lower()
    try:
        ctx = json.loads(context_json)
    except json.JSONDecodeError:
        ctx = {}
    company = ((ctx.get("company") or {}).get("name")) or "선택 기업"

    if any(k in user_text for k in ("기초", "체력", "피트니스", "자가진단")):
        fit = ctx.get("fitness")
        if fit:
            return (
                f"지금 {company} 기초체력은 **{fit.get('label')}** "
                f"({fit.get('total')}점)입니다. {fit.get('tip')} "
                "메뉴 「기초체력」에서 문항을 다시 조정할 수 있어요."
            )
        return "아직 기초체력 결과가 없어요. 상단 메뉴 「기초체력」에서 8문항을 체크해 주세요."

    if any(k in user_text for k in ("과업", "지시서", "rfp", "로드맵")):
        return (
            f"{company} 기준 과업지시서는 「과업지시서」 메뉴에서 만들 수 있어요. "
            "K-Doctor 우선과제와 기초체력이 있으면 초안이 더 구체적입니다. "
            "원하시면 우선 과업 범위를 알려 주세요."
        )

    if any(k in user_text for k in ("견적", "비교", "단가")):
        return (
            "「견적 비교」에서 샘플 A/B 또는 CSV를 넣고 비교할 수 있어요. "
            "단가 차이만으로 부적정이라고 단정하지 않고, 범위·유지보수·보안을 같이 봅니다."
        )

    if any(k in user_text for k in ("정책", "자금", "융자", "대전환", "기술자금")):
        recs = ctx.get("recommended_now") or []
        lines = [f"- {r.get('name')}: {r.get('why')}" for r in recs[:3]]
        body = "\n".join(lines) if lines else "- 정책연계 메뉴에서 전체 카탈로그를 보세요."
        return (
            "지금 상황에 맞춰 이런 중진공·중기부 창구를 봐요.\n"
            f"{body}\n"
            "일정·신청·담당은 「정책연계」 카드에 정리돼 있어요. (API 키 없을 때 Mock 안내)"
        )

    if any(k in text for k in ("csv", "엑셀", "파일명", "표준")):
        return (
            "「더보기 → CSV 검증」에서 기업현황 표준 컬럼·파일명"
            "(기업명_사업명_문서종류)을 검사합니다. 빈 템플릿도 받을 수 있어요."
        )

    return (
        f"안녕하세요. {company} 기준으로 도와드릴게요. "
        "기초체력, 과업지시서, 견적 비교, 정책자금(기술자금·지역 AI 대전환) 중 "
        "궁금한 걸 말해 주세요. (현재 Mock 상담 — API 키 있으면 더 자세히 답합니다)"
    )


def reply_chat(
    model_name: str,
    history: list[dict[str, str]],
    user_text: str,
    context_json: str,
) -> str:
    return generate_chat(
        model_name,
        system=CHAT_SYSTEM,
        history=history,
        user_text=user_text,
        context_json=context_json,
        mock_fn=_mock_reply,
    )
