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

    # --- フォームのデフォルト値を設定 ---
    for key, value in report_data.items():
        if key.startswith('content_details_') or key == 'injury_details':
            try:
                st.session_state[key] = json.loads(value) if isinstance(value, str) else []
            except (json.JSONDecodeError, TypeError):
                st.session_state[key] = []
        elif key == 'occurrence_datetime' and value:
            dt = pd.to_datetime(value)
            st.session_state['occurrence_date'] = dt.date()
            st.session_state['occurrence_time'] = dt.time()
        elif key == 'connection_with_accident' and isinstance(value, str):
            st.session_state[key] = [item.strip() for item in value.split(',')]
        else:
            st.session_state[key] = value

    # --- フォーム --- 
    with st.form(key='edit_report_form', clear_on_submit=False):
        st.subheader("内容を修正してください")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- 基本情報 ---
        st.subheader("基本情報")
        level_options = ["0", "1", "2", "3a", "3b", "4", "5", "その他"]
        level = st.selectbox("影響度レベル", level_options, key='level')
        
        st.markdown("--- ")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**発生日時**")
            sub_col1, sub_col2 = st.columns([2, 1])
            sub_col1.date_input("発生日", key="occurrence_date", label_visibility="collapsed")
            sub_col2.time_input("発生時刻", key="occurrence_time", label_visibility="collapsed")
                
            st.write("**代表報告者**")
            reporter_col1, reporter_col2 = st.columns([2, 1])
            reporter_col1.text_input("報告者氏名", key="reporter_name", placeholder="氏名を入力", label_visibility="collapsed")
            reporter_col2.selectbox("職種", ["Dr", "Ns", "PT", "At", "RT", "その他"], key="job_type", label_visibility="collapsed")
                
            st.write("**事故との関連性**")
            st.multiselect("関連性をすべて選択", ["当事者", "発見者", "患者本人より訴え", "患者家族より訴え"], key='connection_with_accident', label_visibility="collapsed")
            
            st.write("**経験年数**")
            years_col1, years_col2 = st.columns(2)
            years_col1.selectbox("総実務経験", ["1年未満", "1～3年未満", "3～5年未満", "5～10年未満", "10年以上"], key="years_of_experience")
            years_col2.selectbox("入職年数", ["1年未満", "1～3年未満", "3～5年未満", "5～10年未満", "10年以上"], key="years_since_joining")
            
        with col2:
            st.write("**患者情報**")
            patient_id_col, patient_name_col = st.columns([1, 2])
            patient_id_col.text_input("患者ID", key="patient_ID", placeholder="IDを入力", label_visibility="collapsed")
            patient_name_col.text_input("患者氏名", key="patient_name", placeholder="氏名を入力", label_visibility="collapsed")

            gender_col, age_col, dementia_col = st.columns([1, 1, 2])
            with gender_col:
                st.write("**性別**")
                st.selectbox("性別", ["", "男性", "女性", "その他"], key="patient_gender", label_visibility="collapsed")
            with age_col:
                st.write("**年齢**")
                st.number_input("年齢", min_value=0, max_value=150, key="patient_age", label_visibility="collapsed")
            with dementia_col:
                st.write("**認知症の有無**")
                st.selectbox("認知症の有無", ["", "あり", "なし", "不明"], key="dementia_status", label_visibility="collapsed")
            
            st.write("**発生場所**")
            st.selectbox("発生場所", ["1FMRI室", "1F操作室", "1F撮影室", "1Fエコー室", "1F廊下", "1Fトイレ", "2F受付", "2F待合", "2F診察室", "2F処置室", "2Fトイレ", "3Fリハビリ室", "3F受付", "3F待合","3Fトイレ", "4Fリハビリ室", "4F受付", "4F待合","4Fトイレ"], key="location", label_visibility="collapsed")

            st.write("**状態変化・説明**")
            col_change, col_change_radio = st.columns([3, 1])
            col_change.write("事故などによる患者の状態変化")
            col_change_radio.radio("", ["有", "無"], key="patient_status_change_accident", horizontal=True, label_visibility="collapsed")

            col_patient, col_patient_radio = st.columns([3, 1])
            col_patient.write("患者への説明")
            col_patient_radio.radio("", ["有", "無"], key="patient_status_change_patient_explanation", horizontal=True, label_visibility="collapsed")

            col_family, col_family_radio = st.columns([3, 1])
            col_family.write("家族への説明")
            col_family_radio.radio("", ["有", "無"], key="patient_status_change_family_explanation", horizontal=True, label_visibility="collapsed")

        st.markdown("--- ")
        st.subheader("状況と対策")
        st.text_area("発生の状況と直後の対応（詳細に記入）", key="situation")
        st.text_area("今後の対策（箇条書きで記入）", key="countermeasure")

        st.markdown("--- ")
        update_button = st.form_submit_button(label='✅ この内容で更新する', use_container_width=True)
        cancel_button = st.form_submit_button(label='キャンセル', use_container_width=True)

    if update_button:
        updated_data = {
            "occurrence_datetime": datetime.datetime.combine(st.session_state.occurrence_date, st.session_state.occurrence_time),
            "reporter_name": st.session_state.reporter_name,
            "job_type": st.session_state.job_type,
            "level": st.session_state.level,
            "location": st.session_state.location,
            "connection_with_accident": ", ".join(st.session_state.connection_with_accident or []),
            "years_of_experience": st.session_state.years_of_experience,
            "years_since_joining": st.session_state.years_since_joining,
            "patient_ID": st.session_state.patient_ID,
            "patient_name": st.session_state.patient_name,
            "patient_gender": st.session_state.patient_gender,
            "patient_age": st.session_state.patient_age,
            "dementia_status": st.session_state.dementia_status,
            "patient_status_change_accident": st.session_state.patient_status_change_accident,
            "patient_status_change_patient_explanation": st.session_state.patient_status_change_patient_explanation,
            "patient_status_change_family_explanation": st.session_state.patient_status_change_family_explanation,
            "situation": st.session_state.situation,
            "countermeasure": st.session_state.countermeasure
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
