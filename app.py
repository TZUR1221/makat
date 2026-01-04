import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("בדיקת חיבור")

try:
    # ניסיון לקרוא את הסודות
    st.write("1. בודק אם הסודות קיימים...")
    creds_dict = st.secrets["gcp_service_account"]
    st.success("הסודות נקראו בהצלחה!")

    # ניסיון להתחבר לגוגל
    st.write("2. מנסה להתחבר לגוגל...")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    st.success("החיבור לגוגל הצליח!")

    # ניסיון לפתוח את הקובץ
    st.write("3. מנסה לפתוח את הקובץ...")
    sheet_url = "https://docs.google.com/spreadsheets/d/1oq-vcCj1FxqFz0cPIEtHWF_ePofjSkIPXOCRdH8DSv0/edit?usp=sharing"
    sheet = client.open_by_url(sheet_url).sheet1
    st.success(f"הקובץ נפתח! נמצאו {len(sheet.get_all_records())} שורות.")

except Exception as e:
    st.error("נמצאה שגיאה!")
    st.code(str(e)) # זה יראה לנו בדיוק מה הבעיה
