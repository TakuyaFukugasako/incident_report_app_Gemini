import streamlit as st
import pandas as pd
from db_utils import get_all_reports, update_report_status
import datetime

# --- 認証チェック ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/0_Login.py")

# --- ロールベースのアクセス制御 ---
if st.session_state.get("role") != "admin":
    st.warning("このページにアクセスする権限がありません。管理者としてログインしてください。")
    st.stop() # ページの実行を停止

st.set_page_config(page_title="承認管理", page_icon="✅", layout="wide")

st.title("✅ 承認管理")
st.markdown("--- ")

df = get_all_reports()

if df.empty:
    st.info("現在、レポートは1件も報告されていません。")
else:
    df.reset_index(inplace=True) # idを列に変換
    # --- 列名の日本語化 ---
    df.rename(columns={
        'id': '報告ID',
        'occurrence_datetime': '発生日時',
        'reporter_name': '報告者',
        'job_type': '職種',
        'level': '影響度レベル',
        'location': '発生場所',
        'connection_with_accident': '事故との関連性',
        'years_of_experience': '経験年数',
        'years_since_joining': '入職年数',
        'patient_ID': '患者ID',
        'patient_name': '患者氏名',
        'patient_gender': '性別',
        'patient_age': '年齢',
        'dementia_status': '認知症の有無',
        'patient_status_change_accident': '患者状態変化',
        'patient_status_change_patient_explanation': '患者への説明',
        'patient_status_change_family_explanation': '家族への説明',
        'content_category': '内容分類',
        'content_details': 'インシデント内容',
        'cause_details': '発生原因',
        'manual_relation': 'マニュアル関連',
        'situation': '状況詳細',
        'countermeasure': '今後の対策',
        'created_at': '報告日時',
        'status': 'ステータス',
        'approver1': '承認者1',
        'approved_at1': '承認日時1',
        'approver2': '承認者2',
        'approved_at2': '承認日時2',
        'manager_comments': '管理者コメント'
    }, inplace=True)

    # --- 未承認レポートのフィルタリング ---
    unapproved_df = df[df['ステータス'].isin(['未読', '承認中(1/2)'])].copy()

    st.subheader("承認待ちレポート一覧")
    if unapproved_df.empty:
        st.success("🎉 現在、承認待ちのレポートはありません。")
    else:
        st.info(f"現在、{len(unapproved_df)}件のレポートが承認を待っています。")

        # --- セッションステートの初期化 ---
        if 'selected_approval_report_id' not in st.session_state:
            st.session_state.selected_approval_report_id = None

        # --- 一覧表示 ---
        header_cols = st.columns([1, 3, 1, 2, 3, 3, 1, 1])
        headers = ["ステータス", "発生日時", "職種", "発生場所", "内容分類", "報告者", "Lv.", ""]
        for col, header in zip(header_cols, headers):
            col.markdown(f"**{header}**")
        st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)

        for _, report in unapproved_df.iterrows():
            data_cols = st.columns([1, 3, 1, 2, 3, 3, 1, 1])
            status = report.get('ステータス', '-')
            status_color = {"未読": "#e74c3c", "承認中(1/2)": "#f39c12"}.get(status, "#7f8c8d")
            data_cols[0].markdown(f"<span style='color: {status_color};'>●</span> {status}", unsafe_allow_html=True)
            data_cols[1].write(pd.to_datetime(report['発生日時']).strftime('%Y-%m-%d %H:%M'))
            data_cols[2].write(report.get('職種', '-'))
            data_cols[3].write(report.get('発生場所', '-'))
            data_cols[4].write(report.get('内容分類', '-'))
            data_cols[5].write(report.get('報告者', '-'))
            data_cols[6].write(report.get('影響度レベル', '-'))
            if data_cols[7].button("承認", key=f"approve_btn_{report['報告ID']}", use_container_width=True):
                st.session_state.selected_approval_report_id = report['報告ID']
                st.rerun()
            st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)

        # --- 詳細表示・承認アクションエリア ---
        if st.session_state.selected_approval_report_id is not None:
            st.markdown("---")
            selected_report_details = unapproved_df[unapproved_df['報告ID'] == st.session_state.selected_approval_report_id].iloc[0]
            
            st.markdown(f"<h2 style='text-align: center; color: #2c3e50; margin-bottom: 20px;'>インシデント報告詳細レポート <br> <small style='font-size: 0.6em; color: #7f8c8d;'>報告ID: {st.session_state.selected_approval_report_id}</small></h2>", unsafe_allow_html=True)
            

            if st.button("✖️ 閉じる", key="close_approval_view"):
                st.session_state.selected_approval_report_id = None
                st.rerun()

            def section_header(title):
                return f"<h4 style='font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif; color: #1a5276; border-bottom: 2px solid #aed6f1; padding-bottom: 10px; margin-top: 30px; margin-bottom: 20px; font-weight: bold;'>{title}</h4>"

            def detail_item_html(label, value, highlight=False):
                value_style = "font-weight: bold; color: #c0392b;" if highlight else ""
                return f"<div style='margin-bottom: 14px; font-size: 18px;'><b style='color: #566573; min-width: 120px; display: inline-block;'>{label}：</b> <span style='{value_style}'>{value}</span></div>"

            def detail_block_html(label, value):
                escaped_value = str(value).replace('\n', '<br>')
                return f"<div style='margin-bottom: 22px;'><b style='display: block; margin-bottom: 8px; color: #566573; font-size: 17px;'>{label}：</b><div style='padding: 18px; background-color: #fdfefe; border: 1px solid #e5e7e9; border-radius: 8px; line-height: 1.7; color: #34495e; font-size: 16px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.04);'>{escaped_value if escaped_value else '-'}</div></div>"

            # --- 概要サマリー ---
            st.markdown(section_header("概要"), unsafe_allow_html=True)
            summary_cols = st.columns([1, 2, 2])
            with summary_cols[0]:
                st.markdown(detail_item_html("影響度レベル", selected_report_details.get('影響度レベル', '-'), highlight=True), unsafe_allow_html=True)
            with summary_cols[1]:
                st.markdown(detail_item_html("発生日時", pd.to_datetime(selected_report_details.get('発生日時')).strftime('%Y年%m月%d日 %H:%M') if pd.notna(selected_report_details.get('発生日時')) else '-'), unsafe_allow_html=True)
            with summary_cols[2]:
                st.markdown(detail_item_html("報告者", selected_report_details.get('報告者', '-')), unsafe_allow_html=True)
            
            # --- 患者情報 ---
            st.markdown(section_header("患者情報"), unsafe_allow_html=True)
            p1, p2 = st.columns(2)
            with p1:
                st.markdown(detail_item_html("患者ID", selected_report_details.get('患者ID', '-')), unsafe_allow_html=True)
                st.markdown(detail_item_html("性別", selected_report_details.get('性別', '-')), unsafe_allow_html=True)
                st.markdown(detail_item_html("認知症の有無", selected_report_details.get('認知症の有無', '-')), unsafe_allow_html=True)
            with p2:
                st.markdown(detail_item_html("患者氏名", selected_report_details.get('患者氏名', '-') or '-'), unsafe_allow_html=True)
                st.markdown(detail_item_html("年齢", str(int(selected_report_details.get('年齢', 0))) + ' 歳' if pd.notna(selected_report_details.get('年齢')) else '-'), unsafe_allow_html=True)

            # --- インシデント分析 ---
            st.markdown(section_header("インシデント分析"), unsafe_allow_html=True)
            st.markdown(detail_item_html("発生場所", selected_report_details.get('発生場所', '-')), unsafe_allow_html=True)
            st.markdown(detail_item_html("内容分類", selected_report_details.get('内容分類', '-')), unsafe_allow_html=True)
            st.markdown(detail_block_html("インシデント内容", selected_report_details.get('インシデント内容', '-')), unsafe_allow_html=True)
            st.markdown(detail_block_html("状況詳細", selected_report_details.get('状況詳細', '-')), unsafe_allow_html=True)
            st.markdown(detail_block_html("今後の対策", selected_report_details.get('今後の対策', '-')), unsafe_allow_html=True)

            # --- 報告者情報と経緯 ---
            st.markdown(section_header("報告者情報と経緯"), unsafe_allow_html=True)
            r1, r2 = st.columns(2)
            with r1:
                st.markdown(detail_item_html("職種", selected_report_details.get('職種', '-')), unsafe_allow_html=True)
                st.markdown(detail_item_html("経験年数", selected_report_details.get('経験年数', '-')), unsafe_allow_html=True)
                st.markdown(detail_item_html("事故との関連性", selected_report_details.get('事故との関連性', '-')), unsafe_allow_html=True)
            with r2:
                created_at_val = selected_report_details.get('報告日時')
                created_at_str = pd.to_datetime(created_at_val).strftime('%Y年%m月%d日 %H:%M') if pd.notna(created_at_val) else '-'
                st.markdown(detail_item_html("報告日時", created_at_str), unsafe_allow_html=True)
                st.markdown(detail_item_html("入職年数", selected_report_details.get('入職年数', '-')), unsafe_allow_html=True)

            # --- 状態変化と説明 ---
            st.markdown(section_header("状態変化と説明"), unsafe_allow_html=True)
            e1, e2, e3 = st.columns(3)
            with e1:
                st.markdown(detail_item_html("患者の状態変化", selected_report_details.get('患者状態変化', '-'), highlight=selected_report_details.get('患者状態変化') == '有'), unsafe_allow_html=True)
            with e2:
                st.markdown(detail_item_html("患者への説明", selected_report_details.get('患者への説明', '-'), highlight=selected_report_details.get('患者への説明') == '有'), unsafe_allow_html=True)
            with e3:
                st.markdown(detail_item_html("家族への説明", selected_report_details.get('家族への説明', '-'), highlight=selected_report_details.get('家族への説明') == '有'), unsafe_allow_html=True)

            st.markdown(section_header("原因分析とマニュアル"), unsafe_allow_html=True)
            def format_cause_details(cause_details_str):
                if not cause_details_str or cause_details_str == '-': return '-'
                html = ""
                for cat_item in cause_details_str.split(' | '):
                    if '： ' in cat_item: # ここも全角コロンに
                        cat, items = cat_item.split('： ', 1)
                        html += f"<div style='margin-bottom: 5px;'><b>{cat}：</b><ul style='margin: 0; padding-left: 20px;'>"
                        for item in items.split(', '): html += f"<li>{item}</li>"
                        html += "</ul></div>"
                    else:
                        html += f"<li>{cat_item}</li>" # Fallback for unexpected format
                return html
            st.markdown(detail_block_html("発生原因", format_cause_details(selected_report_details.get('発生原因', '-'))), unsafe_allow_html=True)
            st.markdown(detail_item_html("マニュアル関連", selected_report_details.get('マニュアル関連', '-')), unsafe_allow_html=True)

            # --- 承認ワークフロー ---
            st.markdown(section_header("承認ワークフロー"), unsafe_allow_html=True)
            wf1, wf2 = st.columns(2)
            wf1.markdown(detail_item_html("ステータス", selected_report_details.get('ステータス', '-'), highlight=True), unsafe_allow_html=True)
            wf1.markdown(detail_item_html("承認者1", selected_report_details.get('承認者1', '-')), unsafe_allow_html=True)
            wf2.markdown(detail_item_html("承認日時1", pd.to_datetime(selected_report_details.get('承認日時1')).strftime('%Y-%m-%d %H:%M') if pd.notna(selected_report_details.get('承認日時1')) else '-'), unsafe_allow_html=True)
            wf1.markdown(detail_item_html("承認者2", selected_report_details.get('承認者2', '-')), unsafe_allow_html=True)
            wf2.markdown(detail_item_html("承認日時2", pd.to_datetime(selected_report_details.get('承認日時2')).strftime('%Y-%m-%d %H:%M') if pd.notna(selected_report_details.get('承認日時2')) else '-'), unsafe_allow_html=True)
            st.markdown(detail_block_html("管理者フィードバック", selected_report_details.get('管理者コメント', '-')), unsafe_allow_html=True)

            if selected_report_details.get('ステータス') != '承認済み':
                with st.form(key='approval_form_in_approval_page'):
                    st.markdown("<b>承認アクション</b>", unsafe_allow_html=True)
                    approver_name_display = st.session_state.get("username", "不明")
                    st.markdown(f"**承認予定者名:** {approver_name_display}")
                    manager_comment_input = st.text_area("管理者フィードバック（任意）", value=selected_report_details.get('管理者コメント', ''))
                    if st.form_submit_button("承認する", use_container_width=True):
                        approver_name = st.session_state.get("username", "不明なユーザー")
                        
                        # 同一ユーザーによる連続承認をチェック
                        if selected_report_details.get('ステータス') == '承認中(1/2)' and selected_report_details.get('承認者1') == approver_name:
                            st.warning(f"このレポートは既に {approver_name} によって承認されています。同一ユーザーによる連続承認はできません。")
                        else:
                            updates = {"manager_comments": manager_comment_input}
                            if selected_report_details.get('ステータス') == '未読':
                                updates.update({'status': '承認中(1/2)', 'approver1': approver_name, 'approved_at1': datetime.datetime.now()})
                            elif selected_report_details.get('ステータス') == '承認中(1/2)':
                                updates.update({'status': '承認済み', 'approver2': approver_name, 'approved_at2': datetime.datetime.now()})
                            update_report_status(st.session_state.selected_approval_report_id, updates, approver_id=st.session_state.get('id'))
                            st.success("承認状態を更新しました。")
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)