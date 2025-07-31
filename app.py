import streamlit as st
import pandas as pd
from db_utils import init_db # db_utilsからinit_dbをインポート

# --- DB初期化 ---
init_db() # アプリ起動時にテーブルを作成

# --- 認証チェック ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/0_Login.py")

# --- アプリ設定 ---
st.set_page_config(
    page_title="インシデント報告システム",
    page_icon="🏥",
    layout="wide"
)

# --- ログアウトボタン ---
if st.sidebar.button("ログアウト"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.switch_page("pages/0_Login.py")

# --- 管理者向けメニュー ---
if st.session_state.get("role") == "admin":
    st.sidebar.markdown("### ユーザー管理")
    if st.sidebar.button("👥 ユーザー管理"):
        st.switch_page("pages/ユーザー管理.py")

# --- トップページの表示 ---
st.title("🏥 インシデント報告システム")
st.markdown("--- ")
st.header(f"ようこそ！ {st.session_state.username}さん")
st.write("このシステムは、院内で発生したインシデント・アクシデントを報告・管理するためのものです。")
st.write("左のサイドバーからメニューを選択してください。")

st.markdown("--- ")
st.subheader("📖 操作マニュアル")
st.write("アプリケーションの操作方法については、以下のマニュアルを参照してください。")
if st.button("操作マニュアルを開く"):
    st.switch_page("pages/9_マニュアル.py")
