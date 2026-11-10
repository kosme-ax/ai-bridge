from __future__ import annotations

import json
import re
from typing import Any

import httpx

from src.config import runtime_settings

JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", re.DOTALL)

SYSTEM = """당신은 공공기관 기업지원 담당자를 돕는 AX(AI 전환) 컨설턴트입니다.
한국어로 답합니다. 확인되지 않은 절감률·시장가격을 만들지 마십시오.
근거가 부족하면 부족하다고 명시하고, 사람이 검토할 위험을 빠뜨리지 마십시오.
반드시 JSON만 출력합니다."""


def extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    text = text.strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    match = JSON_FENCE.search(text)
    if match:
        try:
            parsed = json.loads(match.group(1))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _mock_company(context: str) -> str:
    if "한빛" in context:
        return "(합성) 한빛정밀"
    if "푸른" in context:
        return "(합성) 푸른식품"
    return "가상기업"


def _mock_payload(task: str, context: str) -> dict[str, Any]:
    company = _mock_company(context)
    base = {
        "summary": f"{company} 합성 시연 결과입니다. API 키가 없어 Mock으로 생성했습니다.",
        "human_review_risks": [
            "최종 지원 결정은 담당자가 합니다.",
            "실제 수치·단가는 별도 검증이 필요합니다.",
        ],
    }
    if task == "quotation":
        return {
            **base,
            "currency": "KRW",
            "vendors": [
                {
                    "name": "공급사 A(합성)",
                    "supply_amount": 12000000,
                    "vat_amount": 1200000,
                    "total_amount": 13200000,
                    "notes": "GPU 서버 포함",
                },
                {
                    "name": "공급사 B(합성)",
                    "supply_amount": 9800000,
                    "vat_amount": 980000,
                    "total_amount": 10780000,
                    "notes": "클라우드 추론 옵션",
                },
            ],
            "comparison_notes": [
                "단가 차이만으로 부적정으로 단정하지 마십시오.",
                "범위·유지보수·데이터 반출 조건을 함께 보십시오.",
            ],
            "recommendation": "범위가 동일한지 확인한 뒤 기술·보안·유지보수 항목을 우선 비교하십시오.",
        }
    if task == "vendors":
        return {
            **base,
            "summary": f"{company} 적용 영역·고충에 맞춰 카탈로그 공급사를 Mock 추천했습니다.",
            "recommendations": [
                {"id": "ato", "score": 9, "why": "품질·비전 검사 PoC에 적합"},
                {"id": "runup", "score": 8, "why": "MES·ERP 연계·공정 자동화에 적합"},
                {"id": "twim", "score": 7, "why": "제조 외관검사 레퍼런스가 많음"},
                {"id": "upstage", "score": 6, "why": "문서·LLM 업무자동화 후보"},
                {"id": "bizarim", "score": 6, "why": "MES·제조 AI 연계 후보"},
                {"id": "intelliz", "score": 5, "why": "중소 제조 보급형 비전 후보"},
            ],
        }
    if task == "policies":
        return {
            **base,
            "summary": f"{company} AX 후속 실행에 맞는 정책·자금을 Mock 추천했습니다.",
            "recommendations": [
                {"id": "tech_finance", "score": 9, "why": "설비·시스템 도입 자금이 필요할 때"},
                {"id": "smart_factory_loan", "score": 8, "why": "스마트화·ICT 설비와 맞음"},
                {"id": "regional_ai", "score": 7, "why": "지역 AI·AX 지원 사업과 연계"},
            ],
        }

    areas = "품질관리 · 공정/설비"
    problems = "외관·치수 검사 숙련 의존 / 공정 병목 원인 파악 어려움"
    if "품질" in context:
        areas = "품질관리" + (" · 공정/설비" if "공정" in context else "")
    if "라벨" in context or "물류" in context:
        areas = "품질관리 · 물류"
        problems = "검사 데이터 미축적 / 출하·재고 실사 오차"
    area_list = [a.strip() for a in areas.split("·")]
    problem_list = [p.strip() for p in problems.split("/")]
    return {
        **base,
        "document_type": "표준RFP/과업지시서",
        "title": f"{company} AX 지원 표준 RFP·과업지시서 초안",
        "summary": (
            f"{company}의 기초체력 설문(적용 영역: {areas})을 반영한 "
            "표준 RFP/과업지시서 Mock 초안입니다."
        ),
        "target_ai_areas": area_list,
        "target_problems": problem_list,
        "fitness_basis": {
            "industry": "제조업",
            "ai_areas": area_list,
            "ai_problems": problem_list,
            "level": "mid",
            "label": "보완 필요",
        },
        "objectives": [
            f"{areas} 영역에 AI 보조 도입 범위·검수기준 확정",
            "현장 PoC로 효과·리스크 검증 후 확산 여부 결정",
        ],
        "scope": {
            "in_scope": ["PoC 1개 라인/업무", "데이터 연계 초안", "운영 매뉴얼"],
            "out_of_scope": ["전사 ERP 재구축", "확정 단가·계약"],
        },
        "deliverables": ["과업지시서/RFP", "PoC 결과보고서", "운영매뉴얼", "검수기록"],
        "schedule_phases": [
            {"phase": "착수·현황", "weeks": 2, "tasks": ["요구사항 확정", "데이터 샘플 점검"]},
            {"phase": "구축·시험", "weeks": 6, "tasks": ["모델/연계 PoC", "현장 시험"]},
            {"phase": "이관·보고", "weeks": 2, "tasks": ["교육", "결과보고"]},
        ],
        "roles": {
            "발주": "수요기업 (범위·데이터·검수)",
            "수행": "공급사 (구축·시험·이관)",
            "검수": "수요기업·중진공 담당자",
        },
        "acceptance_criteria": [
            "합의된 샘플 세트에서 재현 가능한 시험 결과",
            "데이터 반출·접근통제 조건 준수",
            "운영 매뉴얼·인수인계 완료",
        ],
        "sections": {
            "사업개요": f"{company} AX 지원을 위한 AI 도입 PoC. 적용 영역은 {areas}.",
            "추진배경및필요성": (
                f"기초체력 설문에서 '{problems}'가 우선 과제로 확인되어, "
                "진단 이후 실행문서(표준 RFP)로 범위를 고정할 필요가 있음."
            ),
            "현황및문제점": (
                f"현장 고충과 설문 결과를 종합하면 {problems}이(가) 핵심 병목임. "
                "숙련 의존·데이터 단절로 품질·일정 리스크가 큼."
            ),
            "기초체력진단요약": (
                f"업종 제조 가정, AI 적용 영역 {areas}, 해결 문제 {problems}. "
                "사업·데이터·운영 준비도는 보완 필요 수준(Mock)."
            ),
            "사업목표": "PoC 범위에서 보조 판정/자동화 효과와 운영 가능성을 검증하고 확산 기준을 마련.",
            "과업범위": "In: 선택 영역 PoC·데이터 연계 초안. Out: 전사 시스템 교체·확정 계약.",
            "세부과업내용": "①착수·현황 ②요구·설계 ③구축 ④시험 ⑤이관·보고 순으로 수행.",
            "기능요구사항": "데이터 수집·추론(또는 자동화)·이력 조회·권한 관리.",
            "데이터요구사항": "학습/시험 데이터 범위, 품질, 반출 금지 옵션, 개인·영업비밀 분리.",
            "보안요구사항": "접근통제, 망 분리/VPN, 로그, 공급사 계정 관리.",
            "추진일정": "착수 2주 → 구축·시험 6주 → 이관 2주 (가정, 협의 조정).",
            "역할분담": "발주=기업, 수행=공급사, 검수=기업·중진공.",
            "산출물": "RFP/과업지시서, PoC 보고서, 운영매뉴얼, 검수기록.",
            "검수및테스트기준": "합의 샘플 재현 시험, 보안 점검, 인수인계 체크리스트.",
            "제안요청및평가기준": "범위 적합도·기술·보안·유지보수를 단가보다 우선 평가.",
            "제출서류": "제안서, 수행계획, 보안확약, 유사사업 실적, 검수 계획.",
        },
        "assumptions": ["시연용 합성 데이터", "실 API·실계약 전 단계"],
        "linked_diagnosis_points": [problems],
    }


def _call_openai_compatible(
    cfg: dict[str, Any],
    prompt: str,
    *,
    system: str = SYSTEM,
    temperature: float = 0.2,
) -> str:
    """OpenAI Chat Completions 호환 (Solar / OpenRouter Llama / GPT / EXAONE)."""
    url = f"{cfg['base_url'].rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    if "openrouter.ai" in str(cfg.get("base_url") or ""):
        headers["HTTP-Referer"] = "https://sme-ax.streamlit.app"
        headers["X-Title"] = "sme-ax-helper"
    # EXAONE 등 느린 응답 대비: 읽기 타임아웃을 넉넉히, 출력 상한 지정
    body: dict[str, Any] = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": 4096,
    }
    timeout = httpx.Timeout(10.0, read=180.0, write=30.0, pool=10.0)
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]


def _call_google(
    cfg: dict[str, Any],
    prompt: str,
    *,
    system: str = SYSTEM,
    temperature: float = 0.2,
) -> str:
    model = cfg["model"]
    url = f"{cfg['base_url'].rstrip('/')}/models/{model}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": cfg["api_key"]}
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
            "maxOutputTokens": 4096,
        },
    }
    timeout = httpx.Timeout(10.0, read=180.0, write=30.0, pool=10.0)
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    text = ""
    for cand in data.get("candidates") or []:
        for part in (cand.get("content") or {}).get("parts") or []:
            text += part.get("text") or ""
    return text


def generate_json(model_name: str, task: str, prompt: str, context: str = "") -> dict[str, Any]:
    """선택된 모델로 분석 요청. 키 없으면 Mock."""
    settings = runtime_settings()
    if model_name not in settings["models"]:
        raise ValueError(f"등록되지 않은 모델: {model_name}")
    cfg = settings["models"][model_name]
    meta = {
        "model_name": model_name,
        "provider": cfg["provider"],
        "model_id": cfg["model"],
        "mode": "live" if cfg.get("api_key") else "mock",
    }
    if not cfg.get("api_key"):
        payload = _mock_payload(task, context or prompt)
        payload["_meta"] = meta
        return payload

    try:
        if cfg["provider"] == "openai_compatible":
            content = _call_openai_compatible(cfg, prompt)
        elif cfg["provider"] == "google":
            content = _call_google(cfg, prompt)
        else:
            raise ValueError(f"지원하지 않는 provider: {cfg['provider']}")
        payload = extract_json(content) or {"raw_text": content, "summary": content[:800]}
        payload["_meta"] = meta
        return payload
    except Exception as exc:
        payload = _mock_payload(task, context or prompt)
        payload["_meta"] = {**meta, "mode": "mock_fallback", "error": str(exc)[:300]}
        payload["summary"] = f"API 호출 실패로 Mock으로 대체했습니다. ({exc.__class__.__name__})"
        return payload
