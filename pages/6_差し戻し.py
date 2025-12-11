import streamlit as st
import pandas as pd
import json
from db_utils import get_all_reports, update_report_status, get_report_by_id
from lineworks_bot_room import send_text_message_to_channel
import datetime
import os

# LINE WORKS設定
LINEWORKS_CHANNEL_ID = os.environ.get("LW_API_20_CHANNEL_ID") if os.environ.get("LW_API_20_CHANNEL_ID") else None
LINEWORKS_BOT_ID = os.environ.get("LW_API_20_BOT_ID") if os.environ.get("LW_API_20_BOT_ID") else None
# 承認通知用のBOT ID と CHANNEL ID
LINEWORKS_APPROVAL_BOT_ID = os.environ.get("LW_API_20_APPROVAL_BOT_ID") if os.environ.get("LW_API_20_APPROVAL_BOT_ID") else None
LINEWORKS_APPROVAL_CHANNEL_ID = os.environ.get("LW_API_20_APPROVAL_CHANNEL_ID") if os.environ.get("LW_API_20_APPROVAL_CHANNEL_ID") else None

# --- 認証チェック ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/0_Login.py")

st.set_page_config(page_title="差し戻し", page_icon="", layout="wide")

st.title(" 差し戻しレポート")
st.markdown("---")

# 説明
st.info("管理者から差し戻されたレポートを確認修正して再提出できます。修正完了後、「再提出」ボタンを押してください。")

df = get_all_reports()

if df.empty:
    st.warning("現在、レポートはありません。")
