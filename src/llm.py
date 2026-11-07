from __future__ import annotations

import json
import re
from typing import Any

import httpx

from src.config import runtime_settings

JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", re.DOTALL)


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


SYSTEM = """당신은 공공기관 기업지원 담당자를 돕는 AX(AI 전환) 컨설턴트입니다.
한국어로 답합니다. 확인되지 않은 절감률·시장가격을 만들지 마십시오.
근거가 부족하면 부족하다고 명시하고, 사람이 검토할 위험을 빠뜨리지 마십시오.
반드시 JSON만 출력합니다."""


def _mock_payload(task: str, context: str) -> dict[str, Any]:
    company = "가상기업"
    if "한빛" in context:
        company = "(합성) 한빛정밀"
    elif "푸른" in context:
        company = "(합성) 푸른식품"
    base = {
        "summary": f"{company} 합성 시연 결과입니다. API 키가 없어 Mock으로 생성했습니다.",
        "human_review_risks": ["최종 지원 결정은 담당자가 합니다.", "실제 수치·단가는 별도 검증이 필요합니다."],
    }
    if task == "diagnosis":
        return {
            **base,
            "ax_readiness": "medium",
            "problems": [
                {"title": "월마감 수기 집계", "detail": "엑셀 수작업 비중이 높음", "severity": "high"},
                {"title": "생산-영업 데이터 단절", "detail": "시스템 간 수기 이관", "severity": "medium"},
            ],
            "candidate_tasks": ["외관 검사 AI 보조 PoC", "마감 엑셀 자동 초안"],
            "data_gaps": ["월 처리량", "라벨된 품질 데이터", "망 분리 여부"],
        }
    if task == "systems":
        return {
            **base,
            "duplicate_functions": ["재고 조회가 ERP와 엑셀에 중복"],
            "manual_work": ["출하 실적 수기 입력"],
            "data_silos": ["품질 데이터가 별도 PC에만 존재"],
            "legacy_risks": ["구형 수주 프로그램 벤더 지원 종료 예정"],
            "ai_applicable_work": ["불량 이미지 분류", "수요 예측 보조"],
            "integration_needs": ["ERP 기준정보 API 또는 파일 연계"],
        }
    if task == "rfp":
        return {
            **base,
            "title": f"{company} AI 도입 PoC RFP 초안",
            "sections": {
                "사업개요": "합성 데이터 기반 AI 도입 PoC",
                "추진배경및필요성": "수작업 검사·마감 부하",
                "현황및문제점": "숙련자 의존, 데이터 단절",
                "사업목표": "오탐/미탐 지표 수립 후 보조 판정",
                "구축범위": "1개 라인 PoC",
                "기능요구사항": "이미지 수집, 추론, 이력 조회",
                "보안요구사항": "폐쇄망 또는 VPN, 접근통제",
                "데이터요구사항": "학습 데이터 반출 금지 옵션",
                "검수및테스트기준": "현장 샘플 세트 재현 시험",
                "산출물": "모델, 운영매뉴얼, 보고서",
            },
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
    return {
        **base,
        "common": ["데이터 품질이 우선"],
        "conflicts": ["클라우드 추론 가능 여부에 의견이 갈릴 수 있음"],
        "weak_claims": ["비용 절감 퍼센트는 근거 부족 시 제외"],
        "final_opinion": "PoC 범위로 검사 보조부터 검증할 것을 권고 (합성 결과)",
    }


def _call_upstage(
    cfg: dict[str, Any],
    prompt: str,
    *,
    system: str = SYSTEM,
    messages: list[dict[str, str]] | None = None,
    temperature: float = 0.2,
) -> str:
    url = f"{cfg['base_url'].rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}
    msgs = messages or [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    body = {
        "model": cfg["model"],
        "messages": msgs,
        "temperature": temperature,
    }
    with httpx.Client(timeout=90) as client:
        resp = client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]


def _call_google(
    cfg: dict[str, Any],
    prompt: str,
    *,
    system: str = SYSTEM,
    as_json: bool = True,
    history: list[dict[str, str]] | None = None,
    temperature: float = 0.2,
) -> str:
    model = cfg["model"]
    url = f"{cfg['base_url'].rstrip('/')}/models/{model}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": cfg["api_key"]}
    contents: list[dict[str, Any]] = []
    for m in history or []:
        role = "user" if m.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m.get("content") or ""}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    gen_cfg: dict[str, Any] = {"temperature": temperature}
    if as_json:
        gen_cfg["responseMimeType"] = "application/json"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": gen_cfg,
    }
    with httpx.Client(timeout=90) as client:
        resp = client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    text = ""
    for cand in data.get("candidates") or []:
        for part in (cand.get("content") or {}).get("parts") or []:
            text += part.get("text") or ""
    return text


def generate_chat(
    model_name: str,
    *,
    system: str,
    history: list[dict[str, str]],
    user_text: str,
    context_json: str = "",
    mock_fn=None,
) -> str:
    """자유 대화 응답. 키 없으면 mock_fn 또는 간단 안내."""
    settings = runtime_settings()
    if model_name not in settings["models"]:
        raise ValueError(f"등록되지 않은 모델: {model_name}")
    cfg = settings["models"][model_name]
    prompt = user_text
    if context_json:
        prompt = f"[세션 컨텍스트 JSON]\n{context_json}\n\n[사용자]\n{user_text}"

    if not cfg.get("api_key"):
        if callable(mock_fn):
            return str(mock_fn(user_text, context_json))
        return "API 키가 없어 상담 Mock만 가능합니다. Secrets에 키를 넣으면 더 자세히 답합니다."

    try:
        if cfg["provider"] == "upstage":
            messages = [{"role": "system", "content": system}]
            for m in history[-8:]:
                messages.append({"role": m["role"], "content": m["content"]})
            messages.append({"role": "user", "content": prompt})
            return _call_upstage(cfg, prompt, system=system, messages=messages, temperature=0.4)
        if cfg["provider"] == "google":
            return _call_google(
                cfg,
                prompt,
                system=system,
                as_json=False,
                history=history[-8:],
                temperature=0.4,
            )
        raise ValueError(f"지원하지 않는 provider: {cfg['provider']}")
    except Exception as exc:
        if callable(mock_fn):
            return f"(연결 불안정 · Mock) {mock_fn(user_text, context_json)}\n\n_{exc.__class__.__name__}_"
        return f"상담 응답에 실패했습니다: {exc.__class__.__name__}"


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
        if cfg["provider"] == "upstage":
            content = _call_upstage(cfg, prompt)
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
