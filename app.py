"""
CleanFlow — Transaction Data Validator
Main Streamlit app
"""
import streamlit as st
import pandas as pd
from processor import process_dataframe, build_download_package
from country_rules import COUNTRY_PHONE_RULES, VALID_PAYMENT_MODES, DATE_FORMAT

st.set_page_config(
    page_title="CleanFlow",
    page_icon="✦",
    layout="wide",
)

st.markdown("""
<style>
  .stApp { background-color: #f8f9fc; }
  section[data-testid="stSidebar"] { background-color: #0f172a !important; }
  section[data-testid="stSidebar"] * { color: #94a3b8 !important; }
  section[data-testid="stSidebar"] h1,
  section[data-testid="stSidebar"] h2,
  section[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }
  section[data-testid="stSidebar"] .stDataFrame { background: #1e293b; }
  .stButton>button {
    background-color: #1e40af;
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: 600;
  }
  .stButton>button:hover { background-color: #1e3a8a; color: white; }
  .stDownloadButton>button {
    background-color: #059669;
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: 600;
  }
  [data-testid="stMetricValue"] { color: #0f172a; font-weight: 600; }
  .block-container { padding-top: 1.5rem; }
  .stForm { background: white; border-radius: 12px; padding: 1rem; border: 0.5px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_login" not in st.session_state:
    st.session_state.show_login = False


# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown(
        "<h2 style='color:#f1f5f9 !important; font-size:18px; margin-bottom:2px;'>✦ CleanFlow</h2>"
        "<p style='color:#475569 !important; font-size:11px; margin-bottom:16px;'>Transaction Validator</p>",
        unsafe_allow_html=True
    )
    st.divider()
    st.markdown("<p style='color:#64748b !important; font-size:11px; text-transform:uppercase; letter-spacing:0.05em;'>Validation Rules</p>", unsafe_allow_html=True)

    rules_df = pd.DataFrame(
        list(COUNTRY_PHONE_RULES.items()),
        columns=["Country", "Digits Required"]
    )
    st.dataframe(rules_df, hide_index=True, use_container_width=True)

    st.markdown("<p style='color:#64748b !important; font-size:11px; margin-top:12px;'>Payment Modes</p>", unsafe_allow_html=True)
    for mode in VALID_PAYMENT_MODES:
        st.markdown(f"<span style='color:#94a3b8 !important; font-size:12px;'>• {mode}</span>", unsafe_allow_html=True)

    st.markdown(f"<p style='color:#64748b !important; font-size:11px; margin-top:12px;'>Date Format: <code style='color:#93c5fd !important;'>{DATE_FORMAT}</code></p>", unsafe_allow_html=True)

    st.divider()
    st.markdown("<p style='color:#475569 !important; font-size:10px;'>Rules are configurable in country_rules.py</p>", unsafe_allow_html=True)


# ---------- HEADER ----------
col_title, col_auth = st.columns([5, 1])
with col_title:
    st.markdown("## ✦ CleanFlow")
    st.caption("Upload transaction data · Validate · Download clean output")

with col_auth:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.logged_in:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.show_login = False
            st.rerun()
    else:
        if st.button("Login"):
            st.session_state.show_login = not st.session_state.show_login
            st.rerun()

# ---------- LOGIN MODAL (shown only when Login is clicked) ----------
if st.session_state.show_login and not st.session_state.logged_in:
    with st.container():
        st.markdown("---")
        lc1, lc2, lc3 = st.columns([1, 1.2, 1])
        with lc2:
            st.markdown("#### Sign In")
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@company.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                if submitted:
                    if email and password:
                        st.session_state.logged_in = True
                        st.session_state.show_login = False
                        st.success("Logged in!")
                        st.rerun()
                    else:
                        st.error("Please enter both email and password")
            st.caption("Demo login — any email/password works")
        st.markdown("---")

# ---------- MAIN VALIDATOR ----------
st.markdown("### 1️⃣ Upload Transaction CSV")
st.caption("Required columns: order_id, product_name, quantity, price, payment_mode, phone_number, country, order_date")

uploaded_file = st.file_uploader(
    "Drop your CSV file here",
    type=["csv"],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, dtype={"phone_number": str, "order_id": str})
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

    st.markdown("**Preview — first 5 rows:**")
    st.dataframe(df.head(), use_container_width=True)

    st.markdown("### 2️⃣ Validate")
    if st.button("Run Validation", type="primary"):
        with st.spinner("Validating all rows..."):
            valid_df, invalid_df, summary = process_dataframe(df)
        st.session_state.valid_df = valid_df
        st.session_state.invalid_df = invalid_df
        st.session_state.summary = summary

if "summary" in st.session_state:
    summary = st.session_state.summary
    valid_df = st.session_state.valid_df
    invalid_df = st.session_state.invalid_df

    st.markdown("### 3️⃣ Results")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Rows", summary["total_rows"])
    m2.metric("Valid Rows", summary["valid_rows"], delta=f"{summary['success_rate']}% clean")
    m3.metric("Invalid Rows", summary["invalid_rows"])
    m4.metric("Success Rate", f"{summary['success_rate']}%")

    if len(invalid_df) > 0:
        st.markdown("**❌ Invalid rows — with reasons:**")
        display_cols = ["_row_number", "_errors"]
        existing = [c for c in ["order_id"] if c in invalid_df.columns]
        st.dataframe(
            invalid_df[existing + display_cols].rename(columns={
                "_row_number": "Row #",
                "_errors": "Error(s)",
                "order_id": "Order ID"
            }),
            use_container_width=True
        )
    else:
        st.success("All rows passed validation!")

    st.markdown("### 4️⃣ Download Cleaned Data")
    if len(valid_df) > 0:
        file_bytes, filename, mime = build_download_package(valid_df)
        if filename.endswith(".zip"):
            st.info(f"Large file detected — output split into 500-row chunks and zipped ({len(valid_df)} valid rows total).")
        st.download_button(
            label=f"⬇️ Download {filename}",
            data=file_bytes,
            file_name=filename,
            mime=mime,
            use_container_width=True
        )
    else:
        st.warning("No valid rows to download — all rows had errors.")
