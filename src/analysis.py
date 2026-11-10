from __future__ import annotations

from typing import Any

from src.llm import generate_json
from src.policies import POLICIES, recommend_policies
from src.prompt_templates import (
    build_fitness_context,
    policy_prompt,
    quotation_prompt,
    vendor_prompt,
    work_order_prompt,
)
from src.vendors import VENDORS, recommend_vendors

_PROMPT_KEYS = ("_prompt", "prompt", "raw_prompt", "system_prompt")


def _strip_prompt_keys(result: dict[str, Any]) -> dict[str, Any]:
    for key in _PROMPT_KEYS:
        result.pop(key, None)
    return result


def _company_context(
    company: dict[str, Any],
    *,
    fitness: dict[str, Any] | None = None,
    work_order: dict[str, Any] | None = None,
) -> str:
    kdoctor = company.get("kdoctor") or {}
    fit = fitness or company.get("fitness") or {}
    lines = [
        f"기업명: {company.get('name')}",
        f"업종: {company.get('industry')}",
        f"인원: {company.get('employees')}",
        f"주요업무: {company.get('main_tasks')}",
        f"IT현황: {company.get('it_summary')}",
        f"고충: {company.get('pain_points')}",
        f"K-Doctor: {kdoctor.get('diagnosis_id')} / AX수준 {kdoctor.get('ax_level')}",
        f"K-Doctor요약: {kdoctor.get('summary')}",
        f"K-Doctor우선과제: {kdoctor.get('priority_tasks')}",
        build_fitness_context(fit),
    ]
    if work_order:
        lines.append(f"과업지시서제목: {work_order.get('title')}")
        lines.append(f"과업지시서요약: {work_order.get('summary')}")
        lines.append(f"적용영역: {work_order.get('target_ai_areas')}")
        lines.append(f"해결문제: {work_order.get('target_problems')}")
    return "\n".join(str(x) for x in lines)


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
            _company_context(company, fitness=fitness),
            f"추가입력키: {list(extra.keys())}",
        ]
    )
    prompt = work_order_prompt(context=context, ai_areas=ai_areas, ai_problems=ai_problems)
    result = generate_json(model_name, "work_order", prompt, context)
    _strip_prompt_keys(result)
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
        f"{_company_context(company, fitness=company.get('fitness'))}\n"
        f"견적자료:\n{quote_text[:14000]}"
    )
    prompt = quotation_prompt(context=context)
    result = generate_json(model_name, "quotation", prompt, context)
    return _strip_prompt_keys(result)


def _vendor_catalog_text() -> str:
    lines = []
    for v in VENDORS:
        fit = ",".join(v.get("fit") or [])
        lines.append(
            f"{v['id']}|{v['name']}|{v.get('category','')}|{v.get('summary','')}|{fit}"
        )
    return "\n".join(lines)


def _policy_catalog_text() -> str:
    lines = []
    for p in POLICIES:
        tags = ",".join(p.get("tags") or [])
        lines.append(
            f"{p['id']}|{p['name']}|{p.get('org','')}|{p.get('category','')}|{p.get('summary','')}|{tags}"
        )
    return "\n".join(lines)


def _hydrate_from_catalog(
    *,
    catalog: list[dict[str, Any]],
    recommendations: list[Any],
    limit: int,
) -> list[dict[str, Any]]:
    by_id = {str(item["id"]): item for item in catalog}
    by_name = {str(item.get("name") or "").strip(): item for item in catalog}
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, row in enumerate(recommendations or []):
        if not isinstance(row, dict):
            continue
        raw_id = str(row.get("id") or row.get("vendor_id") or row.get("policy_id") or "").strip()
        item = by_id.get(raw_id)
        if item is None:
            name = str(row.get("name") or "").strip()
            item = by_name.get(name)
        if item is None or item["id"] in seen:
            continue
        hydrated = dict(item)
        score = row.get("score")
        try:
            hydrated["match_score"] = int(score)
        except (TypeError, ValueError):
            hydrated["match_score"] = max(1, limit - i)
        why = str(row.get("why") or "").strip()
        hydrated["why"] = why or f"AI 추천 · {item.get('category', '')}"
        out.append(hydrated)
        seen.add(item["id"])
        if len(out) >= limit:
            break
    return out


def rank_vendors(
    model_name: str,
    company: dict[str, Any],
    *,
    work_order: dict[str, Any] | None = None,
    fitness: dict[str, Any] | None = None,
    limit: int = 6,
) -> dict[str, Any]:
    """LLM으로 공급사 순위를 매기고 카탈로그 정보로 채운다."""
    context = _company_context(company, fitness=fitness, work_order=work_order)
    prompt = vendor_prompt(context=context, catalog=_vendor_catalog_text(), limit=limit)
    result = generate_json(model_name, "vendors", prompt, context)
    _strip_prompt_keys(result)
    recs = _hydrate_from_catalog(
        catalog=VENDORS,
        recommendations=result.get("recommendations") or [],
        limit=limit,
    )
    if not recs:
        recs = recommend_vendors(
            company=company, work_order=work_order, fitness=fitness, limit=limit
        )
        result["_meta"] = {
            **(result.get("_meta") or {}),
            "mode": "rule_fallback",
        }
    result["recommendations"] = recs
    return result


def rank_policies(
    model_name: str,
    company: dict[str, Any],
    *,
    fitness: dict[str, Any] | None = None,
    context_label: str = "work_order",
    limit: int = 3,
) -> dict[str, Any]:
    """LLM으로 정책 순위를 매기고 카탈로그 정보로 채운다."""
    context = (
        f"{_company_context(company, fitness=fitness)}\n"
        f"추천맥락: {context_label}"
    )
    prompt = policy_prompt(context=context, catalog=_policy_catalog_text(), limit=limit)
    result = generate_json(model_name, "policies", prompt, context)
    _strip_prompt_keys(result)
    recs = _hydrate_from_catalog(
        catalog=POLICIES,
        recommendations=result.get("recommendations") or [],
        limit=limit,
    )
    if not recs:
        recs = recommend_policies(
            fitness=fitness, company=company, context=context_label, limit=limit
        )
        result["_meta"] = {
            **(result.get("_meta") or {}),
            "mode": "rule_fallback",
        }
    result["recommendations"] = recs
    return result
