import pandas as pd
# กำหนด path
path_bom = "/content/Raw_BOM2.csv"
path_subpart = "/content/Subpart.csv"
path_ignore = "/content/Ignore.csv"
path_Name ="/content/Name.csv"
MyStation = "100L04"
# โหลด BOM
bom_df = pd.read_csv(path_bom)  # ชื่อไฟล์ BOM

# โหลด Mapping Table (ไว้แตก part)
map_df = pd.read_csv(path_subpart)  # มี Original_Part, Sub_Part, Sub_Qty

# โหลด ignore list (Part ที่ไม่ต้องตรวจ)
ignore_df = pd.read_csv(path_ignore)  # มีคอลัมน์ชื่อ "Ignore_Part"

# โหลด model name lookup table
model_lookup_df = pd.read_csv(path_Name)  # มี MODEL_CODE, MODEL_NAME
# กรองเฉพาะ Station ที่ต้องการ
bom_df = bom_df[bom_df["STATION_NO"] == MyStation]
# ทำความสะอาดชื่อ part ทั้งหมด
bom_df["ITEM_DESCRIPTION"] = bom_df["ITEM_DESCRIPTION"].str.strip().str.lower()
bom_df["ITEM_NUMBER"] = bom_df["ITEM_NUMBER"].str.strip()#.str.lower()
map_df["Original_Part"] = map_df["Original_Part"].str.strip()#.str.lower()
ignore_df["Ignore_Part"] = ignore_df["ITEM_Part"].str.strip()#.str.lower()

# เอา BOM ที่ไม่อยู่ใน ignore list เท่านั้น
bom_df = bom_df[~bom_df["ITEM_NUMBER"].isin(ignore_df["Ignore_Part"])]

# เติม MODEL_NAME จาก lookup table
bom_df = bom_df.merge(model_lookup_df, how="left", on="MODEL_CODE")

# รวม BOM กับ mapping (แยก part ย่อย)
merged = bom_df.merge(map_df, how="left", left_on="ITEM_NUMBER", right_on="Original_Part")
# ลบเฉพาะแถวที่ MODEL_NAME มี "RT" และ Sub_Part เป็น "Pipe_small"
merged = merged[~(
    (merged["Sub_Part"] == "Pipe_small") &
    (merged["MODEL_NAME"].fillna("").str.contains("RT"))
)]
# ใช้ Sub_Part ถ้ามี, ไม่งั้นใช้ part เดิม
merged["Final_Part"] = merged["Sub_Part"].fillna(merged["ITEM_NUMBER"])
merged["Final_Qty"] = merged.apply(
    lambda row: row["Sub_Qty"] * row["PICKING_QTY"] if pd.notnull(row["Sub_Qty"]) else row["PICKING_QTY"],
    axis=1
)

# เลือกเฉพาะคอลัมน์สุดท้าย
final_df = merged[["MODEL_CODE", "MODEL_NAME","ITEM_NUMBER", "Final_Part", "Final_Qty"]]
final_df.columns = ["Model", "MODEL_NAME", "ITEM_NUMBER", "Part", "QtyNeeded"]

# ลบแถวที่ "MODEL_NAME ว่าง (เช่น "", NaN)
final_df = final_df[final_df["MODEL_NAME"].fillna("").str.strip() != ""]

# บันทึกเป็นไฟล์ใหม่
final_df.to_csv("expanded_bom.csv", index=False)