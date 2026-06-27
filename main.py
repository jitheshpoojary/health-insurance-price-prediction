import streamlit as st

from prediction_helper import predict, calculate_normalized_risk

st.set_page_config(
    page_title="Premium Estimator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="auto",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,wght@0,400;0,500;1,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
    --bg: #F5F6F2;
    --card: #FFFFFF;
    --ink: #1B3A34;
    --accent: #B8863C;
    --muted: #6B7674;
    --line: #DCDED8;
    --risk-low: #5C8A66;
    --risk-mid: #D1A23A;
    --risk-high: #A6503A;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    color: var(--ink);
}

.stApp { background: var(--bg); }
.block-container { padding-top: 2.5rem; max-width: 1120px; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }

/* ---- Hero ---- */
.hero { padding-bottom: 1.5rem; border-bottom: 1px solid var(--line); margin-bottom: 1.75rem; }
.eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.14em;
    font-size: 0.72rem;
    color: var(--accent);
    text-transform: uppercase;
    margin: 0 0 0.4rem 0;
}
.hero h1 {
    font-family: 'Newsreader', serif;
    font-weight: 500;
    font-size: 2.6rem;
    color: var(--ink);
    margin: 0;
    line-height: 1.15;
}
.subtitle { color: var(--muted); font-size: 1rem; margin-top: 0.6rem; max-width: 34rem; }

/* ---- Form sections ---- */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    color: var(--ink);
    text-transform: uppercase;
    font-weight: 600;
    margin: 0.25rem 0 0.75rem 0;
}
hr.hairline { border: none; border-top: 1px solid var(--line); margin: 1.6rem 0; }

/* ---- Inputs & buttons ---- */
div[data-testid="stForm"] { background: transparent; border: none; padding: 0; }
div[data-testid="stFormSubmitButton"] button, div[data-testid="stButton"] button {
    background: var(--ink) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em;
    padding: 0.65rem 1.4rem !important;
    transition: background 0.2s ease;
}
div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stButton"] button:hover {
    background: var(--accent) !important;
    color: #FFFFFF !important;
}

/* ---- Result stub ---- */
.stub {
    background: var(--card);
    border-top: 3px dashed var(--line);
    border-radius: 0 0 6px 6px;
    padding: 2rem 1.85rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.stub-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    color: var(--muted);
    text-transform: uppercase;
    margin: 0;
}
.stub-amount {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.7rem;
    font-weight: 600;
    color: var(--ink);
    margin: 0.35rem 0 0 0;
}
.stub-caption { color: var(--muted); font-size: 0.85rem; margin: 0 0 1.4rem 0; }
.risk-track {
    background: var(--bg);
    border: 1px solid var(--line);
    border-radius: 999px;
    height: 8px;
    overflow: hidden;
    margin-bottom: 0.6rem;
}
.risk-fill { height: 100%; border-radius: 999px; transition: width 0.4s ease; }
.stub-risk { font-size: 0.9rem; color: var(--muted); margin: 0; }
.stub-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 230px;
    text-align: center;
}
.stub-placeholder { color: var(--muted); font-size: 0.95rem; max-width: 15rem; margin: 0; }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

MEDICAL_OPTIONS = ["No Disease", "Diabetes", "Heart Disease", "High Blood Pressure", "Thyroid"]


def format_inr(amount: float) -> str:
    """Format a number using Indian digit grouping, e.g. 123456 -> ₹1,23,456."""
    whole = str(int(round(amount)))
    if len(whole) <= 3:
        return f"₹{whole}"
    last3, rest = whole[-3:], whole[:-3]
    parts = []
    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.insert(0, rest)
    return "₹" + ",".join(parts) + "," + last3


def risk_band(score: float):
    if score < 0.34:
        return "Low", "var(--risk-low)"
    if score < 0.67:
        return "Moderate", "var(--risk-mid)"
    return "High", "var(--risk-high)"


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### About this tool")
    st.markdown(
        "A prototype that estimates an annual health insurance premium "
        "from a short personal, financial and health profile."
    )
    st.markdown("---")
    st.caption("Estimates are model-generated and are not a binding quote.")

