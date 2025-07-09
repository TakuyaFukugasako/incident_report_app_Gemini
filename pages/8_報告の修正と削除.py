import streamlit as st
import pandas as pd
import datetime
import json
from db_utils import get_all_reports, get_report_by_id, update_report, delete_report

# --- 認証チェック ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/0_Login.py")

st.set_page_config(page_title="報告の修正・削除", page_icon="📝", layout="wide")

st.title("📝 報告の修正・削除")
st.markdown("---")

# --- セッションステートの初期化 ---
if 'edit_report_id' not in st.session_state:
    st.session_state.edit_report_id = None
if 'delete_confirm_id' not in st.session_state:
    st.session_state.delete_confirm_id = None

# --- ユーザーの権限に応じて表示するレポートをフィルタリング ---
reports_df = get_all_reports()
if not reports_df.empty:
    if st.session_state.get("role") != 'admin':
        reports_df = reports_df[reports_df['reporter_name'] == st.session_state.get("username")]

# --- 編集フォーム --- 
if st.session_state.edit_report_id is not None:
    report_data = get_report_by_id(st.session_state.edit_report_id)
    
    st.header(f"報告ID: {st.session_state.edit_report_id} の修正")

    with st.form(key='edit_form'):
        # (ここに「1_新規報告.py」とほぼ同様のフォーム要素を配置)
        # 簡単のため、主要なテキスト項目のみを修正対象とします
        occurrence_datetime = pd.to_datetime(report_data.get('occurrence_datetime'))
        st.session_state.occurrence_date = st.date_input("発生日", value=occurrence_datetime.date())
        st.session_state.occurrence_time = st.time_input("発生時刻", value=occurrence_datetime.time())
        st.session_state.level = st.selectbox("影響度レベル", ["0", "1", "2", "3a", "3b", "4", "5", "その他"], index=["0", "1", "2", "3a", "3b", "4", "5", "その他"].index(report_data.get('level', '1')))
        st.session_state.reporter_name = st.text_input("代表報告者", value=report_data.get('reporter_name', ''))
        st.write("**発生場所**")
        st.session_state.occurrence_location = st.selectbox("発生場所", ["1FMRI室", "1F操作室", "1F撮影室", "1Fエコー室", "1F廊下", "1Fトイレ", "2F受付", "2F待合", "2F診察室", "2F処置室", "2Fトイレ", "3Fリハビリ室", "3F受付", "3F待合","3Fトイレ", "4Fリハビリ室", "4F受付", "4F待合","4Fトイレ"], index=(["1FMRI室", "1F操作室", "1F撮影室", "1Fエコー室", "1F廊下", "1Fトイレ", "2F受付", "2F待合", "2F診察室", "2F処置室", "2Fトイレ", "3Fリハビリ室", "3F受付", "3F待合","3Fトイレ", "4Fリハビリ室", "4F受付", "4F待合","4Fトイレ"].index(report_data.get('location', '1FMRI室')) if report_data.get('location') in ["1FMRI室", "1F操作室", "1F撮影室", "1Fエコー室", "1F廊下", "1Fトイレ", "2F受付", "2F待合", "2F診察室", "2F処置室", "2Fトイレ", "3Fリハビリ室", "3F受付", "3F待合","3Fトイレ", "4Fリハビリ室", "4F受付", "4F待合","4Fトイレ"] else 0), label_visibility="collapsed")
        st.session_state.connection_with_accident = st.multiselect("事故との関連性", ["当事者", "発見者", "患者本人より訴え", "患者家族より訴え"], default=report_data.get('connection_with_accident', '').split(', '))
        st.write("**経験年数**")
        years_col1, years_col2 = st.columns(2)
        with years_col1:
            st.session_state.years_of_experience = st.selectbox("総実務経験", ["1年未満", "1～3年未満", "3～5年未満", "5～10年未満", "10年以上"], index=["1年未満", "1～3年未満", "3～5年未満", "5～10年未満", "10年以上"].index(report_data.get('years_of_experience', '1年未満')))
        with years_col2:
            st.session_state.years_since_joining = st.selectbox("入職年数", ["1年未満", "1～3年未満", "3～5年未満", "5～10年未満", "10年以上"], index=["1年未満", "1～3年未満", "3～5年未満", "5～10年未満", "10年以上"].index(report_data.get('years_since_joining', '1年未満')))
        st.session_state.situation = st.text_area("発生の状況と直後の対応", value=report_data.get('situation', ''), height=150)
        st.session_state.countermeasure = st.text_area("今後の対策", value=report_data.get('countermeasure', ''), height=150)

        update_button = st.form_submit_button('✅ 更新する')
        cancel_button = st.form_submit_button('キャンセル')

    if update_button:
        updated_data = {
            'occurrence_datetime': datetime.datetime.combine(st.session_state.occurrence_date, st.session_state.occurrence_time),
            'level': st.session_state.level,
            'reporter_name': st.session_state.reporter_name,
            'location': st.session_state.occurrence_location,
            'connection_with_accident': ', '.join(st.session_state.connection_with_accident or []),
            'years_of_experience': st.session_state.years_of_experience,
            'years_since_joining': st.session_state.years_since_joining,
            'situation': st.session_state.situation,
            'countermeasure': st.session_state.countermeasure
        }
        update_report(st.session_state.edit_report_id, updated_data)
        st.success(f"報告ID: {st.session_state.edit_report_id} を更新しました。")
        st.session_state.edit_report_id = None
        st.rerun()

    if cancel_button:
        st.session_state.edit_report_id = None
        st.rerun()

# --- 一覧表示 --- 
else:
    if reports_df.empty:
        st.info("修正・削除可能な報告はありません。")
    else:
        st.header("報告一覧")
        for index, row in reports_df.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
                col1.text(f"発生日時: {pd.to_datetime(row['occurrence_datetime']).strftime('%Y-%m-%d %H:%M')}")
                col2.text(f"報告者: {row['reporter_name']}")
                col3.text(f"レベル: {row['level']}")
                
                if col4.button("修正", key=f"edit_{index}"):
                    st.session_state.edit_report_id = index
                    st.rerun()
                
                if col5.button("削除", key=f"delete_{index}"):
                    st.session_state.delete_confirm_id = index
                    st.rerun()

                # 削除確認
                if st.session_state.delete_confirm_id == index:
                    st.warning(f"本当に報告ID: {index} を削除しますか？この操作は元に戻せません。")
                    confirm_col1, confirm_col2 = st.columns(2)
                    if confirm_col1.button("はい、削除します", key=f"confirm_delete_{index}"):
                        delete_report(index)
                        st.success(f"報告ID: {index} を削除しました。")
                        st.session_state.delete_confirm_id = None
                        st.rerun()
                    if confirm_col2.button("キャンセル", key=f"cancel_delete_{index}"):
                        st.session_state.delete_confirm_id = None
                        st.rerun()
            st.markdown("---")
