import streamlit as st
import pandas as pd
from datetime import datetime

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="BOB Recon Engine",
    layout="wide"
)

# -------------------- BLOOMBERG STYLE --------------------
st.markdown("""
<style>
body {
    background-color: #0a0f1a;
    color: #e6e6e6;
}
h1, h2, h3 {
    color: #f5a623;
}
.stButton>button {
    background-color: #f5a623;
    color: black;
    border-radius: 8px;
}
[data-testid="stMetric"] {
    background-color: #111827;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    border: 1px solid #f5a623;
}
</style>
""", unsafe_allow_html=True)

# -------------------- TITLE --------------------
st.title("🧠 BOB - Murex Recon Terminal")
st.caption("Upload → Standardize → Reconcile → Dominate Ops")

# -------------------- FILE UPLOAD --------------------
col1, col2 = st.columns(2)

with col1:
    murex_file = st.file_uploader("📂 Upload Murex File", type=["csv", "xlsx"])

with col2:
    fo_file = st.file_uploader("📂 Upload FO File", type=["csv", "xlsx"])


# -------------------- HELPERS --------------------
def smart_read(file):
    try:
        return pd.read_csv(file)
    except:
        return pd.read_excel(file)


def standardize_columns(df):
    column_map = {}

    for col in df.columns:
        c = col.lower()

        if "trade" in c and "ref" in c:
            column_map[col] = "TradeRef"
        elif "counter" in c:
            column_map[col] = "Counterparty"
        elif "notional" in c or "amount" in c:
            column_map[col] = "Notional"
        elif "ccy" in c or "currency" in c:
            column_map[col] = "Currency"
        elif "value" in c and "date" in c:
            column_map[col] = "ValueDate"

    return df.rename(columns=column_map)


def clean_data(df):
    if "Notional" in df.columns:
        df["Notional"] = df["Notional"].astype(str).str.replace(",", "").astype(float)

    if "ValueDate" in df.columns:
        df["ValueDate"] = pd.to_datetime(df["ValueDate"], errors="coerce")

    return df


# -------------------- RECON LOGIC --------------------
def run_recon(mx, fo):

    merged = pd.merge(
        mx,
        fo,
        on="TradeRef",
        how="outer",
        suffixes=("_MX", "_FO"),
        indicator=True
    )

    def classify(row):
        if row["_merge"] == "left_only":
            return "Missing in FO"
        elif row["_merge"] == "right_only":
            return "Missing in MX"
        else:
            if (
                row.get("Notional_MX") == row.get("Notional_FO") and
                row.get("ValueDate_MX") == row.get("ValueDate_FO")
            ):
                return "Match"
            else:
                return "Break"

    merged["Status"] = merged.apply(classify, axis=1)

    return merged


# -------------------- MAIN FLOW --------------------
if murex_file and fo_file:

    st.success("Files uploaded successfully ✅")

    if st.button("🚀 Run Reconciliation"):

        with st.spinner("Recon engine thinking like a trader..."):

            mx_df = smart_read(murex_file)
            fo_df = smart_read(fo_file)

            mx_df = standardize_columns(mx_df)
            fo_df = standardize_columns(fo_df)

            mx_df = clean_data(mx_df)
            fo_df = clean_data(fo_df)

            result = run_recon(mx_df, fo_df)

            # -------------------- METRICS --------------------
            st.subheader("📊 Recon Summary")

            col1, col2, col3, col4 = st.columns(4)

            status_counts = result["Status"].value_counts()

            col1.metric("Total Trades", len(result))
            col2.metric("Matched", status_counts.get("Match", 0))
            col3.metric("Breaks", status_counts.get("Break", 0))
            col4.metric("Missing", 
                status_counts.get("Missing in FO", 0) + 
                status_counts.get("Missing in MX", 0)
            )

            # -------------------- HIGHLIGHT TABLE --------------------
            def highlight(row):
                if row["Status"] == "Break":
                    return ['background-color: #5c1a1a'] * len(row)
                elif "Missing" in row["Status"]:
                    return ['background-color: #5c3d1a'] * len(row)
                elif row["Status"] == "Match":
                    return ['background-color: #1a5c2e'] * len(row)
                return [''] * len(row)

            st.subheader("📋 Detailed Recon Output")
            st.dataframe(result.style.apply(highlight, axis=1), use_container_width=True)

            # -------------------- DOWNLOAD --------------------
            csv = result.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="📥 Download Recon Report",
                data=csv,
                file_name="recon_output.csv",
                mime="text/csv"
            )
