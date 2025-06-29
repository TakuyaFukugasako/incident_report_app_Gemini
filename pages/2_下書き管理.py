import streamlit as st
import pandas as pd
import json
from db_utils import get_all_drafts, add_draft, delete_draft

st.set_page_config(page_title="下書き管理", page_icon="💾")
st.title("💾 下書き保存と呼び出し")
st.markdown("---")

# 下書きを新規作成
st.subheader("現在の入力内容を下書き保存")

# 例：新規報告で入力中のデータが session_state にある前提
# （ない場合は空でOK）
draft_title = st.text_input("下書きタイトル（任意）", value="未設定タイトル")

# 保存したいキー
keys_to_save = ["reporter_name", "job_type", "occurrence_date",
                "occurrence_time", "connection_with_accident",
                "situation", "countermeasure"]

draft_data = {k: st.session_state.get(k) for k in keys_to_save}

if st.button("💾 下書きとして保存"):
    add_draft(draft_title, json.dumps(draft_data, ensure_ascii=False))
    st.success("下書きを保存しました！")

st.markdown("---")
st.subheader("保存済み下書き一覧")

df = get_all_drafts()
if df.empty:
    st.info("下書きはまだありません。")
else:
    for _, row in df.iterrows():
        st.write(f"### {row['title']}")
        st.write(f"保存日時: {row['created_at']}")
        if st.button("この下書きを読み込む", key=f"load_{row['id']}"):
            loaded_data = json.loads(row['data_json'])
            st.session_state.loaded_draft = loaded_data
            st.success("下書きを読み込みました。左の新規報告ページで自動入力されます！")
        if st.button("❌ 削除", key=f"delete_{row['id']}"):
            delete_draft(row['id'])
            st.experimental_rerun()