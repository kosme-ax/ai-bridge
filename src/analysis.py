from __future__ import annotations

from typing import Any

from src.llm import generate_json
from src.prompt_templates import build_fitness_context, quotation_prompt, work_order_prompt

_PROMPT_KEYS = ("_prompt", "prompt", "raw_prompt", "system_prompt")


def generate_work_order(
    model_name: str,
    company: dict[str, Any],
    diagnosis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """표준 RFP/과업지시서 초안. 상세 프롬프트는 UI에 노출하지 않음."""
    kdoctor = company.get("kdoctor") or {}
    fitness = company.get("fitness") or (diagnosis or {}).get("fitness") or {}
    ai_areas = list(fitness.get("ai_areas") or kdoctor.get("ai_areas") or [])
    ai_problems = list(fitness.get("ai_problems") or kdoctor.get("ai_problems") or [])
    extra = {
        k: v
        for k, v in (diagnosis or {}).items()
        if k not in {"fitness", "kdoctor"} and not str(k).startswith("_")
    }
    context = "\n".join(
        [
            f"기업명: {company.get('name')}",
            f"업종: {company.get('industry')}",
            f"인원: {company.get('employees')}",
            f"주요업무: {company.get('main_tasks')}",
            f"IT현황: {company.get('it_summary')}",
            f"고충: {company.get('pain_points')}",
            f"K-Doctor: {kdoctor.get('diagnosis_id')} / AX수준 {kdoctor.get('ax_level')}",
            f"K-Doctor요약: {kdoctor.get('summary')}",
            f"K-Doctor우선과제: {kdoctor.get('priority_tasks')}",
            build_fitness_context(fitness),
            f"추가입력키: {list(extra.keys())}",
        ]
    )
    prompt = work_order_prompt(context=context, ai_areas=ai_areas, ai_problems=ai_problems)
    result = generate_json(model_name, "work_order", prompt, context)
    for key in _PROMPT_KEYS:
        result.pop(key, None)
    result.setdefault("document_type", "표준RFP/과업지시서")
    result.setdefault(
        "fitness_basis",
        {
            "industry": fitness.get("industry") or company.get("industry"),
            "ai_areas": ai_areas,
            "ai_problems": ai_problems,
            "level": fitness.get("level"),
            "label": fitness.get("label"),
            "tip": fitness.get("tip"),
        },
    )
    result.setdefault("target_ai_areas", ai_areas)
    result.setdefault("target_problems", ai_problems)
    return result


def compare_quotations(model_name: str, company: dict[str, Any], quote_text: str) -> dict[str, Any]:
    context = (
        f"기업: {company.get('name')}\n"
        f"K-Doctor 연계 우선과제: {(company.get('kdoctor') or {}).get('priority_tasks')}\n"
        f"기초체력: {build_fitness_context(company.get('fitness'))}\n"
        f"견적자료:\n{quote_text[:14000]}"
    )
    prompt = quotation_prompt(context=context)
    result = generate_json(model_name, "quotation", prompt, context)
    for key in _PROMPT_KEYS:
        result.pop(key, None)
    return result
