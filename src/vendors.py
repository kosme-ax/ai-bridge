"""과업지시서 연계 AI 공급사 카탈로그(시연용).

※ 추천·안내용 공개 정보 기반 목록입니다. 선정·단가·계약 보증이 아니며,
   최신 AI바우처 공급기업 Pool·각사 공고를 반드시 확인하세요.
"""

from __future__ import annotations

from typing import Any

VENDORS: list[dict[str, Any]] = [
    # —— 비전·품질검사 ——
    {
        "id": "intelliz",
        "name": "인텔리즈",
        "category": "비전·품질검사",
        "summary": "보급형·SaaS형 AI 머신비전. 중소 제조 품질검사 PoC에 적합.",
        "fit": ["외관검사", "품질", "비전", "불량", "검사"],
        "url": "https://intelliz.net/solutions",
        "contact": "sales@intelliz.net / 070-7006-8916",
        "note": "중소기업 부담 완화형 검사 플랫폼",
    },
    {
        "id": "ato",
        "name": "아토",
        "category": "비전·품질검사",
        "summary": "AI 비전·3D 정밀검사, 이종/누락 검사. MES/ERP/PLC 연동.",
        "fit": ["외관검사", "품질", "비전", "자동차", "부품"],
        "url": "https://ato.ai.kr/",
        "contact": "atoaikr@gmail.com / 054-605-9955",
        "note": "자동차·조립 라인 적합",
    },
    {
        "id": "twim",
        "name": "트윔",
        "category": "비전·품질검사",
        "summary": "MOAI 학습형 딥러닝 비전검사. 자동차·전지·식품 등 다수 레퍼런스.",
        "fit": ["외관검사", "품질", "비전", "자동차", "불량"],
        "url": "https://www.twim21.com/",
        "contact": "sales@twim21.com / 031-8055-8311",
        "note": "비정형 미세 불량에 강점",
    },
    {
        "id": "laonpeople",
        "name": "라온피플",
        "category": "비전·품질검사",
        "summary": "NAVI AI 등 제조 AX 비전. HW·SW 통합, MES/ERP 연동.",
        "fit": ["외관검사", "품질", "비전", "반도체", "배터리"],
        "url": "https://laonpeople.com/",
        "contact": "service@laonpeople.com / 1899-3058",
        "note": "대기업·정밀공정 레퍼런스",
    },
    {
        "id": "plaidlabs",
        "name": "플래드랩스",
        "category": "비전·품질검사",
        "summary": "제로샷 비전 AI + 로봇(NUVION). 학습 데이터 부족 현장에 유리.",
        "fit": ["외관검사", "품질", "비전", "로봇", "자동화"],
        "url": "https://plaidlabs.ai/ai/nuvion",
        "contact": "홈페이지 문의",
        "note": "소량·다품종·데이터 부족 시",
    },
    {
        "id": "virnect",
        "name": "버넥트",
        "category": "비전·품질검사",
        "summary": "외관결함·3D정합·SOP 자동생성·AR 현장지원. AI바우처 공급.",
        "fit": ["외관검사", "품질", "비전", "SOP", "현장"],
        "url": "https://virnect.com/",
        "contact": "홈페이지 문의",
        "note": "AI바우처 연계 검토 가능",
    },
    {
        "id": "ezpark",
        "name": "이즈파크",
        "category": "비전·품질검사",
        "summary": "도장·케이블 조립 등 작업중 비전 AI. AI 팩토리·바우처 공급.",
        "fit": ["품질", "비전", "조립", "도장", "케이블"],
        "url": "https://www.etnews.com/20260323000059",
        "contact": "홈페이지·보도 문의",
        "note": "현장 작업자 피드백형",
    },
    {
        "id": "deepnoid",
        "name": "딥노이드",
        "category": "비전·품질검사",
        "summary": "DEEP:FACTORY 산업 비전. 조립·이물·도포 등 공정검사.",
        "fit": ["품질", "비전", "조립", "전지", "불량"],
        "url": "https://www.deepnoid.com/",
        "contact": "홈페이지 문의",
        "note": "2차전지 등 대형 공급 사례",
    },
    {
        "id": "snuailab",
        "name": "스누아이랩",
        "category": "비전·품질검사",
        "summary": "AutoCare 기반 머신비전 학습·불량 식별.",
        "fit": ["품질", "비전", "불량", "검사"],
        "url": "https://www.snuailab.ai/",
        "contact": "홈페이지 문의",
        "note": "비전 학습도구 중심",
    },
    {
        "id": "impix",
        "name": "임픽스",
        "category": "비전·품질검사",
        "summary": "A²Lab Vision. 자동차 부품 표면·스크래치 등 AI 비전.",
        "fit": ["품질", "비전", "자동차", "부품", "표면"],
        "url": "https://www.impix.co.kr/",
        "contact": "홈페이지 문의",
        "note": "자동차부품 적용 사례",
    },
    {
        "id": "cognex",
        "name": "코그넥스(Cognex)",
        "category": "비전·품질검사",
        "summary": "글로벌 머신비전. VisionPro Deep Learning(수아랩 기술 흡수).",
        "fit": ["품질", "비전", "반도체", "전지", "검사"],
        "url": "https://www.cognex.com/ko-kr",
        "contact": "국내 지사·파트너 문의",
        "note": "대량·고정밀 라인용",
    },
    # —— MES·ERP·데이터 연계 ——
    {
        "id": "bizarim",
        "name": "비자림",
        "category": "MES·ERP 연계",
        "summary": "QFactory MES + 제조 AI. ERP·설비·문서·영상 연결.",
        "fit": ["ERP", "MES", "월마감", "데이터", "연계", "생산"],
        "url": "https://www.bizarim.com/ko/about",
        "contact": "sales@bizarim.com / 02-470-5398",
        "note": "생산·영업 데이터 단절 해소",
    },
    {
        "id": "runup",
        "name": "런업",
        "category": "MES·ERP 연계",
        "summary": "기존 MES·ERP·PLC 교체 없이 자동화 레이어(DynaMOS).",
        "fit": ["ERP", "MES", "연계", "자동화", "월마감", "수기"],
        "url": "https://runup.co.kr/",
        "contact": "support@runup.co.kr",
        "note": "레거시 유지·공백 자동화",
    },
    {
        "id": "definite",
        "name": "디피니트",
        "category": "MES·ERP 연계",
        "summary": "ERP/MES/문서 연결 제조 AI(다비오·다비스). 중기부 매칭 참여.",
        "fit": ["ERP", "MES", "문서", "데이터", "분석", "월마감"],
        "url": "https://www.mt.co.kr/future/2026/06/16/2026061615165262791",
        "contact": "홈페이지·보도 문의",
        "note": "의사결정·지식검색형",
    },
    {
        "id": "trinio",
        "name": "트리니오",
        "category": "업무자동화",
        "summary": "중소 제조 사무·ERP 자동화(D.A.N.A Work). 단기 맞춤 도입.",
        "fit": ["월마감", "엑셀", "ERP", "정산", "자동화", "수기"],
        "url": "https://trinio.io/",
        "contact": "홈페이지 문의",
        "note": "월마감·정산 수작업 완화",
    },
    {
        "id": "hosu",
        "name": "호수아이오",
        "category": "MES·ERP 연계",
        "summary": "Factory Agent — MES·ERP·IoT를 AI 사령탑으로 운영.",
        "fit": ["MES", "ERP", "운영", "보고", "자동화"],
        "url": "https://hosu.io/homepage/",
        "contact": "tera@hosu.io / 031-212-8607",
        "note": "운영·보고 자동화",
    },
    {
        "id": "micube",
        "name": "엠아이큐브솔루션",
        "category": "제조 AI 플랫폼",
        "summary": "SmartAI 비전·예지·공정최적화. AI바우처 풀 제조특화.",
        "fit": ["품질", "비전", "예지", "공정", "최적화"],
        "url": "https://micube.co.kr/",
        "contact": "02-553-2171",
        "note": "바우처 공급 Pool 참고",
    },
    {
        "id": "atech",
        "name": "에이테크",
        "category": "제조 AI 플랫폼",
        "summary": "AT-XENS 등 Edge 기반 생산·품질·예지·수요예측.",
        "fit": ["품질", "예지", "예측", "공정", "모니터링"],
        "url": "https://www.atech1221.com/",
        "contact": "홈페이지 문의",
        "note": "스마트팩토리 통합형",
    },
    # —— 예지보전·수요예측·문서 ——
    {
        "id": "futuremain",
        "name": "퓨처메인",
        "category": "예지보전",
        "summary": "ExRBM 설비 결함진단·예지보전. AI바우처 다년간 공급.",
        "fit": ["예지", "설비", "고장", "보전", "CNC"],
        "url": "https://www.aitimes.com/news/articleView.html?idxno=157051",
        "contact": "홈페이지·보도 문의",
        "note": "설비 다운타임 감소",
    },
    {
        "id": "motorsense",
        "name": "모터센스",
        "category": "예지보전",
        "summary": "산업용 모터 고장예측·설비 상태 AI.",
        "fit": ["예지", "모터", "설비", "보전"],
        "url": "https://motorsense.io/",
        "contact": "031-698-2714",
        "note": "모터·회전기 특화",
    },
    {
        "id": "impactfulai",
        "name": "임팩티브AI",
        "category": "수요예측",
        "summary": "딥플로우 — AI 수요예측·재고/생산계획. AI바우처 공급.",
        "fit": ["수요", "재고", "예측", "생산계획", "월마감"],
        "url": "https://www.mt.co.kr/industry/2024/02/21/2024022116572671229",
        "contact": "홈페이지·보도 문의",
        "note": "재고·수주 변동 대응",
    },
    {
        "id": "upstage",
        "name": "업스테이지",
        "category": "문서·LLM",
        "summary": "Solar LLM·Document AI. 문서 파싱·업무 자동화·에이전트.",
        "fit": ["문서", "RFP", "과업", "월마감", "자동화", "LLM"],
        "url": "https://www.upstage.ai/",
        "contact": "기업 세일즈 문의",
        "note": "과업지시서·문서 업무와 직결",
    },
    {
        "id": "wisenut",
        "name": "와이즈넛",
        "category": "문서·LLM",
        "summary": "RAG·도메인 LLM 에이전트. AI바우처 공급.",
        "fit": ["문서", "검색", "자동화", "LLM", "상담"],
        "url": "https://www.wisenut.com/",
        "contact": "홈페이지 문의",
        "note": "사내 지식·업무봇",
    },
    {
        "id": "jsystem",
        "name": "제이에스시스템",
        "category": "예지·공정",
        "summary": "설비 데이터 분석·공정 최적화. AI바우처 공급 사례.",
        "fit": ["예지", "공정", "품질", "설비"],
        "url": "https://www.sisajournal-e.com/news/articleView.html?idxno=419806",
        "contact": "홈페이지·보도 문의",
        "note": "중소 제조 예지·품질",
    },
]


