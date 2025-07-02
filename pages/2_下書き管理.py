import streamlit as st
import pandas as pd
import json
from db_utils import get_all_drafts, delete_draft

# --- 認証チェック ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/0_Login.py")

st.set_page_config(page_title="下書き管理", page_icon="")
st.title("📝 下書き管理")
st.markdown("--- ")

st.info("「新規報告」ページで入力途中の内容を「下書き保存」ボタンで保存できます。")

st.subheader("保存済み下書き一覧")

# --- 下書き一覧の取得 ---
df = get_all_drafts()

if df.empty:
    st.info("保存されている下書きはありません。")
else:
    # --- 一覧をカード形式で表示 ---
    for _, row in df.iterrows():
        with st.container():
            # --- JSONデータを読み込んで報告者名を取得 ---
            draft_data = json.loads(row['data_json'])
            reporter_name = draft_data.get('reporter_name', '氏名未入力') # .get()で安全に取得

            st.markdown(f"#### {row['title']}")
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"*保存日時: {pd.to_datetime(row['created_at']).strftime('%Y-%m-%d %H:%M')}*")
                # 報告者名を表示（空の場合は「氏名未入力」）
                st.write(f"**代表報告者:** {reporter_name if reporter_name else '氏名未入力'}")
            with col2:
                # 読み込みボタン
                if st.button("この下書きを読み込む", key=f"load_{row['id']}", use_container_width=True):
                    # session_stateに保存して新規報告ページに渡す
                    st.session_state.loaded_draft = draft_data # 既に読み込み済みのデータを使用
                    st.session_state.loaded_draft_id = row['id'] # ★ 下書きのIDも保存
                    # 新規報告ページに切り替え
                    st.switch_page("pages/1_新規報告.py")
            with col3:
                # 削除ボタン
                if st.button("❌ 削除", key=f"delete_{row['id']}", use_container_width=True):
                    delete_draft(row['id'])
                    st.success(f"「{row['title']}」を削除しました。")
                    # 削除後、ページを再読み込みして一覧を更新
                    st.rerun()
            st.markdown("--- ")