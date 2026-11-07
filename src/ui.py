"""K-Doctor(중진공 AI진단) 톤에 맞춘 Streamlit UI 헬퍼."""

from __future__ import annotations

import streamlit as st

STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap');

html, body, [class*="css"]  {
  font-family: "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
}

.stApp {
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(45, 140, 220, 0.35), transparent 55%),
    radial-gradient(ellipse 60% 40% at 80% 100%, rgba(30, 90, 180, 0.25), transparent 50%),
    linear-gradient(180deg, #06101f 0%, #071526 40%, #0a1c33 100%);
  color: #F2F7FC;
}

[data-testid="stHeader"] {
  background: rgba(6, 16, 31, 0.75);
  backdrop-filter: blur(8px);
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0a1a2e 0%, #071526 100%);
  border-right: 1px solid rgba(90, 160, 220, 0.18);
}

[data-testid="stSidebar"] * {
  color: #E8F1FA !important;
}

.block-container {
  padding-top: 1rem;
  max-width: 1180px;
}

div[data-testid="stTabs"] button[data-baseweb="tab"] {
  color: #A9C4DE;
  font-weight: 600;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
  color: #FFFFFF !important;
  border-bottom-color: #3D9BE9 !important;
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
  background: linear-gradient(90deg, #1E6FBF 0%, #3D9BE9 100%);
  border: 0;
  color: #fff;
  font-weight: 700;
  border-radius: 4px;
  box-shadow: 0 8px 24px rgba(30, 111, 191, 0.35);
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(90deg, #2480D8 0%, #56AEF0 100%);
  border: 0;
  color: #fff;
}

div[data-testid="stAlert"] {
  border-radius: 6px;
}

.kd-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.35rem 0 0.75rem;
  border-bottom: 1px solid rgba(120, 170, 220, 0.18);
  margin-bottom: 0.85rem;
  font-size: 0.78rem;
  color: rgba(220, 235, 250, 0.78);
  letter-spacing: -0.01em;
}
.kd-topbar a {
  color: rgba(220, 235, 250, 0.85);
  text-decoration: none;
  margin-left: 1rem;
}
.kd-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0.4rem 0 1.1rem;
}
.kd-mark {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: linear-gradient(145deg, #2F8FDB, #0E4F91);
  box-shadow: 0 0 0 1px rgba(120, 190, 255, 0.35), 0 10px 28px rgba(20, 90, 170, 0.45);
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #fff;
  font-size: 0.72rem;
  letter-spacing: 0.02em;
}
.kd-brand-title {
  font-size: 1.05rem;
  font-weight: 800;
  color: #fff;
  line-height: 1.25;
}
.kd-brand-sub {
  font-size: 0.78rem;
  color: #9FBFDC;
}

.kd-hero {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  padding: 2.4rem 2rem 2rem;
  margin-bottom: 1.25rem;
  border: 1px solid rgba(100, 170, 230, 0.22);
  background:
    linear-gradient(180deg, rgba(8, 28, 55, 0.55) 0%, rgba(6, 18, 36, 0.35) 100%),
    radial-gradient(circle at 70% 80%, rgba(55, 150, 230, 0.28), transparent 42%),
    repeating-linear-gradient(
      90deg,
      transparent 0,
      transparent 38px,
      rgba(80, 160, 230, 0.07) 38px,
      rgba(80, 160, 230, 0.07) 39px
    ),
    repeating-linear-gradient(
      0deg,
      transparent 0,
      transparent 38px,
      rgba(80, 160, 230, 0.07) 38px,
      rgba(80, 160, 230, 0.07) 39px
    );
  box-shadow: inset 0 -40px 80px rgba(20, 90, 170, 0.18);
  text-align: center;
}
.kd-hero::after {
  content: "";
  position: absolute;
  inset: auto 10% -30% 10%;
  height: 55%;
  background: radial-gradient(ellipse at center, rgba(70, 170, 255, 0.35), transparent 70%);
  filter: blur(8px);
  pointer-events: none;
}
.kd-eyebrow {
  display: inline-block;
  padding: 0.22rem 0.7rem;
  border: 1px solid rgba(130, 190, 245, 0.35);
  border-radius: 999px;
  color: #B7D8F5;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.9rem;
  background: rgba(20, 50, 90, 0.35);
}
.kd-hero h1 {
  margin: 0;
  font-size: clamp(1.7rem, 3.4vw, 2.55rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #FFFFFF;
  text-shadow: 0 8px 30px rgba(0, 40, 90, 0.55);
}
.kd-hero p {
  margin: 0.85rem auto 0;
  max-width: 46rem;
  color: #D5E7F8;
  font-size: 0.95rem;
  line-height: 1.65;
  opacity: 0.92;
}

.kd-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.85rem;
  margin: 0 0 1.35rem;
}
.kd-stat {
  text-align: center;
  padding: 1rem 0.6rem 0.95rem;
  border-radius: 12px;
  background: rgba(10, 30, 55, 0.55);
  border: 1px solid rgba(100, 170, 230, 0.2);
  box-shadow: 0 10px 28px rgba(0, 20, 50, 0.28);
}
.kd-stat .ring {
  width: 54px;
  height: 54px;
  margin: 0 auto 0.55rem;
  border-radius: 50%;
  display: grid;
  place-items: center;
  border: 2px solid rgba(120, 190, 255, 0.55);
  box-shadow: 0 0 18px rgba(70, 160, 240, 0.25);
  color: #8FCBFF;
  font-size: 1.15rem;
  background: radial-gradient(circle at 35% 30%, rgba(90, 170, 255, 0.25), rgba(10, 30, 55, 0.2));
}
.kd-stat .label {
  color: #A9C7E0;
  font-size: 0.78rem;
  margin-bottom: 0.25rem;
}
.kd-stat .value {
  color: #FFFFFF;
  font-size: 1.45rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.kd-panel {
  border: 1px solid rgba(100, 170, 230, 0.18);
  border-radius: 12px;
  padding: 0.15rem 0.2rem 0.4rem;
  background: rgba(8, 24, 45, 0.45);
}

.kd-foot {
  margin-top: 2rem;
  padding: 1rem 0 0.4rem;
  border-top: 1px solid rgba(100, 170, 230, 0.15);
  color: #8FA9C2;
  font-size: 0.78rem;
  text-align: center;
}

@media (max-width: 900px) {
  .kd-stats { grid-template-columns: repeat(2, 1fr); }
  .kd-hero { padding: 1.6rem 1.1rem 1.4rem; }
}
</style>
"""


def inject_styles() -> None:
    st.markdown(STYLES, unsafe_allow_html=True)


def render_top() -> None:
    st.markdown(
        """
<div class="kd-topbar">
  <div>K-Doctor 진단 완료 기업 → AX 지원 후속업무 시연</div>
  <div>
    <a href="https://kdoctor.kosmes.or.kr/main.do?v=f" target="_blank">K-Doctor 진단</a>
    <a href="https://www.kosmes.or.kr/" target="_blank">중진공</a>
  </div>
</div>
<div class="kd-brand">
  <div class="kd-mark">AX</div>
  <div>
    <div class="kd-brand-title">AI-Bridge · AX 과업지시서 · 견적비교</div>
    <div class="kd-brand-sub">진단은 K-Doctor가, 지원 실행 문서는 AI-Bridge가</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
<div class="kd-hero">
  <div class="kd-eyebrow">핵심 = 과업지시서 작성 + 견적 비교 · 진단은 연동 입력</div>
  <h1>진단 이후의 AX 지원, 여기서 실행합니다</h1>
  <p>
    <a href="https://kdoctor.kosmes.or.kr/main.do?v=f" target="_blank" style="color:#9FD0FF;">K-Doctor</a>에서
    끝난 기업진단 데이터를 받아, 중진공 AX 지원에 필요한
    <strong>과업지시서</strong>와 <strong>공급사 견적 비교</strong> 초안을 만듭니다.
    진단 자체를 대체하지 않습니다.
  </p>
</div>
<div class="kd-stats">
  <div class="kd-stat"><div class="ring">①</div><div class="label">입력</div><div class="value">K-Doctor</div></div>
  <div class="kd-stat"><div class="ring">②</div><div class="label">핵심①</div><div class="value">과업지시서</div></div>
  <div class="kd-stat"><div class="ring">③</div><div class="label">핵심②</div><div class="value">견적비교</div></div>
  <div class="kd-stat"><div class="ring">④</div><div class="label">보조</div><div class="value">시스템분석</div></div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
<div class="kd-foot">
  시연용 MVP입니다. K-Doctor 실데이터 API 연동 전, 합성 진단 결과를 사용합니다.
  진단 서비스가 아니라 AX 지원 과업지시서·견적비교 업무보조가 목적입니다.
</div>
""",
        unsafe_allow_html=True,
    )