else:
    df.reset_index(inplace=True)
    df.rename(columns={
        'id': '報告ID',
        'occurrence_datetime': '発生日時',
        'reporter_name': '報告者',
        'job_type': '職種',
        'level': '影響度レベル',
        'location': '発生場所',
        'content_category': '内容分類',
        'content_details': 'インシデント内容',
        'cause_details': '発生原因',
        'situation': '状況詳細',
        'countermeasure': '今後の対策',
        'status': 'ステータス',
        'manager_comments': '管理者コメント'
    }, inplace=True)

    current_username = st.session_state.get('username', '')
    rejected_df = df[(df['ステータス'] == '差し戻し') & (df['報告者'] == current_username)].copy()

    if rejected_df.empty:
        st.success(" 現在、差し戻しされたレポートはありません。")
    else:
        st.warning(f" {len(rejected_df)}件のレポートが差し戻しされています。修正して再提出してください。")

        if 'selected_rejection_report_id' not in st.session_state:
            st.session_state.selected_rejection_report_id = None

        st.subheader("差し戻しレポート一覧")
        for _, report in rejected_df.iterrows():
            with st.expander(f"報告ID: {report['報告ID']} | {report.get('内容分類', '-')} | {pd.to_datetime(report['発生日時']).strftime('%Y-%m-%d %H:%M')}"):
                st.markdown("**差し戻し理由:**")
                st.error(report.get('管理者コメント', '理由が記載されていません。'))
                st.markdown("---")
                col1, col2 = st.columns(2)
                col1.write(f"**発生場所:** {report.get('発生場所', '-')}")
                col2.write(f"**影響度レベル:** {report.get('影響度レベル', '-')}")
                st.write(f"**インシデント内容:** {report.get('インシデント内容', '-')}")
                st.markdown("---")
                if st.button(f" このレポートを修正再提出", key=f"edit_btn_{report['報告ID']}", use_container_width=True):
                    st.session_state.selected_rejection_report_id = report['報告ID']
                    st.rerun()

        if st.session_state.selected_rejection_report_id is not None:
            st.markdown("---")
            st.subheader(" レポート修正フォーム（全項目）")
            
            report_data = get_report_by_id(st.session_state.selected_rejection_report_id)
            if report_data is None:
                st.error("レポートが見つかりません。")
                st.session_state.selected_rejection_report_id = None
                st.rerun()
            else:
                selected_report = rejected_df[rejected_df['報告ID'] == st.session_state.selected_rejection_report_id].iloc[0]
                st.error(f"**差し戻し理由:** {selected_report.get('管理者コメント', '-')}")
                
                with st.form(key='resubmit_form'):
                    st.markdown("### 基本情報")
                    col1, col2 = st.columns(2)
                    with col1:
                        occurrence_date = st.date_input("発生日", value=pd.to_datetime(report_data.get('occurrence_datetime')).date() if report_data.get('occurrence_datetime') else datetime.date.today())
                        reporter_name = st.text_input("報告者氏名", value=report_data.get('reporter_name', ''))
                    with col2:
                        occurrence_time = st.time_input("発生時刻", value=pd.to_datetime(report_data.get('occurrence_datetime')).time() if report_data.get('occurrence_datetime') else datetime.time(9, 0))
                        job_type = st.selectbox("職種", ["Dr", "Ns", "PT", "At", "RT", "その他"], index=["Dr", "Ns", "PT", "At", "RT", "その他"].index(report_data.get('job_type')) if report_data.get('job_type') in ["Dr", "Ns", "PT", "At", "RT", "その他"] else 0)
                    
                    location = st.text_input("発生場所", value=report_data.get('location', ''))
                    level = st.selectbox("影響度レベル", ["0", "1", "2", "3a", "3b", "4", "5", "その他"], index=["0", "1", "2", "3a", "3b", "4", "5", "その他"].index(report_data.get('level')) if report_data.get('level') in ["0", "1", "2", "3a", "3b", "4", "5", "その他"] else 0)
                    
                    st.markdown("### インシデント内容")
                    content_category = st.selectbox("内容分類", ["診察", "処置", "受付", "放射線業務", "リハビリ業務", "転倒転落", "患者対応", "機器関連", "その他"], index=["診察", "処置", "受付", "放射線業務", "リハビリ業務", "転倒転落", "患者対応", "機器関連", "その他"].index(report_data.get('content_category')) if report_data.get('content_category') in ["診察", "処置", "受付", "放射線業務", "リハビリ業務", "転倒転落", "患者対応", "機器関連", "その他"] else 0)
                    content_details = st.text_area("インシデント内容（詳細）", value=report_data.get('content_details', ''), height=100)
                    cause_details = st.text_area("発生原因", value=report_data.get('cause_details', ''), height=100)
                    
                    st.markdown("### 状況と対策")
                    situation = st.text_area("発生の状況と直後の対応", value=report_data.get('situation', ''), height=150)
                    countermeasure = st.text_area("今後の対策", value=report_data.get('countermeasure', ''), height=150)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        cancel_button = st.form_submit_button("キャンセル", use_container_width=True)
                    with col2:
                        submit_button = st.form_submit_button(" 再提出する", use_container_width=True, type="primary")
                    
                    if cancel_button:
                        st.session_state.selected_rejection_report_id = None
                        st.rerun()
                    
                    if submit_button:
                        if not reporter_name or not situation or not countermeasure:
                            st.error("報告者氏名、状況詳細、今後の対策は必須項目です。")
                        else:
                            updates = {
                                'occurrence_datetime': datetime.datetime.combine(occurrence_date, occurrence_time),
                                'reporter_name': reporter_name,
                                'job_type': job_type,
                                'location': location,
                                'level': level,
                                'content_category': content_category,
                                'content_details': content_details,
                                'cause_details': cause_details,
                                'situation': situation,
                                'countermeasure': countermeasure,
                                'status': '未読',
                                'manager_comments': ''
                            }
                            update_report_status(st.session_state.selected_rejection_report_id, updates)
                            
                            # 承認グループに通知
                            if LINEWORKS_APPROVAL_CHANNEL_ID and LINEWORKS_APPROVAL_BOT_ID:
                                message = (
                                    f"【再提出インシデント報告】\n\n"
                                    f"報告ID: {st.session_state.selected_rejection_report_id}\n"
                                    f"報告者: {reporter_name}\n"
                                    f"発生日時: {occurrence_date} {occurrence_time}\n"
                                    f"影響度レベル: {level}\n"
                                    f"内容分類: {content_category}\n\n"
                                    f"差し戻し後の修正が完了しました。再承認をお願いします。"
                                )
                                send_text_message_to_channel(message, LINEWORKS_APPROVAL_CHANNEL_ID, bot_id=LINEWORKS_APPROVAL_BOT_ID)
                            
                            st.success("レポートを再提出しました！承認管理者に通知されました。")
                            st.session_state.selected_rejection_report_id = None
                            st.rerun()
