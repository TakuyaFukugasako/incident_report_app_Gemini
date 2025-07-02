import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import get_all_reports

# --- 認証チェック ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/0_Login.py")

st.set_page_config(page_title="グラフ・分析", page_icon="")

st.title(" グラフ・分析ダッシュボード")
st.markdown("---")

df = get_all_reports()

if df.empty:
    st.info("分析対象のデータがありません。「新規報告」ページから入力してください。")
else:
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
        'created_at': '報告日時'
    }, inplace=True)
    
    level_order = ["0", "1", "2", "3a", "3b", "4", "5", "その他"]
    
    # '影響度レベル' 列を、定義した順序を持つ「カテゴリ型」に変換する
    # これにより、この後の .sort_index() がこの定義通りの順番で動作するようになる
    try:
        df['影響度レベル'] = pd.Categorical(df['影響度レベル'], categories=level_order, ordered=True)
    except Exception as e:
        st.error(f"データ型の変換中にエラーが発生しました: {e}")
        st.info("データに予期せぬ値が含まれている可能性があります。")
        
    st.header("インシデント傾向分析")

    # 影響度レベルの円グラフ
    st.subheader("影響度レベルの割合")
    level_counts = df['影響度レベル'].value_counts()
    fig_pie = px.pie(
        level_counts, 
        values=level_counts.values, 
        names=level_counts.index, 
        title='影響度レベル別'
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # 2列レイアウト
    col1, col2 = st.columns(2)

    with col1:
        # 発生場所ごとの棒グラフ
        st.subheader("発生場所別 件数")
        location_counts = df['発生場所'].value_counts()
        st.bar_chart(location_counts)

    with col2:
        # 職種ごとの棒グラフ
        st.subheader("報告者の職種別 件数")
        job_counts = df['職種'].value_counts()
        st.bar_chart(job_counts)

    # 時系列分析
    st.subheader("月別インシデント発生件数")
    # '発生日時'列をdatetime型に変換（もし文字列なら）
    df_time = df.copy()
    df_time['発生日時'] = pd.to_datetime(df_time['発生日時'])
    # 月ごとに集計
    monthly_counts = df_time.set_index('発生日時').resample('ME').size()
    monthly_counts.index = monthly_counts.index.strftime('%Y-%m')
    st.line_chart(monthly_counts)