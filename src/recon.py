import pandas as pd
from datetime import datetime
import os

def murex_recon(murex_file, fo_file, tolerance=0.01):
    try:
        mx = pd.read_csv(murex_file)
        fo = pd.read_csv(fo_file)

        # Expected columns
        required_cols = ['TradeRef', 'Counterparty', 'Notional', 'Currency', 'ValueDate', 'EventType']

        for col in required_cols:
            if col not in mx.columns:
                raise ValueError(f"Missing column in Murex file: {col}")
            if col not in fo.columns:
                raise ValueError(f"Missing column in FO file: {col}")

        # Merge
        merge_keys = ['TradeRef', 'Counterparty', 'Currency', 'ValueDate']

        merged = pd.merge(
            mx,
            fo,
            on=merge_keys,
            how='outer',
            suffixes=('_MX', '_FO'),
            indicator=True
        )

        # Break logic
        merged['Notional_MX'] = merged['Notional_MX'].fillna(0)
        merged['Notional_FO'] = merged['Notional_FO'].fillna(0)

        merged['Amount_Break'] = abs(merged['Notional_MX'] - merged['Notional_FO']) > tolerance
        merged['Lifecycle_Break'] = merged['EventType_MX'] != merged['EventType_FO']

        # Status
        merged['Status'] = 'Matched'

        merged.loc[merged['_merge'] == 'left_only', 'Status'] = 'Missing in FO'
        merged.loc[merged['_merge'] == 'right_only', 'Status'] = 'Missing in MX'

        merged.loc[merged['Amount_Break'], 'Status'] = 'Notional Break'
        merged.loc[merged['Lifecycle_Break'], 'Status'] = 'Lifecycle Break'

        # Filter breaks
        breaks = merged[merged['Status'] != 'Matched']

        # Output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        os.makedirs("output", exist_ok=True)

        breaks.to_excel(f"output/Murex_Breaks_{timestamp}.xlsx", index=False)
        merged.to_csv(f"output/Full_Recon_{timestamp}.csv", index=False)

        print("\n📊 Summary:")
        print(merged['Status'].value_counts())

        print(f"\n✅ Done! {len(breaks)} breaks found")

        return merged

    except Exception as e:
        print(f"❌ Error: {e}")
        return None
