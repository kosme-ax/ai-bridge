"""상단 AI 상담 챗봇 — 기초체력·과업·견적·정책을 대화로 안내."""

from __future__ import annotations

import json
from typing import Any

from src.llm import generate_chat
from src.policies import POLICIES, recommend_policies

CHAT_SYSTEM = """당신은 sme-ax-helper 상담 도우미입니다.
중진공 AX 지원 후속업무를 돕는 Streamlit 앱의 가이드입니다.

앱 실행 순서(반드시 이 순서로 안내):
1) 기초체력 — 우리 회사 AX 수준 진단: 보고서 업로드 또는 적용 영역·해결 문제·사업/데이터/운영 문항
2) 과업지시서 — 선택한 적용 영역을 반영한 표준 RFP/과업지시서
3) 업체 — AI 공급사 추천
4) 견적 — 공급사 견적 비교 (단가 차이만으로 부적정 단정 금지)
5) 정책 — 기술자금·스마트화·지역주도형 AI 대전환 등

규칙:
- 한국어, 짧고 토스처럼 친절하게.
- 확인되지 않은 시장가·절감률을 만들지 말 것.
- 다음 스텝 메뉴명으로 안내하고, 필요하면 질문으로 정보 수집.
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
            "industry": (fitness or {}).get("industry"),
            "ai_areas": (fitness or {}).get("ai_areas"),
            "ai_problems": (fitness or {}).get("ai_problems"),
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

    if any(k in user_text for k in ("기초", "체력", "피트니스", "자가진단", "적용")):
        fit = ctx.get("fitness")
        if fit:
            areas = fit.get("ai_areas") or []
            area_txt = " · ".join(areas) if areas else "미선택"
            return (
                f"지금 {company} 기초체력은 **{fit.get('label')}** "
                f"({fit.get('total')}점)이고, AI 적용 희망 영역은 **{area_txt}** 입니다. "
                f"{fit.get('tip')} STEP 1에서 다시 고를 수 있어요."
            )
        return (
            "아직 기초체력 결과가 없어요. STEP 1 「기초체력보기」에서 "
            "「기초체력」에서 우리 회사 AX 수준 진단부터 시작해 주세요."
        )

    if any(k in user_text for k in ("업체", "공급사", "벤더", "추천")):
        return (
            "STEP 3 「업체 탐색」에서 과업·진단 키워드로 AI 공급사를 골라 드려요. "
            "그다음 STEP 4 「견적비교」로 이어가면 됩니다."
        )

    if any(k in user_text for k in ("과업", "지시서", "rfp", "로드맵")):
        return (
            f"{company} 기준 과업은 STEP 2 「과업지시서 작성」에서 만들 수 있어요. "
            "끝나면 STEP 3 「업체 탐색」으로 넘어가세요."
        )

    if any(k in user_text for k in ("견적", "비교", "단가")):
        return (
            "STEP 4 「견적비교」에서 샘플 A/B 또는 CSV를 넣고 비교할 수 있어요. "
            "단가 차이만으로 부적정이라고 단정하지 않고, 범위·유지보수·보안을 같이 봅니다."
        )

    if any(k in user_text for k in ("정책", "자금", "융자", "대전환", "기술자금")):
        recs = ctx.get("recommended_now") or []
        lines = [f"- {r.get('name')}: {r.get('why')}" for r in recs[:3]]
        body = "\n".join(lines) if lines else "- STEP 5 「정책연계」에서 전체 카탈로그를 보세요."
        return (
            "지금 상황에 맞춰 이런 중진공·중기부 창구를 봐요.\n"
            f"{body}\n"
            "일정·신청·담당은 STEP 5 「정책연계」 카드에 정리돼 있어요."
        )

    return (
        f"안녕하세요. {company} 기준으로 도와드릴게요. "
        "순서는 ①기초체력(AX 수준 진단) → ②과업지시서 → ③업체 → ④견적 → ⑤정책 입니다. "
        "궁금한 스텝을 말해 주세요."
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
