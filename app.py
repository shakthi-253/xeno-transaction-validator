"""
Xeno Transaction Validator
Main Streamlit app: login -> upload -> validate -> download
"""
import streamlit as st
import pandas as pd
from processor import process_dataframe, build_download_package
from country_rules import COUNTRY_PHONE_RULES, VALID_PAYMENT_MODES, DATE_FORMAT

st.set_page_config(
    page_title="Xeno Transaction Validator",
    page_icon="✅",
    layout="wide",
)

# ---------- THEME (white + terracotta) ----------
st.markdown("""
<style>
    .stApp { background-color: #fdfbf9; }
    h1, h2, h3 { color: #b5502f; }
    .stButton>button {
        background-color: #c1572f;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #9e4424;
        color: white;
    }
    [data-testid="stMetricValue"] { color: #b5502f; }
    .stDownloadButton>button {
        background-color: #2f8a5e;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
    }
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# ---------- LOGIN PAGE ----------
def login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<h1 style='text-align:center;'>🧾 Xeno Validator</h1>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center; color:#8a7a6f;'>"
            "Transaction data validation & processing</p>",
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@company.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                # NOTE: demo-only auth, not connected to a real user database.
                # Any non-empty email/password logs in -- this assignment's
                # focus is the validation engine, not auth infrastructure.
                if email and password:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Please enter both email and password")

        st.markdown(
            "<p style='text-align:center; color:#b0a59c; font-size:0.8rem;'>"
            "Demo login — any email/password works</p>",
            unsafe_allow_html=True
        )


# ---------- MAIN APP (after login) ----------
def main_app():
    # Header
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("## 🧾 Transaction Data Validator")
        st.caption("Upload, validate, and clean your transaction dataset")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    st.divider()

    # Sidebar — configured rules (shows it's config-driven, not hardcoded)
    with st.sidebar:
        st.markdown("### ⚙️ Validation Rules")
        st.caption("Configured in `country_rules.py`")

        st.markdown("**Phone digit rules by country:**")
        rules_df = pd.DataFrame(
            list(COUNTRY_PHONE_RULES.items()),
            columns=["Country", "Required Digits"]
        )
        st.dataframe(rules_df, hide_index=True, use_container_width=True)

        st.markdown("**Valid payment modes:**")
        st.write(", ".join(VALID_PAYMENT_MODES))

        st.markdown(f"**Date format expected:** `{DATE_FORMAT}`")

    # File upload
    st.markdown("### 1️⃣ Upload Transaction CSV")
    uploaded_file = st.file_uploader(
        "Drop your CSV here",
        type=["csv"],
        help="Required columns: order_id, product_name, quantity, price, "
             "payment_mode, phone_number, country, order_date"
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, dtype={"phone_number": str, "order_id": str})
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
            return

        st.markdown("**Preview (first 5 rows):**")
        st.dataframe(df.head(), use_container_width=True)

        st.markdown("### 2️⃣ Run Validation")
        if st.button("Validate Data", type="primary"):
            with st.spinner("Validating rows..."):
                valid_df, invalid_df, summary = process_dataframe(df)

            st.session_state.valid_df = valid_df
            st.session_state.invalid_df = invalid_df
            st.session_state.summary = summary

        if "summary" in st.session_state:
            summary = st.session_state.summary
            valid_df = st.session_state.valid_df
            invalid_df = st.session_state.invalid_df

            st.markdown("### 3️⃣ Results")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Rows", summary["total_rows"])
            c2.metric("Valid Rows", summary["valid_rows"])
            c3.metric("Invalid Rows", summary["invalid_rows"])
            c4.metric("Success Rate", f"{summary['success_rate']}%")

            if len(invalid_df) > 0:
                st.markdown("**❌ Rows with errors:**")
                st.dataframe(
                    invalid_df[["_row_number", "_errors"]].rename(
                        columns={"_row_number": "Row #", "_errors": "Error(s)"}
                    ),
                    use_container_width=True
                )

            st.markdown("### 4️⃣ Download Cleaned Data")
            if len(valid_df) > 0:
                file_bytes, filename, mime = build_download_package(valid_df)
                if filename.endswith(".zip"):
                    st.info(
                        f"Output split into multiple chunks "
                        f"({len(valid_df)} rows, 500 rows per file) "
                        f"and packaged into a ZIP."
                    )
                st.download_button(
                    label=f"⬇️ Download {filename}",
                    data=file_bytes,
                    file_name=filename,
                    mime=mime,
                )
            else:
                st.warning("No valid rows to download.")


# ---------- ROUTER ----------
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
