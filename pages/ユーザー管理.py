import streamlit as st
from db_utils import get_all_users, update_user_role, update_user_password, delete_user, add_user, update_user_lineworks_id
import bcrypt
import pandas as pd
import os

st.set_page_config(page_title="ユーザー管理", page_icon="👥", layout="wide")

# --- 認証チェック ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/0_Login.py")

# --- ロールベースのアクセス制御 ---
if st.session_state.get("role") != "admin":
    st.warning("このページにアクセスする権限がありません。管理者としてログインしてください。")
    st.stop() # ページの実行を停止

# --- メッセージ表示エリア ---
if "user_management_message" in st.session_state:
    if st.session_state.user_management_message_type == "success":
        st.success(st.session_state.user_management_message)
    elif st.session_state.user_management_message_type == "error":
        st.error(st.session_state.user_management_message)
    del st.session_state.user_management_message
    del st.session_state.user_management_message_type

st.title("👥 ユーザー管理")
st.markdown("--- ")

# --- ユーザー一覧の表示 ---
st.subheader("登録済みユーザー一覧")
users = get_all_users()

if not users:
    st.info("現在、登録されているユーザーはいません。")
else:
    # DataFrameに変換して表示
    users_df = pd.DataFrame(users)
    users_df['created_at'] = pd.to_datetime(users_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    st.dataframe(users_df.set_index('id'), use_container_width=True)

    st.markdown("--- ")

    # --- ユーザーの編集・削除 ---
    st.subheader("ユーザーの編集・削除")
    
    # 編集・削除対象ユーザーの選択
    user_options = {user['username']: user['id'] for user in users}
    selected_username = st.selectbox("操作対象のユーザーを選択", list(user_options.keys()))
    selected_user_id = user_options.get(selected_username)

    if selected_user_id:
        current_user_data = next((user for user in users if user['id'] == selected_user_id), None)

        if current_user_data:
            st.markdown(f"#### {selected_username} の操作")
            
            # ロール変更
            with st.form(key=f"edit_role_form_{selected_user_id}"):
                st.write("**ロールの変更**")
                new_role = st.selectbox("新しいロール", ['general', 'admin'], index=['general', 'admin'].index(current_user_data['role']))
                if st.form_submit_button("ロールを更新"):
                    update_user_role(selected_user_id, new_role)
                    st.session_state.user_management_message = f"{selected_username} のロールを {new_role} に更新しました。"
                    st.session_state.user_management_message_type = "success"
                    st.rerun()
            
            # パスワードリセット
            with st.form(key=f"reset_password_form_{selected_user_id}"):
                st.write("**パスワードのリセット**")
                new_password = st.text_input("新しいパスワード", type="password")
                confirm_new_password = st.text_input("新しいパスワード（確認用）", type="password")
                if st.form_submit_button("パスワードをリセット"):
                    if not new_password or not confirm_new_password:
                        st.session_state.user_management_message = "新しいパスワードを入力してください。"
                        st.session_state.user_management_message_type = "error"
                    elif new_password != confirm_new_password:
                        st.session_state.user_management_message = "パスワードが一致しません。"
                        st.session_state.user_management_message_type = "error"
                    elif len(new_password) < 6:
                        st.session_state.user_management_message = "パスワードは6文字以上である必要があります。"
                        st.session_state.user_management_message_type = "error"
                    else:
                        update_user_password(selected_user_id, new_password)
                        st.session_state.user_management_message = f"{selected_username} のパスワードをリセットしました。"
                        st.session_state.user_management_message_type = "success"
                    st.rerun()

            # LINE WORKS ID編集
            with st.form(key=f"edit_lineworks_id_form_{selected_user_id}"):
                st.write("**LINE WORKS IDの設定**")
                current_lineworks_id = current_user_data.get('lineworks_id', '') or ''
                new_lineworks_id = st.text_input("LINE WORKS ID", value=current_lineworks_id, placeholder="例: user@example.com")
                if st.form_submit_button("LINE WORKS IDを更新"):
                    update_user_lineworks_id(selected_user_id, new_lineworks_id if new_lineworks_id else None)
                    st.session_state.user_management_message = f"{selected_username} のLINE WORKS IDを更新しました。"
                    st.session_state.user_management_message_type = "success"
                    st.rerun()

            # ユーザー削除
            st.markdown("--- ")
            st.write("**ユーザーの削除**")
            # 削除ボタンと確認ロジック
            if st.button(f"❌ {selected_username} を削除", key=f"delete_user_btn_{selected_user_id}"):
                if selected_user_id == st.session_state.get('id'): # ログイン中のユーザー自身のIDを取得
                    st.session_state.user_management_message = "自分自身のアカウントを削除することはできません。"
                    st.session_state.user_management_message_type = "error"
                    st.rerun()
                else:
                    # 確認ダイアログを出すためにセッションステートを使用
                    st.session_state[f'confirm_delete_{selected_user_id}'] = True

            if st.session_state.get(f'confirm_delete_{selected_user_id}'):
                st.warning(f"{selected_username} を本当に削除しますか？この操作は元に戻せません。")
                col_confirm_del1, col_confirm_del2 = st.columns(2)
                with col_confirm_del1:
                    if st.button(f"はい、{selected_username} を削除します", key=f"confirm_delete_user_yes_{selected_user_id}", use_container_width=True):
                        delete_user(selected_user_id)
                        st.session_state.user_management_message = f"{selected_username} を削除しました。"
                        st.session_state.user_management_message_type = "success"
                        del st.session_state[f'confirm_delete_{selected_user_id}'] # 確認フラグをクリア
                        st.rerun()
                with col_confirm_del2:
                    if st.button("キャンセル", key=f"confirm_delete_user_no_{selected_user_id}", use_container_width=True):
                        del st.session_state[f'confirm_delete_{selected_user_id}'] # 確認フラグをクリア
                        st.rerun()

    st.markdown("--- ")

# --- 新規ユーザー追加（管理者用） ---
st.subheader("新規ユーザー追加")
with st.form(key='admin_add_user_form'):
    new_username_admin = st.text_input("ユーザー名")
    new_password_admin = st.text_input("パスワード", type="password")
    new_role_admin = st.selectbox("ロール", ['general', 'admin'])
    if st.form_submit_button("ユーザーを追加"):
        if not new_username_admin or not new_password_admin:
            st.session_state.user_management_message = "ユーザー名とパスワードを入力してください。"
            st.session_state.user_management_message_type = "error"
        elif len(new_password_admin) < 6:
            st.session_state.user_management_message = "パスワードは6文字以上である必要があります。"
            st.session_state.user_management_message_type = "error"
        else:
            if add_user(new_username_admin, new_password_admin, new_role_admin):
                st.session_state.user_management_message = f"{new_username_admin} ({new_role_admin}) を追加しました。"
                st.session_state.user_management_message_type = "success"
            else:
                st.session_state.user_management_message = "このユーザー名は既に存在します。"
                st.session_state.user_management_message_type = "error"
        st.rerun()
