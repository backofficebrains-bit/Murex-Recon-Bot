import streamlit as st
import pandas as pd
from src.recon import murex_recon

st.set_page_config(page_title="BOB Recon Engine", layout="wide")

st.title("🧠 BOB - Murex Recon Engine")
st.write("Upload Murex and FO files to identify breaks instantly.")

murex_file = st.file_uploader("Upload Murex File", type=["csv"])
fo_file = st.file_uploader("Upload FO File", type=["csv"])

if murex_file and fo_file:
    st.success("Files uploaded successfully ✅")

    if st.button("Run Reconciliation"):
        with st.spinner("Recon in progress..."):
            
            mx_df = pd.read_csv(murex_file)
            fo_df = pd.read_csv(fo_file)

            mx_df.to_csv("temp_mx.csv", index=False)
            fo_df.to_csv("temp_fo.csv", index=False)

            result = murex_recon("temp_mx.csv", "temp_fo.csv")

            if result is not None:
                st.subheader("📊 Recon Results")
                st.dataframe(result)

                st.subheader("📈 Summary")
                st.write(result['Status'].value_counts())