def _haystack(company: dict[str, Any] | None, work_order: dict[str, Any] | None) -> str:
    parts: list[str] = []
    if company:
        parts.extend(
            [
                str(company.get("name") or ""),
                str(company.get("industry") or ""),
                str(company.get("main_tasks") or ""),
                str(company.get("it_summary") or ""),
                str(company.get("pain_points") or ""),
            ]
        )
        kd = company.get("kdoctor") or {}
        parts.append(str(kd.get("summary") or ""))
        parts.extend(str(t) for t in (kd.get("priority_tasks") or []))
    if work_order:
        parts.append(str(work_order.get("summary") or ""))
        parts.append(str(work_order.get("title") or ""))
        for key in ("objectives", "scope", "deliverables", "linked_diagnosis_points"):
            parts.append(str(work_order.get(key) or ""))
        sections = work_order.get("sections") or {}
        if isinstance(sections, dict):
            parts.extend(f"{k} {v}" for k, v in sections.items())
    return " ".join(parts).lower()


def recommend_vendors(
    *,
    company: dict[str, Any] | None = None,
    work_order: dict[str, Any] | None = None,
    fitness: dict[str, Any] | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    text = _haystack(company, work_order)
    # AX 적용 희망 영역·문제를 매칭 키워드에 강하게 반영
    focus_bits = []
    if fitness:
        focus_bits.extend(fitness.get("ai_areas") or [])
        focus_bits.extend(fitness.get("ai_problems") or [])
        if fitness.get("industry"):
            focus_bits.append(str(fitness["industry"]))
    focus_text = " ".join(str(x) for x in focus_bits).lower()
    text = f"{text} {focus_text}".strip()

    area_boost = {
        "품질관리": ("비전·품질검사",),
        "공정/설비": ("예지보전", "예지·공정", "MES·ERP 연계", "제조 AI 플랫폼"),
        "현장/작업": ("MES·ERP 연계", "예지보전", "제조 AI 플랫폼"),
        "구매/자재": ("MES·ERP 연계", "수요예측"),
        "물류": ("MES·ERP 연계", "수요예측"),
        "재무/회계": ("문서·LLM", "업무자동화", "MES·ERP 연계"),
        "영업/마케팅": ("문서·LLM", "업무자동화", "수요예측"),
        "기획관리": ("문서·LLM", "업무자동화"),
        "고객지원": ("문서·LLM", "업무자동화"),
        "인사/총무": ("문서·LLM", "업무자동화"),
        "기술개발": ("비전·품질검사", "제조 AI 플랫폼"),
        "제품개발": ("비전·품질검사", "제조 AI 플랫폼"),
        "연구기획": ("문서·LLM",),
    }

    scored: list[tuple[int, dict[str, Any]]] = []
    for v in VENDORS:
        hit = sum(1 for kw in v.get("fit") or [] if kw.lower() in text)
        for area in (fitness or {}).get("ai_areas") or []:
            if v.get("category") in area_boost.get(area, ()):
                hit += 2
        # soft boosts by industry
        industry = str((company or {}).get("industry") or "")
        if "자동차" in industry and "자동차" in " ".join(v.get("fit") or []):
            hit += 1
        if "식품" in industry and v["id"] in {"twim", "trinio", "impactfulai", "runup"}:
            hit += 1
        if hit == 0 and v["category"] in {"비전·품질검사", "MES·ERP 연계"}:
            hit = 1  # always surface core categories lightly
        scored.append((hit, v))
    scored.sort(key=lambda x: (-x[0], x[1]["name"]))
    out: list[dict[str, Any]] = []
    seen_cat: dict[str, int] = {}
    for hit, v in scored:
        cat = v["category"]
        # diversify categories a bit
        if seen_cat.get(cat, 0) >= 3 and len(out) >= 4:
            continue
        item = dict(v)
        item["match_score"] = hit
        item["why"] = (
            f"과업·진단 키워드와 {hit}건 매칭 · {v['category']}"
            if hit
            else f"기본 후보 · {v['category']}"
        )
        out.append(item)
        seen_cat[cat] = seen_cat.get(cat, 0) + 1
        if len(out) >= limit:
            break
    return out
