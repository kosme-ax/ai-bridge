"""중진공·중기부 정책자금/사업 카탈로그 + 결과 기반 추천.

※ 공고 일정·조건은 매년 변경됩니다. 시연·안내용 요약이며 최종은 공식 공고를 확인하세요.
"""

from __future__ import annotations

from typing import Any

POLICIES: list[dict[str, Any]] = [
    {
        "id": "tech_finance",
        "name": "개발기술사업화자금 (기술자금 융자)",
        "org": "중소벤처기업진흥공단",
        "category": "정책자금·융자",
        "summary": (
            "정부·지자체 R&D 성공기술, 특허·인증기술, 기업부설연구소 기술 등을 "
            "사업화하려는 중소기업에 시설·운전 자금을 융자 지원합니다."
        ),
        "period": "2026.01.05 ~ 예산 소진 시까지 (연간)",
        "apply": (
            "중진공 누리집 정책자금 온라인신청 "
            "(회원가입 → 기업정보입력 → 정책우선도평가 → 융자신청서)"
        ),
        "apply_url": "https://digital.kosmes.or.kr/dh/map/main.do",
        "info_url": "https://www.kosmes.or.kr/nsh/SH/SBI/SHSBI004M0.do",
        "contact": "정책자금 전담콜센터 1811-3655 / 통합콜센터 1357",
        "owner": "중진공 기업금융·지역본(지)부",
        "tags": ["finance", "tech", "facility", "ax_mid", "ax_high", "fitness_mid", "fitness_high"],
        "why_template": "AX 과업·설비/시스템 도입에 자금이 필요할 때 우선 검토하세요.",
    },
    {
        "id": "smart_factory_loan",
        "name": "제조현장스마트화 자금",
        "org": "중소벤처기업진흥공단",
        "category": "정책자금·융자",
        "summary": (
            "스마트공장·ICT 기반 생산 효율화 설비 도입 기업 등에 시설·운전 자금을 "
            "지원하는 정책자금입니다. (혁신성장지원 체계 내)"
        ),
        "period": "2026.01 ~ 예산 소진 시까지",
        "apply": "중진공 누리집·디지털지점에서 정책자금 온라인 신청",
        "apply_url": "https://www.kosmes.or.kr/",
        "info_url": "https://www.gov.kr/portal/rcvfvrSvc/dtlEx/B55400900012",
        "contact": "기업금융처·정책자금 콜센터 1811-3655",
        "owner": "중진공 기업금융처 / 지역본지부",
        "tags": ["finance", "smart", "facility", "ax_mid", "ax_high", "fitness_high"],
        "why_template": "시스템·설비 도입형 AX 과업과 잘 맞습니다.",
    },
    {
        "id": "regional_ai",
        "name": "지역 주도형 AI 대전환 사업",
        "org": "중소벤처기업부 · 중진공(제조AI지원처)",
        "category": "국비·지자체 컨소시엄",
        "summary": (
            "광역지자체가 컨소시엄을 꾸려 지역 중소기업 AI 솔루션 도입·인프라·인력양성을 "
            "추진합니다. 기업은 선정 지역의 사업단·참여기관을 통해 솔루션·진단 연계에 "
            "참여할 수 있습니다. (2026년 신규 광역 2곳 모집)"
        ),
        "period": "지자체 신청: 2026.02.04 ~ 2026.03.10 / 협약·사업: 2026.04~2027.12(예정)",
        "apply": (
            "① 광역지자체: 공고에 따라 컨소시엄 사업계획 신청 "
            "② 중소기업: 선정 지역 AI 사업단·중진공 지역본지부에 참여기업 문의"
        ),
        "apply_url": "https://www.mss.go.kr/site/smba/ex/bbs/View.do?bcIdx=1065319&cbIdx=310&parentSeq=1065319",
        "info_url": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000118174",
        "contact": "중진공 제조AI지원처 055-751-9646, 9647 / ai@kosmes.or.kr",
        "owner": "중기부 중소기업인공지능확산추진단 · 중진공 제조AI지원처",
        "tags": ["ai", "regional", "ax_mid", "ax_high", "fitness_mid", "fitness_high", "work_order"],
        "why_template": "지역 AX·AI 솔루션 보급 사업과 과업지시서를 연결하세요.",
    },
    {
        "id": "kdoctor",
        "name": "K-Doctor (빅데이터 기반 AI진단)",
        "org": "중소벤처기업진흥공단",
        "category": "진단·연계",
        "summary": (
            "온라인 기업진단으로 경영·역량 수준을 점검하고 솔루션 방향을 제공합니다. "
            "sme-ax-helper는 진단 이후 과업지시서·견적비교로 이어줍니다."
        ),
        "period": "상시 (서비스 운영 기간)",
        "apply": "K-Doctor 누리집 회원가입 후 AI진단·AX자가진단 진행",
        "apply_url": "https://kdoctor.kosmes.or.kr/main.do?v=f",
        "info_url": "https://kdoctor.kosmes.or.kr/main.do?v=f",
        "contact": "중진공 통합콜센터 1357",
        "owner": "중진공 (AI진단 운영)",
        "tags": ["diagnosis", "fitness_low", "fitness_mid", "ax_low", "ax_mid"],
        "why_template": "기초체력·AX 수준이 낮을 때 정식 진단부터 다시 점검하세요.",
    },
    {
        "id": "digital_edu",
        "name": "중진공 연수·디지털 역량 교육",
        "org": "중소벤처기업진흥공단",
        "category": "교육·인식",
        "summary": (
            "데이터·디지털 전환 인식이 부족한 기업에 연수원·온라인 교육을 연계해 "
            "AX 심리적 장벽을 낮춥니다. (국민제안 넛지와 동일 취지)"
        ),
        "period": "과정별 수시 모집",
        "apply": "중진공 누리집 교육·연수 메뉴에서 과정 검색 후 신청",
        "apply_url": "https://www.kosmes.or.kr/",
        "info_url": "https://www.kosmes.or.kr/",
        "contact": "통합콜센터 1357",
        "owner": "중진공 연수·인력 관련 부서",
        "tags": ["edu", "fitness_low", "fitness_mid", "ax_low"],
        "why_template": "데이터 기초체력이 부족할 때 교육부터 권합니다.",
    },
]


