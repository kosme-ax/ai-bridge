"""Toss-like: one job per screen, lots of space, short copy."""

from __future__ import annotations

import streamlit as st

STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
  font-family: "Pretendard", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
}

.stApp {
  background: #F7F8FA;
  color: #191F28;
}

[data-testid="stHeader"] { background: transparent; }

/* 시연용 사이드바 제거 — 모델·기업은 코드/환경변수 */
[data-testid="stSidebar"],
section[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
button[kind="headerNoPadding"] {
  display: none !important;
}
[data-testid="stAppViewContainer"] {
  margin-left: 0 !important;
}

.block-container {
  padding-top: 1.75rem;
  padding-bottom: 4rem;
  max-width: 720px;
}

/* 상단 pills·라디오를 토스 칩처럼 */
div[data-testid="stPills"] {
  margin: 0 0 1rem !important;
}
div[data-testid="stPills"] button {
  border-radius: 999px !important;
  font-weight: 700 !important;
  font-size: 0.82rem !important;
  letter-spacing: -0.02em;
}
div[role="radiogroup"] {
  gap: 0.35rem !important;
  flex-wrap: wrap !important;
  margin-bottom: 0.5rem !important;
}
div[role="radiogroup"] label {
  background: #FFFFFF !important;
  border: 1px solid #E5E8EB !important;
  border-radius: 999px !important;
  padding: 0.35rem 0.75rem !important;
  font-weight: 600 !important;
  font-size: 0.82rem !important;
  color: #4E5968 !important;
}
div[role="radiogroup"] label[data-checked="true"],
div[role="radiogroup"] label:has(input:checked) {
  background: #E8F3FF !important;
  border-color: #3182F6 !important;
  color: #3182F6 !important;
}

h1, h2, h3 { letter-spacing: -0.03em; }

div[data-testid="stAlert"] {
  border-radius: 16px;
  border: none;
}

.stButton > button {
  border-radius: 14px !important;
  font-weight: 700 !important;
  min-height: 52px;
  font-size: 1rem !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
  background: #3182F6 !important;
  border: none !important;
  box-shadow: none !important;
}
.stButton > button[kind="primary"]:hover {
  background: #1B64DA !important;
  border: none !important;
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="select"] > div {
  border-radius: 12px !important;
}

.toss-eyebrow {
  color: #3182F6;
  font-size: 0.85rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
}
.toss-title {
  font-size: clamp(1.75rem, 4vw, 2.25rem);
  font-weight: 800;
  line-height: 1.25;
  letter-spacing: -0.04em;
  color: #191F28;
  margin: 0 0 0.6rem;
}
.toss-sub {
  font-size: 1.05rem;
  line-height: 1.55;
  color: #8B95A1;
  margin: 0 0 2rem;
  max-width: 28rem;
}
.toss-card {
  background: #FFFFFF;
  border-radius: 20px;
  padding: 1.5rem 1.35rem;
  margin: 0 0 1.25rem;
  border: 1px solid #E5E8EB;
}
.toss-card h4 {
  margin: 0 0 0.35rem;
  font-size: 1.05rem;
  font-weight: 700;
  color: #191F28;
}
.toss-card p {
  margin: 0;
  color: #8B95A1;
  font-size: 0.92rem;
  line-height: 1.5;
}
.toss-meta {
  color: #8B95A1;
  font-size: 0.82rem;
  margin: 0 0 1.5rem;
}
.toss-foot {
  margin-top: 3rem;
  color: #B0B8C1;
  font-size: 0.78rem;
  text-align: center;
}
.toss-policy {
  background: #FFFFFF;
  border: 1px solid #E5E8EB;
  border-radius: 20px;
  padding: 1.25rem 1.2rem;
  margin: 0 0 0.85rem;
}
.toss-policy .badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  color: #3182F6;
  margin-bottom: 0.35rem;
}
.toss-policy h4 {
  margin: 0 0 0.4rem;
  font-size: 1.05rem;
  font-weight: 700;
  color: #191F28;
}
.toss-policy p {
  margin: 0 0 0.55rem;
  color: #4E5968;
  font-size: 0.9rem;
  line-height: 1.5;
}
.toss-policy .meta {
  color: #8B95A1;
  font-size: 0.8rem;
  line-height: 1.45;
  margin: 0;
}
</style>
"""


def inject_styles() -> None:
    st.markdown(STYLES, unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, sub: str = "") -> None:
    sub_html = f'<div class="toss-sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""
<div class="toss-eyebrow">{eyebrow}</div>
<div class="toss-title">{title}</div>
{sub_html}
""",
        unsafe_allow_html=True,
    )


def soft_card(title: str, body: str) -> None:
    st.markdown(
        f"""
<div class="toss-card">
  <h4>{title}</h4>
  <p>{body}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def vendor_card(vendor: dict) -> None:
    st.markdown(
        f"""
<div class="toss-policy">
  <div class="badge">{vendor.get("category", "공급사")} · 매칭 {vendor.get("match_score", 0)}</div>
  <h4>{vendor.get("name", "")}</h4>
  <p>{vendor.get("summary", "")}</p>
  <p class="meta">
    <strong>추천 이유</strong> {vendor.get("why", "")}<br/>
    <strong>메모</strong> {vendor.get("note", "-")}<br/>
    <strong>문의</strong> {vendor.get("contact", "-")}
  </p>
</div>
""",
        unsafe_allow_html=True,
    )


def policy_card(policy: dict) -> None:
    why = policy.get("why") or ""
    st.markdown(
        f"""
<div class="toss-policy">
  <div class="badge">{policy.get("category", "정책")} · {policy.get("org", "")}</div>
  <h4>{policy.get("name", "")}</h4>
  <p>{policy.get("summary", "")}</p>
  <p class="meta">
    <strong>추천 이유</strong> {why}<br/>
    <strong>일정</strong> {policy.get("period", "-")}<br/>
    <strong>신청</strong> {policy.get("apply", "-")}<br/>
    <strong>담당</strong> {policy.get("owner", "-")}<br/>
    <strong>문의</strong> {policy.get("contact", "-")}
  </p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
<div class="toss-foot">
  sme-ax-helper · 시연용 · 업로드 비저장
</div>
""",
        unsafe_allow_html=True,
    )
