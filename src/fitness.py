"""K-Doctor AX 자가진단 가이드에 맞춘 기초체력 체크.

중점: 어디에 AI/AX를 적용하고 싶은지(업무 영역·해결할 문제).
이후 사업·데이터·운영 관점 문항으로 준비도를 본다.
원문 매뉴얼에서 OCR로 확인된 문항(4·10·11·16·17·22)을 우선 반영.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

KDOCTOR_LOGIN = "https://kdoctor.kosmes.or.kr/registn2/login.do"
KDOCTOR_AX_INTRO = "https://kdoctor.kosmes.or.kr/aiself/ai_intro.do"

INDUSTRIES = ("제조업", "바이오헬스", "유통물류업", "서비스업")

# STEP 1 — AI 적용 희망 영역 (최대 2)
AI_AREAS = (
    "기획관리",
    "인사/총무",
    "재무/회계",
    "연구기획",
    "기술개발",
    "제품개발",
    "구매/자재",
    "공정/설비",
    "현장/작업",
    "품질관리",
    "영업/마케팅",
    "물류",
    "고객지원",
)

# STEP 1 — 영역별 해결 문제 (최대 2). 매뉴얼에 나온 기획·인사 항목은 원문 유지,
# 나머지 영역은 같은 톤의 대표 과제로 구성(시연용).
AREA_PROBLEMS: dict[str, tuple[str, ...]] = {
    "기획관리": (
        "사업(매출) 계획 부재",
        "규제 대응 미흡",
        "목표 대비 실적 분석 미흡",
        "경영 리스크 예측 부족",
    ),
    "인사/총무": (
        "이직률 증가",
        "채용 소요시간 지연",
        "인력 역량 부족",
        "적합 인력 배치 미흡",
        "문서관리 미흡",
        "시설안전관리 미흡",
    ),
    "재무/회계": (
        "월마감 지연",
        "비용·원가 집계 수기",
        "현금흐름 예측 부족",
        "거래처 정산 오류",
    ),
    "연구기획": (
        "연구 우선순위 불명확",
        "과제 진척 파악 어려움",
        "기술 트렌드 대응 부족",
    ),
    "기술개발": (
        "개발 일정 지연",
        "설계 변경 이력 분산",
        "시험·검증 데이터 미활용",
    ),
    "제품개발": (
        "시장 요구 반영 지연",
        "시제품 피드백 미수집",
        "사양·BOM 변경 혼선",
    ),
    "구매/자재": (
        "발주 타이밍 오차",
        "재고·자재 데이터 불일치",
        "공급사 단가 비교 어려움",
    ),
    "공정/설비": (
        "설비 가동률 파악 부족",
        "예지보전 미도입",
        "공정 병목 원인 파악 어려움",
    ),
    "현장/작업": (
        "작업 지시·실적 수기",
        "숙련자 의존",
        "안전·이상 대응 지연",
    ),
    "품질관리": (
        "외관·치수 검사 숙련 의존",
        "불량 원인 추적 어려움",
        "검사 데이터 미축적",
    ),
    "영업/마케팅": (
        "수주·납기 예측 부족",
        "고객 요구 이력 분산",
        "견적 작성 시간 과다",
    ),
    "물류": (
        "출하·재고 실사 오차",
        "배송 현황 파악 지연",
        "창고 동선·적재 비효율",
    ),
    "고객지원": (
        "문의·클레임 응대 지연",
        "이슈 이력 미관리",
        "FAQ·지식 공유 부족",
    ),
}

# STEP 2~4 — 확인된 매뉴얼 문항 (선택 1~5, 점수=선택번호)
# id는 매뉴얼 문항 번호를 따름.
LIKERT_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "q4",
        "step": "STEP 2 · 사업 관점",
        "topic": "AI 비전·목표",
        "text": "귀사는 AI 도입과 활용을 위한 비전과 목표를 수립하고 있습니까?",
        "options": [
            ("1 · 비전·목표를 검토한 적 없음", 1),
            ("2 · 관심은 있으나 산발적 논의", 2),
            ("3 · 기본 목표는 있으나 실행계획·성과지표 부재", 3),
            ("4 · 비전·목표와 부문별 실행계획·성과지표 마련", 4),
            ("5 · 전사 비전 명확, 주기적 성과 점검·업데이트", 5),
        ],
    },
    {
        "id": "q10",
        "step": "STEP 2 · 사업 관점",
        "topic": "성과 기여 인식",
        "text": "귀사는 AI 도입과 활용이 조직의 성과에 기여했다고 인식하고 있습니까?",
        "options": [
            ("1 · 성과 영향 인식 부족, 비용 부담으로 여김", 1),
            ("2 · 일부 효과보다 문제·한계가 더 부각", 2),
            ("3 · 특정 부문·프로젝트에서 성과 기여 인식", 3),
            ("4 · 효율·의사결정·비용 효과 있으나 확산 제한", 4),
            ("5 · 전사적으로 실질 성과, AI가 핵심 경쟁력", 5),
        ],
    },
    {
        "id": "q11",
        "step": "STEP 3 · 데이터 관점",
        "topic": "데이터 수집 체계",
        "text": "귀사는 사업 수행 과정에서 발생하는 데이터를 지속적으로 수집할 수 있는 체계를 갖추고 있습니까?",
        "options": [
            ("1 · 체계적 수집 없음, 개인·부서 산발", 1),
            ("2 · 일부 부서·과제만 조직적 수집", 2),
            ("3 · 핵심 영역은 있으나 전사 통합 체계 부재", 3),
            ("4 · 전사 수집, 일부 자동화", 4),
            ("5 · 전사 전 영역 실시간·자동화 수집", 5),
        ],
    },
    {
        "id": "q16",
        "step": "STEP 3 · 데이터 관점",
        "topic": "모델 전이·재사용",
        "text": "귀사는 개발한 AI 모델을 다른 장비나 업무 프로세스에 쉽게 전이(재학습/재사용)하고 있습니까?",
        "options": [
            ("1 · 재사용하지 못함", 1),
            ("2 · 일부 적용 가능하나 대폭 수정 필요", 2),
            ("3 · 특정 범위에서만 재학습·재사용", 3),
            ("4 · 여러 장비·업무 가능, 복잡 환경은 추가 조정", 4),
            ("5 · 대부분 손쉽게 재학습·재사용", 5),
        ],
    },
    {
        "id": "q17",
        "step": "STEP 4 · 운영 관점",
        "topic": "시스템 연계",
        "text": "귀사는 기존 비즈니스 시스템(ERP, MES 등)과 AI 시스템 간 데이터를 효율적으로 연계하여 활용하고 있습니까?",
        # OCR상 4지선다만 확인됨 → 원문 유지
        "options": [
            ("1 · 필요할 때 각 시스템에서 수동 추출", 1),
            ("2 · 일부 핵심 데이터만 부분 연계", 2),
            ("3 · 주요 시스템 연계, 실시간은 제한적", 3),
            ("4 · 대부분 양방향 실시간 연계, 업무·의사결정 즉시 반영", 4),
        ],
    },
    {
        "id": "q22",
        "step": "STEP 4 · 운영 관점",
        "topic": "보안·윤리",
        "text": "귀사는 데이터와 AI 모델이 안전하게 관리되고, 관련 법규와 윤리 기준을 지키도록 운영하고 있습니까?",
        "options": [
            ("1 · 개인정보·보안 정책 미수립", 1),
            ("2 · 일부 정책 있으나 법적·윤리 검토 비정기", 2),
            ("3 · 접근 통제는 있으나 AI 윤리 검토 미흡", 3),
            ("4 · 보안·법·윤리 기준 마련, 체계는 보완 필요", 4),
            ("5 · 수집·학습·운영 전 과정 거버넌스 확립", 5),
        ],
    },
]

EDUCATION_LINKS: list[dict[str, str]] = [
    {"title": "K-Doctor AX 자가진단 시작", "url": KDOCTOR_AX_INTRO, "when": "all"},
    {"title": "K-Doctor 로그인·회원가입", "url": KDOCTOR_LOGIN, "when": "all"},
    {"title": "중진공 연수원 · 교육과정 안내", "url": "https://www.kosmes.or.kr/", "when": "low"},
]

FITNESS_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": q["id"],
        "text": q["text"],
        "options": q["options"],
        "topic": q["topic"],
        "step": q["step"],
    }
    for q in LIKERT_QUESTIONS
]

# 퀴즈 전체 단계: 업종 → 영역 → 문제 → 리커트 6문항
FOCUS_STEPS = ("industry", "areas", "problems")
TOTAL_QUIZ_STEPS = len(FOCUS_STEPS) + len(LIKERT_QUESTIONS)


def problems_for_areas(areas: list[str]) -> list[str]:
    seen: list[str] = []
    for area in areas:
        for p in AREA_PROBLEMS.get(area, ()):
            if p not in seen:
                seen.append(p)
    return seen


def likert_at(index: int) -> dict[str, Any]:
    q = LIKERT_QUESTIONS[index]
    return {
        "id": q["id"],
        "topic": q["topic"],
        "step": q["step"],
        "text": q["text"],
        "options": q["options"],
        "index": index,
        "total": len(LIKERT_QUESTIONS),
    }


def _focus_tip(areas: list[str], problems: list[str], level: str) -> str:
    area_txt = " · ".join(areas) if areas else "미선택"
    if problems:
        prob_txt = " / ".join(problems[:2])
        focus = f"AI 적용 희망: {area_txt}. 우선 과제 후보: {prob_txt}."
    else:
        focus = f"AI 적용 희망: {area_txt}."
    if level == "high":
        return f"{focus} 사업·데이터·운영 준비가 양호합니다. 과업지시서로 범위를 고정하세요."
    if level == "mid":
        return f"{focus} 선택 영역에 맞춰 과업 범위를 좁히고, 데이터·연계를 보완하세요."
    return f"{focus} 거창한 도입보다 선택 영역의 데이터 기록·표준화부터 시작하세요."


def score_fitness(
    answers: dict[str, int],
    *,
    questions: list[dict[str, Any]] | None = None,
    source: str = "quiz",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    qs = questions or FITNESS_QUESTIONS
    max_score = sum(max(o[1] for o in q["options"]) for q in qs) or 1
    total = sum(int(answers.get(q["id"], 0)) for q in qs)
    ratio = total / max_score
    if ratio >= 0.7:
        level, label = "high", "준비됨"
    elif ratio >= 0.4:
        level, label = "mid", "보완 필요"
    else:
        level, label = "low", "기초 다지기"

    areas = list((extra or {}).get("ai_areas") or [])
    problems = list((extra or {}).get("ai_problems") or [])
    industry = (extra or {}).get("industry")
    tip = _focus_tip(areas, problems, level)

    links = [
        x
        for x in EDUCATION_LINKS
        if x["when"] == "all" or (level in ("low", "mid") and x["when"] == "low")
    ]
    result = {
        "total": total,
        "max_score": max_score,
        "ratio": round(ratio, 3),
        "level": level,
        "label": label,
        "tip": tip,
        "education": links,
        "answers": answers,
        "source": source,
        "industry": industry,
        "ai_areas": areas,
        "ai_problems": problems,
        "priority_tasks": problems[:3] or areas[:2],
    }
    if extra:
        # tip/priority는 위에서 계산한 값을 유지하되, 명시 덮어쓰기 허용
        merged = dict(extra)
        result.update(merged)
        if not merged.get("tip"):
            result["tip"] = tip
        if not merged.get("priority_tasks"):
            result["priority_tasks"] = problems[:3] or areas[:2]
    return result


def _split_list(raw: str, *, known: tuple[str, ...] | list[str] | None = None) -> list[str]:
    text = (raw or "").strip()
    if not text:
        return []
    # 알려진 라벨(예: 공정/설비)을 먼저 매칭해 '/' 오분할 방지
    if known:
        found: list[str] = []
        rest = text
        for label in sorted(known, key=len, reverse=True):
            if label in rest:
                found.append(label)
                rest = rest.replace(label, ",", 1)
        if found:
            return found
    parts = []
    for chunk in text.replace("·", ",").replace("\n", ",").split(","):
        item = chunk.strip(" -•\t")
        if item:
            parts.append(item)
    return parts


def parse_ax_report(text: str) -> dict[str, Any]:
    """업로드한 AX 자가진단 결과 보고서 텍스트 → 구조화 필드.

    시연용 예시 파일의 '키: 값' / 불릿 형식을 파싱합니다.
    키가 없으면 영역·문제 키워드를 본문에서 느슨하게 찾습니다.
    """
    lines = [ln.strip() for ln in (text or "").splitlines()]
    fields: dict[str, str] = {}
    bullets: list[str] = []
    current_block: str | None = None
    block_buf: list[str] = []

    def flush_block() -> None:
        nonlocal current_block, block_buf
        if current_block and block_buf:
            fields[current_block] = "\n".join(block_buf)
        current_block, block_buf = None, []

    for ln in lines:
        if not ln or ln.startswith("#"):
            continue
        if ln.startswith(("- ", "• ", "* ")):
            bullets.append(ln[2:].strip())
            if current_block:
                block_buf.append(ln[2:].strip())
            continue
        if ":" in ln or "：" in ln:
            flush_block()
            sep = "：" if "：" in ln and (":" not in ln or ln.index("：") < ln.index(":")) else ":"
            key, val = ln.split(sep, 1)
            key_n = key.strip().lower().replace(" ", "")
            val = val.strip()
            key_map = {
                "진단id": "diagnosis_id",
                "진단번호": "diagnosis_id",
                "기업명": "company_name",
                "업종": "industry",
                "ax수준": "ax_level",
                "ax레벨": "ax_level",
                "ai적용영역": "ai_areas",
                "적용영역": "ai_areas",
                "ai적용희망영역": "ai_areas",
                "해결문제": "ai_problems",
                "해결하고싶은문제": "ai_problems",
                "요약": "summary",
                "진단요약": "summary",
                "우선과제": "priority_tasks",
                "q4": "q4",
                "q10": "q10",
                "q11": "q11",
                "q16": "q16",
                "q17": "q17",
                "q22": "q22",
                "비전목표점수": "q4",
                "성과기여점수": "q10",
                "데이터수집점수": "q11",
                "모델전이점수": "q16",
                "시스템연계점수": "q17",
                "보안윤리점수": "q22",
            }
            mapped = key_map.get(key_n)
            if mapped in {"summary", "priority_tasks", "ai_areas", "ai_problems"} and not val:
                current_block = mapped
                continue
            if mapped:
                fields[mapped] = val
            continue
        if current_block:
            block_buf.append(ln)

    flush_block()

    all_problems = tuple(p for opts in AREA_PROBLEMS.values() for p in opts)
    areas = _split_list(fields.get("ai_areas", ""), known=AI_AREAS)
    if not areas:
        areas = [a for a in AI_AREAS if a in text][:2]
    problems = _split_list(fields.get("ai_problems", ""), known=all_problems)
    if not problems:
        # 우선과제 불릿·본문 문제 목록에서 후보 추출
        known = set(all_problems)
        problems = [b for b in bullets if b in known][:2]
        if not problems:
            problems = _split_list(fields.get("priority_tasks", ""), known=all_problems)[:2]

    priority = _split_list(fields.get("priority_tasks", "")) or bullets[:3] or problems

    answers: dict[str, int] = {}
    for qid in ("q4", "q10", "q11", "q16", "q17", "q22"):
        raw = fields.get(qid)
        if raw and raw[:1].isdigit():
            answers[qid] = int(raw[0])
    # 점수 없으면 AX수준으로 대략 채움
    if not answers:
        ax = fields.get("ax_level", "")
        base = {"초기": 2, "중간": 3, "높음": 4}.get(ax, 3)
        answers = {qid: base for qid in ("q4", "q10", "q11", "q16", "q17", "q22")}
        answers["q17"] = min(4, base)

    return {
        "diagnosis_id": fields.get("diagnosis_id", "UPLOAD"),
        "company_name": fields.get("company_name"),
        "industry": fields.get("industry"),
        "ax_level": fields.get("ax_level", "중간"),
        "summary": fields.get("summary", text[:400].strip()),
        "ai_areas": areas,
        "ai_problems": problems,
        "priority_tasks": priority[:3],
        "answers": answers,
        "raw_excerpt": text[:1200],
    }


def fitness_from_report(text: str, company: dict[str, Any]) -> dict[str, Any]:
    """업로드 보고서 → 기초체력 결과."""
    parsed = parse_ax_report(text)
    tip_map = {
        "초기": "보고서 기준 AX수준이 초기입니다. 선택 영역부터 과업 범위를 좁히세요.",
        "중간": "보고서 기준 AX 중간 수준입니다. 적용 희망 영역으로 과업지시서를 쓰세요.",
        "높음": "보고서 기준 준비가 양호합니다. 견적·정책자금 연계로 실행하세요.",
    }
    ax = str(parsed.get("ax_level") or "")
    result = score_fitness(
        parsed["answers"],
        source="report",
        extra={
            "kdoctor_id": parsed.get("diagnosis_id"),
            "kdoctor_summary": parsed.get("summary"),
            "priority_tasks": parsed.get("priority_tasks") or [],
            "company_name": parsed.get("company_name") or company.get("name"),
            "industry": parsed.get("industry") or company.get("industry"),
            "ai_areas": parsed.get("ai_areas") or [],
            "ai_problems": parsed.get("ai_problems") or [],
            "report_excerpt": parsed.get("raw_excerpt"),
            "tip": tip_map.get(ax) or tip_map["중간"],
        },
    )
    if ax == "초기" and result["level"] == "high":
        result["level"], result["label"] = "mid", "보완 필요"
    areas = result.get("ai_areas") or []
    if areas and "AI 적용" not in str(result.get("tip", "")):
        result["tip"] = f"AI 적용 희망: {' · '.join(areas)}. {result['tip']}"
    return result
