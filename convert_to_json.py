import pandas as pd
import json

print("Reading Excel file...")

df = pd.read_excel("Final_Data_2030_Tagging_Updated.xlsx")

print("Rows found:", len(df))

df.columns = df.columns.str.strip()
df = df.fillna("")

records = df.to_dict(orient="records")

with open(
    "assets_data.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        records,
        f,
        indent=4,
        ensure_ascii=False
    )

print("SUCCESS")
print(f"Saved {len(records)} records")