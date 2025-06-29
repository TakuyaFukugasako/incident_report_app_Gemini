import streamlit as st
import pandas as pd
from db_utils import get_all_reports

st.set_page_config(page_title="検索・一覧", page_icon="🔍")

st.title("🔍 報告データの検索・一覧")
st.markdown("---")

if 'data_version' not in st.session_state:
    st.session_state.data_version = 0
    
df = get_all_reports(st.session_state.data_version) # DBから全てのデータを読み込む

if df.empty:
    st.info("まだ報告データがありません。「新規報告」ページから入力してください。")
else:
    # 'occurrence_datetime'列をdatetime型に変換
    # (DBから読み込むと文字列になっていることがあるため)
    df['occurrence_datetime'] = pd.to_datetime(df['occurrence_datetime'])
    # ▼▼▼ ここに列名変更の処理を追加 ▼▼▼
    df.rename(columns={
        'id': '報告ID',
        'occurrence_datetime': '発生日時',
        'years_of_experience': '経験年数',
        'years_since_joining': '入職年数',
        'reporter_name': '報告者',
        'job_type': '職種',
        'level': '影響度レベル',  # ←←← 'level' を '影響度レベル' に変更！
        'location': '発生場所',
        'connection_with_accident': '事故との関連性',
        'content_details': 'インシデント内容',
        'cause_details': '発生原因',
        'manual_relation': 'マニュアル関連',
        'situation': '状況詳細',
        'countermeasure': '今後の対策',
        'created_at': '報告日時'
    }, inplace=True)
    
    st.header("データ検索")
    
    # 検索条件
    search_keyword = st.text_input("キーワード検索（状況詳細・対策など）")
    
    col1, col2 = st.columns(2)
    with col1:
        search_locations = st.multiselect(
            "発生場所で絞り込み",
            options=df['発生場所'].unique(),
            default=[]
        )
    with col2:
        search_levels = st.multiselect(
            "影響度レベルで絞り込み",
            options=sorted(df['影響度レベル'].unique()),
            default=[]
        )

    # 検索ロジック
    filtered_df = df.copy() # 元のデータフレームをコピーして使う

    # キーワード検索
    if search_keyword:
        # 複数の列を対象に検索
        filtered_df = filtered_df[
            filtered_df['状況詳細'].str.contains(search_keyword, na=False) |
            filtered_df['今後の対策'].str.contains(search_keyword, na=False) |
            filtered_df['報告者'].str.contains(search_keyword, na=False)
        ]
    
    # 発生場所での絞り込み
    if search_locations:
        filtered_df = filtered_df[filtered_df['発生場所'].isin(search_locations)]

    # 影響度レベルでの絞り込み
    if search_levels:
        filtered_df = filtered_df[filtered_df['影響度レベル'].isin(search_levels)]

    st.header("検索結果")
    st.write(f"該当件数: {len(filtered_df)} 件")
    
    # データフレームをインタラクティブに表示
    st.dataframe(filtered_df)

    # データをCSVでダウンロード
    @st.cache_data
    def convert_df(df_to_convert):
        return df_to_convert.to_csv(index=False).encode('utf-8-sig')

    csv = convert_df(filtered_df)
    st.download_button(
        label="検索結果をCSVでダウンロード",
        data=csv,
        file_name='filtered_incident_reports.csv',
        mime='text/csv',
    )