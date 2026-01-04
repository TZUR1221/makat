import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# --- הגדרות האתר ---
st.set_page_config(page_title="ניהול מלאי", page_icon="📦", layout="centered")

# --- עיצוב לימין-לשמאל (עברית) ---
st.markdown("""
<style>
    .stTextInput > label {direction:rtl; text-align:right;}
    .stNumberInput > label {direction:rtl; text-align:right;}
    .stSelectbox > label {direction:rtl; text-align:right;}
    .stMarkdown {direction:rtl; text-align:right;}
    div[data-testid="stExpander"] details summary p {direction:rtl; text-align:right;}
</style>
""", unsafe_allow_html=True)

# --- חיבור לגוגל ---
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # שליפת הסיסמאות מתוך המערכת המאובטחת של הענן
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client

# --- קריאת נתונים ---
def get_data(client):
    try:
        sheet = client.open("SKU_DB").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        # המרת עמודת מק"ט לטקסט כדי למנוע בעיות תצוגה
        if 'sku' in df.columns:
            df['sku'] = df['sku'].astype(str)
        return df
    except Exception as e:
        return pd.DataFrame()

# --- יצירת מק"ט חדש ---
def generate_sku(df, category):
    # מפה שמגדירה קידומת לכל קטגוריה
    # אתה יכול לשנות את המספרים כאן לפי איך שאתה רוצה
    cat_map = {
        "כללי": 10,
        "מזון": 20,
        "משקאות": 30,
        "ניקיון": 40,
        "חד פעמי": 50,
        "חשמל": 60
    }
    
    # אם הקטגוריה לא ברשימה, נקבע לה קידומת 99
    cat_prefix = cat_map.get(category, 99)
    
    # חישוב המספר הבא
    if not df.empty and 'category' in df.columns:
        # בודקים כמה מוצרים יש כבר בקטגוריה הזו
        count = len(df[df['category'] == category])
        next_num = count + 1
    else:
        next_num = 1
    
    # יצירת המק"ט: קידומת + מספר רץ (למשל 20005)
    return f"{cat_prefix}{str(next_num).zfill(3)}"

# --- הממשק הראשי ---
st.title("📦 ניהול מלאי - אונליין")

try:
    client = init_connection()
    sheet = client.open("SKU_DB").sheet1
    df = get_data(client)

    # --- חלק 1: הוספת מוצר חדש ---
    with st.expander("➕ הוספת מוצר חדש", expanded=True):
        with st.form("add_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("שם מוצר")
                price = st.number_input("מחיר", min_value=0.0, step=0.1)
            
            with col2:
                # רשימת קטגוריות שנבנית אוטומטית ממה שיש באקסל
                existing_cats = df['category'].unique().tolist() if not df.empty else []
                # הוספת קטגוריות בסיס אם הרשימה ריקה
                base_cats = ["כללי", "מזון", "משקאות", "ניקיון", "חד פעמי"]
                all_cats = list(set(existing_cats + base_cats))
                
                category = st.selectbox("קטגוריה", all_cats)
                new_cat_manual = st.text_input("או הקלד קטגוריה חדשה")

            submitted = st.form_submit_button("שמור והפק מק\"ט")
            
            if submitted:
                final_cat = new_cat_manual if new_cat_manual else category
                
                if name:
                    new_sku = generate_sku(df, final_cat)
                    current_time = datetime.now().strftime("%d/%m/%Y")
                    
                    # שמירה לאקסל
                    new_row = [new_sku, name, final_cat, price, "User", current_time]
                    sheet.append_row(new_row)
                    
                    st.success(f"נשמר בהצלחה! מק\"ט חדש: {new_sku}")
                    st.cache_data.clear() # ניקוי זיכרון כדי לראות את העדכון
                    st.rerun() # רענון הדף
                else:
                    st.error("חובה להזין שם מוצר")

    # --- חלק 2: טבלת מוצרים ---
    st.divider()
    st.subheader(f"רשימת מוצרים ({len(df)})")

    if not df.empty:
        search = st.text_input("🔎 חיפוש מוצר...", "")
        
        # סינון הטבלה לפי חיפוש
        if search:
            mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
            df_show = df[mask]
        else:
            df_show = df
            
        # הצגת הטבלה
        st.dataframe(
            df_show, 
            use_container_width=True,
            column_config={
                "sku": st.column_config.TextColumn("מק\"ט"),
                "name": "שם מוצר",
                "category": "קטגוריה",
                "price": st.column_config.NumberColumn("מחיר", format="₪ %.2f"),
                "added_by": "נוסף ע\"י",
                "date": "תאריך"
            },
            hide_index=True
        )
    else:
        st.info("הטבלה ריקה כרגע.")

except Exception as e:
    st.error("לא מצליח להתחבר לגוגל")
    st.info("בפעם הראשונה, יש להגדיר את המפתח הסודי (Secrets) בהגדרות האתר.")