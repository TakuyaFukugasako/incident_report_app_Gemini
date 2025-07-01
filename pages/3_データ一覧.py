import streamlit as st
import pandas as pd
from db_utils import get_all_reports

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
        'patient_status_change_patient_explanation': '患者説明',
        'patient_status_change_family_explanation': '家族説明',
        'content_category': '内容分類',
        'content_details': 'インシデント内容',
        'cause_details': '発生原因',
        'manual_relation': 'マニュアル関連',
        'situation': '状況詳細',
        'countermeasure': '今後の対策',
        'created_at': '報告日時'
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
                content_categories = st.multiselect("内容分類", options=df['内容分類'].unique(), default=st.session_state.search_criteria.get('content_categories', []))
            with c6:
                content_details = st.text_input("インシデント内容", value=st.session_state.search_criteria.get('content_details'))

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
        # 入力された値をセッションステートに保存
        st.session_state.search_criteria = {
            'start_date': start_date,
            'end_date': end_date,
            'reporter_name': reporter_name,
            'locations': locations,
            'levels': levels,
            'job_types': job_types,
            'content_categories': content_categories,
            'content_details': content_details,
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
        filtered_df = filtered_df[filtered_df['内容分類'].isin(criteria['content_categories'])]
    if criteria.get('content_details'):
        filtered_df = filtered_df[filtered_df['インシデント内容'].str.contains(criteria['content_details'], na=False)]
    if criteria.get('keyword'):
        kw = criteria['keyword']
        filtered_df = filtered_df[filtered_df.apply(lambda row: kw in str(row['状況詳細']) or kw in str(row['今後の対策']), axis=1)]

    st.header("検索結果")
    st.write(f"該当件数: {len(filtered_df)} 件")

    # --- セッションステートの初期化 ---
    if 'selected_report_id' not in st.session_state:
        st.session_state.selected_report_id = None

    # --- 検索結果をPandas風テーブルで表示 ---
    # ヘッダー
    header_cols = st.columns([3, 1, 2, 3, 3, 1, 1])
    headers = ["発生日時", "職種", "発生場所", "内容分類", "報告者", "Lv.", "-"]
    for col, header in zip(header_cols, headers):
        col.markdown(f"**{header}**")
    st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)

    # データ行
    for _, report in filtered_df.iterrows():
        data_cols = st.columns([3, 1, 2, 3, 3, 1, 1])
        data_cols[0].write(report['発生日時'].strftime('%Y-%m-%d %H:%M'))
        data_cols[1].write(report.get('職種', '-'))
        data_cols[2].write(report.get('発生場所', '-'))
        data_cols[3].write(report.get('内容分類', '-'))
        data_cols[4].write(report.get('報告者', '-'))
        data_cols[5].write(report.get('影響度レベル', '-'))
        
        button_placeholder = data_cols[6].empty()
        if button_placeholder.button("詳細", key=f"detail_btn_{report['報告ID']}", use_container_width=True):
            st.session_state.selected_report_id = report['報告ID']
            st.rerun()
        st.markdown("<hr style='margin-top: 0; margin-bottom: 0;'>", unsafe_allow_html=True)

    # --- 詳細表示エリア ---
    if st.session_state.selected_report_id is not None:
        st.markdown("---")
        st.markdown(f"<h2 style='text-align: center; color: #2c3e50; margin-bottom: 20px;'>インシデント報告詳細レポート <br> <small style='font-size: 0.6em; color: #7f8c8d;'>報告ID: {st.session_state.selected_report_id}</small></h2>", unsafe_allow_html=True)
        
        selected_report_details = filtered_df[filtered_df['報告ID'] == st.session_state.selected_report_id]

        if not selected_report_details.empty:
            report_details = selected_report_details.iloc[0]

            # レポート全体のコンテナ
            st.markdown("<div style='border: 1px solid #dcdcdc; border-radius: 12px; padding: 30px; background-color: #ffffff; box-shadow: 0 8px 20px rgba(0,0,0,0.08);'>", unsafe_allow_html=True)

            # --- 閉じるボタン ---
            close_col, _ = st.columns([1, 5])
            with close_col:
                if st.button("✖️ 閉じる", key="close_detail_view", use_container_width=True):
                    st.session_state.selected_report_id = None
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

            # --- スタイリングのためのHTMLヘルパー関数 ---
            def section_header(title):
                return f"<h3 style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-top: 35px; margin-bottom: 20px; font-weight: 600; letter-spacing: 0.5px;'>{title}</h3>"

            def detail_item_html(label, value):
                return f"<div style='margin-bottom: 12px; font-size: 16px; color: #34495e;'><b style='color: #2c3e50; margin-right: 5px;'>{label}:</b> {value}</div>"

            def detail_block_html(label, value):
                escaped_value = str(value).replace('\n', '<br>')
                return f"<div style='margin-bottom: 20px;'><b style='display: block; margin-bottom: 8px; color: #2c3e50; font-size: 16px;'>{label}:</b><div style='padding: 18px; background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; line-height: 1.7; color: #333; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);'>{escaped_value if escaped_value else '-'}</div></div>"

            # --- 概要サマリー --- (上司向け)
            st.markdown(section_header("概要"), unsafe_allow_html=True)
            summary_cols = st.columns([2, 3, 2])
            with summary_cols[0]:
                st.markdown(detail_item_html("影響度レベル", report_details.get('影響度レベル', '-')), unsafe_allow_html=True)
            with summary_cols[1]:
                st.markdown(detail_item_html("発生日時", pd.to_datetime(report_details.get('発生日時')).strftime('%Y年%m月%d日 %H時%M分') if pd.notna(report_details.get('発生日時')) else '-'), unsafe_allow_html=True)
            with summary_cols[2]:
                st.markdown(detail_item_html("報告者", report_details.get('報告者', '-')), unsafe_allow_html=True)
            
            # --- 基本情報 ---
            st.markdown(section_header("基本情報"), unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(detail_item_html("発生場所", report_details.get('発生場所', '-')), unsafe_allow_html=True)
                st.markdown(detail_item_html("職種", report_details.get('職種', '-')), unsafe_allow_html=True)
                st.markdown(detail_item_html("経験年数", report_details.get('経験年数', '-')), unsafe_allow_html=True)
                st.markdown(detail_item_html("患者ID", report_details.get('患者ID', '-')), unsafe_allow_html=True)
            with c2:
                created_at_val = report_details.get('報告日時')
                created_at_str = pd.to_datetime(created_at_val).strftime('%Y年%m月%d日 %H時%M分') if pd.notna(created_at_val) else '-'
                st.markdown(detail_item_html("報告日時", created_at_str), unsafe_allow_html=True)
                st.markdown(detail_item_html("事故との関連性", report_details.get('事故との関連性', '-')), unsafe_allow_html=True)
                st.markdown(detail_item_html("入職年数", report_details.get('入職年数', '-')), unsafe_allow_html=True)
                st.markdown(detail_item_html("患者氏名", report_details.get('患者氏名', '-') or '-'), unsafe_allow_html=True)

            # --- インシデント詳細 ---
            st.markdown(section_header("インシデント詳細"), unsafe_allow_html=True)
            st.markdown(detail_item_html("内容分類", report_details.get('内容分類', '-')), unsafe_allow_html=True)
            st.markdown(detail_block_html("インシデント内容", report_details.get('インシデント内容', '-')), unsafe_allow_html=True)

            # --- 状況と対策 ---
            st.markdown(section_header("状況と対策"), unsafe_allow_html=True)
            st.markdown(detail_block_html("状況詳細", report_details.get('状況詳細', '-')), unsafe_allow_html=True)
            st.markdown(detail_block_html("今後の対策", report_details.get('今後の対策', '-')), unsafe_allow_html=True)

            # --- 原因分析とマニュアル関連 ---
            st.markdown(section_header("原因分析とマニュアル関連"), unsafe_allow_html=True)
            def format_cause_details(cause_details_str):
                if not cause_details_str or cause_details_str == '-':
                    return '-'
                
                formatted_html = ""
                categories = cause_details_str.split(' | ')
                for category_item in categories:
                    if ': ' in category_item:
                        category_name, items_str = category_item.split(': ', 1)
                        formatted_html += f"<b>{category_name}:</b><br>"
                        items = items_str.split(', ')
                        for item in items:
                            formatted_html += f"&nbsp;&nbsp;- {item}<br>"
                    else:
                        formatted_html += f"&nbsp;&nbsp;- {category_item}<br>" # Fallback for unexpected format
                return formatted_html

            st.markdown(detail_block_html("発生原因", format_cause_details(report_details.get('発生原因', '-'))), unsafe_allow_html=True)
            st.markdown(detail_item_html("マニュアル関連", report_details.get('マニュアル関連', '-')), unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True) # レポート全体のコンテナを閉じる

        else:
            st.session_state.selected_report_id = None
            st.rerun()


    # --- CSVダウンロードボタンは最後に配置 ---
    st.markdown("---")
    @st.cache_data
    def convert_df(df_to_convert):
        return df_to_convert.to_csv(index=False).encode('utf-8-sig')

    csv = convert_df(filtered_df)
    st.download_button(
        label="現在の検索結果をCSVでダウンロード",
        data=csv,
        file_name='filtered_incident_reports.csv',
        mime='text/csv',
    )