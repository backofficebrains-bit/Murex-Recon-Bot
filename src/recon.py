import pandas as pd
from datetime import datetime
import os

def murex_recon(murex_file, fo_file, tolerance=0.01):
    try:
        # =========================
        # 1. LOAD FILES
        # =========================
        mx = pd.read_csv(murex_file)
        fo = pd.read_csv(fo_file)

        # =========================
        # 2. STANDARDIZE COLUMNS
        # =========================
        mx = mx.rename(columns={
            'Trade ID': 'TradeRef',
            'Cpty': 'Counterparty'
        })

        fo = fo.rename(columns={
            'Trade ID': 'TradeRef',
            'Cpty': 'Counterparty'
        })

        required_cols = ['TradeRef', 'Counterparty', 'Notional', 'Currency', 'ValueDate', 'EventType']

        for col in required_cols:
            if col not in mx.columns:
                raise ValueError(f"Missing column in Murex file: {col}")
            if col not in fo.columns:
                raise ValueError(f"Missing column in FO file: {col}")

        # =========================
        # 3. MERGE DATA
        # =========================
        merge_keys = ['TradeRef', 'Counterparty', 'Currency', 'ValueDate']

        merged = pd.merge(
            mx,
            fo,
            on=merge_keys,
            how='outer',
            suffixes=('_MX', '_FO'),
            indicator=True
        )

        # =========================
        # 4. BREAK LOGIC
        # =========================
        merged['Notional_MX'] = merged['Notional_MX'].fillna(0)
        merged['Notional_FO'] = merged['Notional_FO'].fillna(0)

        merged['Amount_Break'] = abs(merged['Notional_MX'] - merged['Notional_FO']) > tolerance
        merged['Lifecycle_Break'] = merged['EventType_MX'] != merged['EventType_FO']

        # =========================
        # 5. STATUS CLASSIFICATION
        # =========================
        merged['Status'] = 'Matched'

        merged.loc[merged['_merge'] == 'left_only', 'Status'] = 'Missing in FO'
        merged.loc[merged['_merge'] == 'right_only', 'Status'] = 'Missing in MX'

        merged.loc[merged['Amount_Break'], 'Status'] = 'Notional Break'
        merged.loc[merged['Lifecycle_Break'], 'Status'] = 'Lifecycle Break'

        # =========================
        # 6. BREAK REASON
        # =========================
        merged['Break_Reason'] = ''

        merged.loc[merged['Amount_Break'], 'Break_Reason'] += 'Notional mismatch; '
        merged.loc[merged['Lifecycle_Break'], 'Break_Reason'] += 'Event mismatch; '

        merged.loc[merged['Status'] == 'Missing in FO', 'Break_Reason'] = 'Trade missing in FO'
        merged.loc[merged['Status'] == 'Missing in MX', 'Break_Reason'] = 'Trade missing in Murex'

        # =========================
        # 7. FILTER BREAKS
        # =========================
        breaks = merged[merged['Status'] != 'Matched']

        # =========================
        # 8. OUTPUT FILES
        # =========================
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        os.makedirs("output", exist_ok=True)

        breaks_file = f"output/Murex_Breaks_{timestamp}.xlsx"
        full_file = f"output/Full_Recon_{timestamp}.csv"

        breaks.to_excel(breaks_file, index=False)
        merged.to_csv(full_file, index=False)

        # =========================
        # 9. SUMMARY
        # =========================
        summary = merged['Status'].value_counts()

        print("\n📊 Recon Summary:")
        print(summary)

        print(f"\n✅ Done! {len(breaks)} breaks found")
        print(f"📁 Break file: {breaks_file}")
        print(f"📁 Full file: {full_file}")

        # =========================
        # 10. LOGGING
        # =========================
        with open("recon_log.txt", "a") as log:
            log.write(f"{timestamp} | Total: {len(merged)} | Breaks: {len(breaks)}\n")

        return breaks

    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        return None


# =========================
# RUN BLOCK (for testing)
# =========================
if __name__ == "__main__":
    # Replace with your file paths
    murex_file = "data/sample_murex.csv"
    fo_file = "data/sample_fo.csv"

    murex_recon(murex_file, fo_file)