# ----------------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <p class="eyebrow">Health Insurance</p>
        <h1>Premium Estimator</h1>
        <p class="subtitle">Fill in a few details about yourself and we'll estimate
        your annual premium and a relative health risk band.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.6, 1], gap="large")

with left:
    with st.form("premium_form"):
        st.markdown('<p class="section-label">01 — About you</p>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            age = st.number_input("Age", min_value=18, max_value=100, value=30, step=1)
            gender = st.selectbox("Gender", ["Male", "Female"])
        with c2:
            region = st.selectbox("Region", ["Northeast", "Northwest", "Southeast", "Southwest"])
            marital_status = st.selectbox("Marital status", ["Married", "Unmarried"])
        with c3:
            dependants = st.number_input("Dependants", min_value=0, max_value=10, value=0, step=1)
            employment_status = st.selectbox("Employment", ["Salaried", "Self-Employed", "Freelancer"])

        st.markdown('<hr class="hairline">', unsafe_allow_html=True)
        st.markdown('<p class="section-label">02 — Financial profile</p>', unsafe_allow_html=True)
        c4, c5 = st.columns(2)
        with c4:
            income = st.number_input("Income (lakhs / year)", min_value=0, max_value=200, value=10, step=1)
        with c5:
            insurance_plan = st.selectbox("Plan tier", ["Bronze", "Silver", "Gold"])

        st.markdown('<hr class="hairline">', unsafe_allow_html=True)
        st.markdown('<p class="section-label">03 — Health profile</p>', unsafe_allow_html=True)
        c6, c7 = st.columns(2)
        with c6:
            bmi_category = st.selectbox("BMI category", ["Normal", "Underweight", "Overweight", "Obesity"])
            smoking_status = st.selectbox("Smoking", ["No Smoking", "Occasional", "Regular"])
        with c7:
            genetical_risk = st.slider("Genetical risk score", min_value=0, max_value=5, value=0)
            medical_history = st.multiselect(
                "Medical history (max 2)",
                MEDICAL_OPTIONS,
                default=["No Disease"],
                max_selections=2,
            )

        submitted = st.form_submit_button("Calculate premium", use_container_width=True)

    if submitted:
        conditions = [c for c in medical_history if c != "No Disease"] or ["No Disease"]
        medical_history_str = " & ".join(conditions)

        input_dict = {
            "Age": age,
            "Gender": gender,
            "Region": region,
            "Marital Status": marital_status,
            "Number of Dependants": dependants,
            "Employment Status": employment_status,
            "Income in Lakhs": income,
            "Insurance Plan": insurance_plan,
            "BMI Category": bmi_category,
            "Smoking Status": smoking_status,
            "Genetical Risk": genetical_risk,
            "Medical History": medical_history_str,
        }

        try:
            premium = predict(input_dict)
            risk_score = calculate_normalized_risk(medical_history_str)
            st.session_state["result"] = {"premium": premium, "risk": risk_score}
        except FileNotFoundError:
            st.session_state["result"] = None
            st.error(
                "Model artifacts not found. Add model_young.joblib, model_rest.joblib, "
                "scaler_young.joblib and scaler_rest.joblib to an artifacts/ folder "
                "next to this app."
            )

with right:
    result = st.session_state.get("result")
    if result:
        label, color = risk_band(result["risk"])
        st.markdown(
            f"""
            <div class="stub">
                <p class="stub-eyebrow">Estimate</p>
                <p class="stub-amount">{format_inr(result['premium'])}</p>
                <p class="stub-caption">per year</p>
                <div class="risk-track">
                    <div class="risk-fill" style="width:{result['risk'] * 100:.0f}%; background:{color};"></div>
                </div>
                <p class="stub-risk">Health risk — <span style="color:{color};">{label}</span></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="stub stub-empty">
                <p class="stub-placeholder">Fill in the form and calculate to see
                your premium estimate here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )