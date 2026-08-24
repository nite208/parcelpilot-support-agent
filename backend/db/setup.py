import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
from config import DB_PATH, DATA_DIR


def setup_database():
    xlsx_path = os.path.join(DATA_DIR, "ParcelPilot_Assessment_Data.xlsx")
    
    if not os.path.exists(xlsx_path):
        print(f"Excel file not found at {xlsx_path}")
        return
    
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    xl = pd.ExcelFile(xlsx_path)
    print(f"Sheets found: {xl.sheet_names}")

    for sheet_name in xl.sheet_names:
        if sheet_name.lower() == "readme":
            continue
        
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        table_name = sheet_name.strip().lower().replace(" ", "_")
        
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"Loaded sheet '{sheet_name}' → table '{table_name}' ({len(df)} rows)")

    conn.commit()
    conn.close()
    print("Database setup complete.")


if __name__ == "__main__":
    setup_database()