def _ax_tag(company: dict[str, Any] | None) -> str:
    level = ((company or {}).get("kdoctor") or {}).get("ax_level") or ""
    if "초" in str(level) or str(level).lower() in {"low", "초기"}:
        return "ax_low"
    if "중" in str(level) or str(level).lower() in {"mid", "중간"}:
        return "ax_mid"
    if "고" in str(level) or str(level).lower() in {"high", "높"}:
        return "ax_high"
    return "ax_mid"


def _fitness_tag(fitness: dict[str, Any] | None) -> str | None:
    if not fitness:
        return None
    level = fitness.get("level")
    if level == "low":
        return "fitness_low"
    if level == "mid":
        return "fitness_mid"
    if level == "high":
        return "fitness_high"
    return None


def recommend_policies(
    *,
    fitness: dict[str, Any] | None = None,
    company: dict[str, Any] | None = None,
    context: str = "general",
    limit: int = 3,
) -> list[dict[str, Any]]:
    """결과 맥락에 맞는 정책 추천. context: fitness|work_order|quote|general"""
    wanted: set[str] = set()
    ft = _fitness_tag(fitness)
    if ft:
        wanted.add(ft)
    wanted.add(_ax_tag(company))

    if context == "fitness":
        wanted.update({"edu", "diagnosis"} if ft == "fitness_low" else {"finance", "ai", "diagnosis"})
    elif context == "work_order":
        wanted.update({"ai", "finance", "smart", "facility", "work_order"})
    elif context == "quote":
        wanted.update({"finance", "facility", "smart"})
    else:
        wanted.update({"finance", "ai", "edu"})

    scored: list[tuple[int, dict[str, Any]]] = []
    for p in POLICIES:
        tags = set(p.get("tags") or [])
        hit = len(wanted & tags)
        if hit == 0:
            continue
        scored.append((hit, p))
    scored.sort(key=lambda x: (-x[0], x[1]["name"]))

    out: list[dict[str, Any]] = []
    for hit, p in scored[:limit]:
        item = dict(p)
        item["match_score"] = hit
        item["why"] = p.get("why_template", "")
        out.append(item)
    if not out:
        # fallback
        out = [dict(POLICIES[0]), dict(POLICIES[2])]
        for item in out:
            item["match_score"] = 0
            item["why"] = "기본 추천 — 중진공 핵심 AX·자금 창구입니다."
    return out
