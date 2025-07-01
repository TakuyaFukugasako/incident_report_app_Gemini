import streamlit as st
from db_utils import get_user_by_username, verify_password, add_user

st.set_page_config(page_title="ログイン", page_icon="🔑", layout="centered")

st.title("🔑 ログイン")
st.markdown("--- ")

# --- ログインフォーム ---
with st.form(key='login_form'):
    st.subheader("既存ユーザーでログイン")
    login_username = st.text_input("ユーザー名")
    login_password = st.text_input("パスワード", type="password")
    login_button = st.form_submit_button("ログイン", use_container_width=True)

    if login_button:
        user = get_user_by_username(login_username)
        if user and verify_password(login_password, user['password_hash']):
            st.session_state.logged_in = True
            st.session_state.username = user['username']
            st.session_state.role = user['role']
            st.success(f"ようこそ、{user['username']}さん！")
            st.switch_page("app.py") # ログイン成功後、メインページへリダイレクト
        else:
            st.error("ユーザー名またはパスワードが間違っています。")

st.markdown("--- ")

# --- 新規ユーザー登録フォーム ---
with st.form(key='register_form'):
    st.subheader("新規ユーザー登録")
    new_username = st.text_input("新しいユーザー名")
    new_password = st.text_input("パスワード", type="password")
    confirm_password = st.text_input("パスワード（確認用）", type="password")
    register_button = st.form_submit_button("新規登録", use_container_width=True)

    if register_button:
        if not new_username or not new_password or not confirm_password:
            st.error("全ての項目を入力してください。")
        elif new_password != confirm_password:
            st.error("パスワードが一致しません。")
        elif len(new_password) < 6:
            st.error("パスワードは6文字以上である必要があります。")
        else:
            if add_user(new_username, new_password, 'general'): # 新規登録ユーザーは'general'ロール
                st.success("ユーザー登録が完了しました。ログインしてください。")
            else:
                st.error("このユーザー名は既に存在します。別のユーザー名をお試しください。")
