import streamlit as st
import pandas as pd
from db_utils import get_all_reports, update_report_status
import datetime

# --- 認証チェック ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/0_Login.py")

st.set_page_config(page_title="検索・一覧", page_icon="🔍")

st.title(" 報告データの検索・一覧")
st.markdown("---")

df = get_all_reports() # DBから全てのデータを読み込む

if df.empty:
    st.info("まだ報告データがありません。「新規報告」ページから入力してください。")
else:
    # (DBから読み込むと文字列になっていることがあるため)
    df['occurrence_datetime'] = pd.to_datetime(df['occurrence_datetime'])
    df.reset_index(inplace=True) # idを列に変換
    # ▼▼▼ ここに列名変更の処理を追加 ▼▼▼
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
        'content_category': '大分類',
        'content_details': 'インシデント内容',
        'content_details_shinsatsu': '診察詳細',
        'content_details_shochi': '処置詳細',
        'content_details_uketsuke': '受付詳細',
        'content_details_houshasen': '放射線業務詳細',
        'content_details_rehabili': 'リハビリ業務詳細',
        'content_details_kanjataio': '患者対応詳細',
        'content_details_buhin': '物品破損詳細',
        'injury_details': '外傷詳細',
        'injury_other_text': 'その他外傷',
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
    
    st.header("データ検索")

    # --- 検索条件をセッションステートで管理 ---
    if 'search_criteria' not in st.session_state:
        st.session_state.search_criteria = {}

    with st.expander("検索条件を開く", expanded=True):
        with st.form(key='search_form'):
            # 1行目: 期間
            st.write("**発生期間**")
            date_col1, date_col2 = st.columns(2)
            start_date = date_col1.date_input("開始日", value=st.session_state.search_criteria.get('start_date'), label_visibility="collapsed")
            end_date = date_col2.date_input("終了日", value=st.session_state.search_criteria.get('end_date'), label_visibility="collapsed")

            st.markdown("--- ")
            # 2行目:
            c1, c2, c3 = st.columns(3)
            with c1:
                reporter_name = st.text_input("報告者氏名", value=st.session_state.search_criteria.get('reporter_name'))
            with c2:
                locations = st.multiselect("発生場所", options=df['発生場所'].unique(), default=st.session_state.search_criteria.get('locations', []))
            with c3:
                levels = st.multiselect("影響度レベル", options=sorted(df['影響度レベル'].unique()), default=st.session_state.search_criteria.get('levels', []))

            # 3行目:
            c4, c5, c6 = st.columns(3)
            with c4:
                job_types = st.multiselect("職種", options=df['職種'].unique(), default=st.session_state.search_criteria.get('job_types', []))
            with c5:
                content_categories = st.multiselect("大分類", options=df['大分類'].unique(), default=st.session_state.search_criteria.get('content_categories', []))
            with c6:
                all_content_details = [
                    "患者間違い", "オーダー間違い", "予約間違い", "案内間違い", "紛失", "カルテ記載間違い", "伝達漏れ", "返却忘れ", "確認漏れ", "情報漏洩",
                    "部位間違い", "ラベル間違い", "針刺し事故", "検体採り間違い", "不適切な前処置", "未処置帰宅", "薬液間違い", "会計間違い", "郵送関係", "機器登録間違い", "マーカー間違い", 
                    "骨密度解析間違い", "MRI室金属持ち込み", "画像転送忘れ", "左右間違い", "伝達間違い", "MRI完全吸着", "技師コメント間違い", "装置故障", "評価ミス", 
                    "計画書関連", "リハビリ処方による受傷", "リハビリ中の軽微な事故", "転倒", "転落", "滑落", "外傷なし", "擦過傷", "表皮剥離", "打撲", "骨折",
                    "接遇に対する不満", "検査・治療に対する不満", "医療費に対する不満", "待ち時間に対する不満", "設備・環境に対する不満", "電話対応に対する不満", 
                    "患者間のトラブル", "破損", "故障", "不具合", "操作ミス", "盗難", "在庫不足", "発注ミス", "不審者", "施錠忘れ", "災害"
                ]
                content_details = st.multiselect("インシデント内容", options=sorted(list(set(all_content_details))), default=st.session_state.search_criteria.get('content_details', []))

            st.markdown("--- ")
            # 最終行: 全文キーワード
            keyword = st.text_input("キーワード検索（状況詳細・対策など）", value=st.session_state.search_criteria.get('keyword'))

            # フォームのボタン
            st.markdown(" ") # スペース調整
            btn_col1, btn_col2, _ = st.columns([1, 1, 5])
            search_button = btn_col1.form_submit_button(label='🔍 検索', use_container_width=True)
            clear_button = btn_col2.form_submit_button(label='クリア', use_container_width=True)

    # --- フォーム送信時の処理 ---
    if search_button:
        st.session_state.search_criteria = {
            'start_date': start_date, 'end_date': end_date,
            'reporter_name': reporter_name, 'locations': locations, 'levels': levels,
            'job_types': job_types, 'content_categories': content_categories, 'content_details': content_details,
            'keyword': keyword
        }
    if clear_button:
        st.session_state.search_criteria = {}
        st.rerun()

    # --- 検索ロジック ---
    filtered_df = df.copy()
    criteria = st.session_state.search_criteria
    if criteria.get('start_date') and criteria.get('end_date'):
        start_datetime = pd.to_datetime(criteria['start_date'])
        end_datetime = pd.to_datetime(criteria['end_date']) + pd.Timedelta(days=1)
        filtered_df = filtered_df[(filtered_df['発生日時'] >= start_datetime) & (filtered_df['発生日時'] < end_datetime)]
    if criteria.get('reporter_name'):
        filtered_df = filtered_df[filtered_df['報告者'].str.contains(criteria['reporter_name'], na=False)]
    if criteria.get('locations'):
        filtered_df = filtered_df[filtered_df['発生場所'].isin(criteria['locations'])]
    if criteria.get('levels'):
        filtered_df = filtered_df[filtered_df['影響度レベル'].isin(criteria['levels'])]
    if criteria.get('job_types'):
        filtered_df = filtered_df[filtered_df['職種'].isin(criteria['job_types'])]
    if criteria.get('content_categories'):
        filtered_df = filtered_df[filtered_df['大分類'].isin(criteria['content_categories'])]
    if criteria.get('content_details'):
        search_terms = criteria['content_details']
        # 複数の詳細カラムを対象に、いずれかの検索語を含む行をフィルタリング
        detail_columns = [
            'インシデント内容', '診察詳細', '処置詳細', '受付詳細', '放射線業務詳細', 
            'リハビリ業務詳細', '患者対応詳細', '物品破損詳細', '外傷詳細', 'その他外傷'
        ]
        # DataFrameの各行に対して、指定された検索語のいずれかが詳細カラムに含まれているかを確認
        filtered_df = filtered_df[filtered_df.apply(
            lambda row: any(
                term in str(row[col]) for term in search_terms for col in detail_columns if pd.notna(row[col])
            ), 
            axis=1
        )]
    if criteria.get('keyword'):
        kw = criteria['keyword']
        filtered_df = filtered_df[filtered_df.apply(lambda row: kw in str(row['状況詳細']) or kw in str(row['今後の対策']), axis=1)]

    st.header("検索結果")
    st.write(f"該当件数: {len(filtered_df)} 件")

    if 'selected_report_id' not in st.session_state:
        st.session_state.selected_report_id = None

    # --- ページネーション --- 
    ITEMS_PER_PAGE = 10
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    total_items = len(filtered_df)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    start_index = st.session_state.current_page * ITEMS_PER_PAGE
    end_index = min(start_index + ITEMS_PER_PAGE, total_items)

    display_df = filtered_df.iloc[start_index:end_index]

    # --- 検索結果をテーブル表示 ---
    header_cols = st.columns([1, 3, 1, 2, 3, 3, 1, 1])
    headers = ["ステータス", "発生日時", "職種", "発生場所", "大分類", "報告者", "Lv.", ""]
    for col, header in zip(header_cols, headers):
        col.markdown(f"**{header}**")
    st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)

    if display_df.empty:
        st.info("該当するデータはありません。")
    else:
        for _, report in display_df.iterrows():
            data_cols = st.columns([1, 3, 1, 2, 3, 3, 1, 1])
            status = report.get('ステータス', '-')
            status_color = {"未読": "#e74c3c", "承認中(1/2)": "#f39c12", "承認済み": "#2ecc71"}.get(status, "#7f8c8d")
            data_cols[0].markdown(f"<span style='color: {status_color};'>●</span> {status}", unsafe_allow_html=True)
            data_cols[1].write(report['発生日時'].strftime('%Y-%m-%d %H:%M'))
            data_cols[2].write(report.get('職種', '-'))
            data_cols[3].write(report.get('発生場所', '-'))
            data_cols[4].write(report.get('内容分類', '-'))
            data_cols[5].write(report.get('報告者', '-'))
            data_cols[6].write(report.get('影響度レベル', '-'))
            if data_cols[7].button("詳細", key=f"detail_btn_{report['報告ID']}", use_container_width=True):
                st.session_state.selected_report_id = report['報告ID']
                st.rerun()
            st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)

        # --- ページネーションコントロール ---
        st.markdown("<br>", unsafe_allow_html=True)
        col_prev, col_info, col_next = st.columns([1, 2, 1])

        with col_prev:
            if st.session_state.current_page > 0:
                if st.button("◀ 前のページ", use_container_width=True):
                    st.session_state.current_page -= 1
                    st.rerun()
        with col_info:
            st.markdown(f"<div style='text-align: center; font-size: 1.1em; font-weight: bold;'>ページ {st.session_state.current_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
        with col_next:
            if st.session_state.current_page < total_pages - 1:
                if st.button("次のページ ▶", use_container_width=True):
                    st.session_state.current_page += 1
                    st.rerun()

    # --- 詳細表示エリア ---
    if st.session_state.selected_report_id is not None:
        st.markdown("---")
        st.markdown(f"<h2 style='text-align: center; color: #2c3e50; margin-bottom: 20px;'>インシデント報告詳細レポート <br> <small style='font-size: 0.6em; color: #7f8c8d;'>報告ID: {st.session_state.selected_report_id}</small></h2>", unsafe_allow_html=True)
        
        selected_report_details = filtered_df[filtered_df['報告ID'] == st.session_state.selected_report_id]

        if not selected_report_details.empty:
            report_details = selected_report_details.iloc[0]

            

            if st.button("✖️ 閉じる", key="close_detail_view"):
                st.session_state.selected_report_id = None
                st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

            def section_header(title): return f"<h3 style='font-family: \"Helvetica Neue\", Helvetica, Arial, sans-serif; color: #1a5276; border-bottom: 2px solid #aed6f1; padding-bottom: 10px; margin-top: 30px; margin-bottom: 20px; font-weight: bold;'>{title}</h3>"
            def detail_item_html(label, value, highlight=False): 
                value_style = "font-weight: bold; color: #c0392b;" if highlight else ""
                return f"<div style='margin-bottom: 14px; font-size: 18px;'><b style='color: #566573; min-width: 120px; display: inline-block;'>{label}：</b> <span style='{value_style}'>{value}</span></div>"
            def detail_block_html(label, value): 
                escaped_value = str(value).replace('\n', '<br>')
                return f"<div style='margin-bottom: 22px;'><b style='display: block; margin-bottom: 8px; color: #566573; font-size: 17px;'>{label}：</b><div style='padding: 18px; background-color: #fdfefe; border: 1px solid #e5e7e9; border-radius: 8px; line-height: 1.7; color: #34495e; font-size: 16px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.04);'>{escaped_value if escaped_value else '-'}</div></div>"

            st.markdown(section_header("概要"), unsafe_allow_html=True)
            s1, s2, s3 = st.columns([1, 2, 2])
            s1.markdown(detail_item_html("影響度レベル", report_details.get('影響度レベル', '-'), highlight=True), unsafe_allow_html=True)
            s2.markdown(detail_item_html("発生日時", pd.to_datetime(report_details.get('発生日時')).strftime('%Y年%m月%d日 %H時%M分') if pd.notna(report_details.get('発生日時')) else '-'), unsafe_allow_html=True)
            s3.markdown(detail_item_html("報告者", report_details.get('報告者', '-')), unsafe_allow_html=True)

            st.markdown(section_header("患者情報"), unsafe_allow_html=True)
            p1, p2 = st.columns(2)
            p1.markdown(detail_item_html("患者ID", report_details.get('患者ID', '-')), unsafe_allow_html=True)
            p2.markdown(detail_item_html("患者氏名", report_details.get('患者氏名', '-') or '-'), unsafe_allow_html=True)
            p1.markdown(detail_item_html("性別", report_details.get('性別', '-')), unsafe_allow_html=True)
            p2.markdown(detail_item_html("年齢", str(int(report_details.get('年齢', 0))) + ' 歳' if pd.notna(report_details.get('年齢')) else '-'), unsafe_allow_html=True)
            p1.markdown(detail_item_html("認知症の有無", report_details.get('認知症の有無', '-')), unsafe_allow_html=True)

            st.markdown(section_header("インシデント分析"), unsafe_allow_html=True)
            st.markdown(detail_item_html("発生場所", report_details.get('発生場所', '-')), unsafe_allow_html=True)
            st.markdown(detail_item_html("内容分類", report_details.get('内容分類', '-')), unsafe_allow_html=True)
            st.markdown(detail_block_html("インシデント内容", report_details.get('インシデント内容', '-')), unsafe_allow_html=True)
            
            # 新しい詳細項目を表示
            if report_details.get('内容分類') == "診察":
                st.markdown(detail_block_html("診察詳細", report_details.get('診察詳細', '-')), unsafe_allow_html=True)
            elif report_details.get('内容分類') == "処置":
                st.markdown(detail_block_html("処置詳細", report_details.get('処置詳細', '-')), unsafe_allow_html=True)
            elif report_details.get('内容分類') == "受付":
                st.markdown(detail_block_html("受付詳細", report_details.get('受付詳細', '-')), unsafe_allow_html=True)
            elif report_details.get('内容分類') == "放射線業務":
                st.markdown(detail_block_html("放射線業務詳細", report_details.get('放射線業務詳細', '-')), unsafe_allow_html=True)
            elif report_details.get('内容分類') == "リハビリ業務":
                st.markdown(detail_block_html("リハビリ業務詳細", report_details.get('リハビリ業務詳細', '-')), unsafe_allow_html=True)
            elif report_details.get('内容分類') == "転倒・転落":
                st.markdown(detail_block_html("転倒・転落詳細", report_details.get('転倒・転落詳細', '-')), unsafe_allow_html=True)
                st.markdown(detail_block_html("外傷詳細", report_details.get('外傷詳細', '-')), unsafe_allow_html=True)
                st.markdown(detail_block_html("その他外傷", report_details.get('その他外傷', '-')), unsafe_allow_html=True)
            elif report_details.get('内容分類') == "患者対応":
                st.markdown(detail_block_html("患者対応詳細", report_details.get('患者対応詳細', '-')), unsafe_allow_html=True)
            elif report_details.get('内容分類') == "物品破損":
                st.markdown(detail_block_html("物品破損詳細", report_details.get('物品破損詳細', '-')), unsafe_allow_html=True)
            st.markdown(detail_block_html("状況詳細", report_details.get('状況詳細', '-')), unsafe_allow_html=True)
            st.markdown(detail_block_html("今後の対策", report_details.get('今後の対策', '-')), unsafe_allow_html=True)

            st.markdown(section_header("報告者情報と経緯"), unsafe_allow_html=True)
            r1, r2 = st.columns(2)
            r1.markdown(detail_item_html("職種", report_details.get('職種', '-')), unsafe_allow_html=True)
            r2.markdown(detail_item_html("報告日時", pd.to_datetime(report_details.get('報告日時')).strftime('%Y年%m月%d日 %H:%M') if pd.notna(report_details.get('報告日時')) else '-'), unsafe_allow_html=True)
            r1.markdown(detail_item_html("経験年数", report_details.get('経験年数', '-')), unsafe_allow_html=True)
            r2.markdown(detail_item_html("入職年数", report_details.get('入職年数', '-')), unsafe_allow_html=True)
            r1.markdown(detail_item_html("事故との関連性", report_details.get('事故との関連性', '-')), unsafe_allow_html=True)

            st.markdown(section_header("状態変化と説明"), unsafe_allow_html=True)
            e1, e2, e3 = st.columns(3)
            e1.markdown(detail_item_html("患者の状態変化", report_details.get('患者状態変化', '-'), highlight=report_details.get('患者状態変化') == '有'), unsafe_allow_html=True)
            e2.markdown(detail_item_html("患者への説明", report_details.get('患者への説明', '-'), highlight=report_details.get('患者への説明') == '有'), unsafe_allow_html=True)
            e3.markdown(detail_item_html("家族への説明", report_details.get('家族への説明', '-'), highlight=report_details.get('家族への説明') == '有'), unsafe_allow_html=True)

            

            st.markdown(section_header("原因分析とマニュアル"), unsafe_allow_html=True)
            def format_cause_details(cause_details_str):
                if not cause_details_str or cause_details_str == '-': return '-'
                html = ""
                for cat_item in cause_details_str.split(' | '):
                    if ': ' in cat_item:
                        cat, items = cat_item.split(': ', 1)
                        html += f"<div style='margin-bottom: 5px;'><b>{cat}:</b><ul style='margin: 0; padding-left: 20px;'>"
                        for item in items.split(', '): html += f"<li>{item}</li>"
                        html += "</ul></div>"
                return html
            st.markdown(detail_block_html("発生原因", format_cause_details(report_details.get('発生原因', '-'))), unsafe_allow_html=True)
            st.markdown(detail_item_html("マニュアル関連", report_details.get('マニュアル関連', '-')), unsafe_allow_html=True)

            # --- 承認ワークフロー ---
            st.markdown(section_header("承認ワークフロー"), unsafe_allow_html=True)
            wf1, wf2 = st.columns(2)
            wf1.markdown(detail_item_html("ステータス", report_details.get('ステータス', '-'), highlight=True), unsafe_allow_html=True)
            wf1.markdown(detail_item_html("承認者1", report_details.get('承認者1', '-')), unsafe_allow_html=True)
            wf2.markdown(detail_item_html("承認日時1", pd.to_datetime(report_details.get('承認日時1')).strftime('%Y-%m-%d %H:%M') if pd.notna(report_details.get('承認日時1')) else '-'), unsafe_allow_html=True)
            wf1.markdown(detail_item_html("承認者2", report_details.get('承認者2', '-')), unsafe_allow_html=True)
            wf2.markdown(detail_item_html("承認日時2", pd.to_datetime(report_details.get('承認日時2')).strftime('%Y-%m-%d %H:%M') if pd.notna(report_details.get('承認日時2')) else '-'), unsafe_allow_html=True)
            st.markdown(detail_block_html("管理者コメント", report_details.get('管理者コメント', '-')), unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.session_state.selected_report_id = None
            st.rerun()