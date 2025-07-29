import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import get_all_reports

# --- 認証チェック ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/0_Login.py")

st.set_page_config(page_title="グラフ・分析", page_icon="📊", layout="wide")

st.title("📊 グラフ・分析ダッシュボード")
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
        'level': '影響度レベル',
        'location': '発生場所',
        'connection_with_accident': '事故との関連性',
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
    
    level_order = ["0", "1", "2", "3a", "3b", "4", "5", "その他"]
    
    # '影響度レベル' 列を、定義した順序を持つ「カテゴリ型」に変換する
    try:
        df['影響度レベル'] = pd.Categorical(df['影響度レベル'], categories=level_order, ordered=True)
    except Exception as e:
        st.error(f"データ型の変換中にエラーが発生しました: {e}")
        st.info("データに予期せぬ値が含まれている可能性があります。")
        
    st.header("インシデント傾向分析")

    # --- 1行目: 影響度レベル円グラフと内容分類棒グラフ ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("影響度レベルの割合")
        # 影響度レベルのカウントを降順でソート
        level_counts = df['影響度レベル'].value_counts().sort_values(ascending=False)
        fig_pie_level = px.pie(
            level_counts, 
            values=level_counts.values, 
            names=level_counts.index, 
            title='影響度レベル別インシデント件数',
            hole=0.3, # ドーナツグラフにする
            color_discrete_sequence=px.colors.sequential.RdBu # 色のシーケンス
        )
        fig_pie_level.update_traces(textposition='inside', textinfo='percent+label', sort=False)
        st.plotly_chart(fig_pie_level, use_container_width=True)

    with col2:
        st.subheader("内容分類別インシデント件数")
        # 内容分類のカウントを降順でソート
        content_category_counts = df['内容分類'].value_counts().sort_values(ascending=False)
        fig_bar_category = px.bar(
            content_category_counts, 
            x=content_category_counts.index, 
            y=content_category_counts.values, 
            title='内容分類別',
            labels={'x':'内容分類', 'y':'件数'},
            color_discrete_sequence=px.colors.qualitative.Pastel # 色のシーケンス
        )
        fig_bar_category.update_layout(xaxis_tickangle=-45) # X軸ラベルを斜めにする
        st.plotly_chart(fig_bar_category, use_container_width=True)

    st.markdown("--- ")

    # --- 2行目: 発生場所棒グラフと職種別インシデント詳細円グラフ ---
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("発生場所別インシデント件数")
        # 発生場所のカウントを降順でソート
        location_counts = df['発生場所'].value_counts().sort_values(ascending=False)
        fig_bar_location = px.bar(
            location_counts, 
            x=location_counts.index, 
            y=location_counts.values, 
            title='発生場所別',
            labels={'x':'発生場所', 'y':'件数'},
            color_discrete_sequence=px.colors.qualitative.Pastel # 色のシーケンス
        )
        fig_bar_location.update_layout(xaxis_tickangle=-45) # X軸ラベルを斜めにする
        st.plotly_chart(fig_bar_location, use_container_width=True)

    with col4:
        st.subheader("職種ごとのインシデント詳細")
        # 職種の表示順を定義
        job_type_order = ["Dr", "Ns", "PT", "At", "RT", "その他"]
        # 既存のデータフレームからユニークな職種を取得し、定義した順序でソート
        # データに存在しない職種は表示されないようにする
        available_job_types = [job for job in job_type_order if job in df['職種'].unique()]
        selected_job_type = st.selectbox("職種を選択してください", available_job_types)

        if selected_job_type:
            filtered_by_job = df[df['職種'] == selected_job_type]
            if not filtered_by_job.empty:
                # インシデント内容をカンマで分割し、フラット化してカウント
                # 空文字列やNaNを除外
                incident_details_counts = filtered_by_job['インシデント内容'].dropna().str.split(',').explode().str.strip()
                # データを降順でソート
                incident_details_counts = incident_details_counts[incident_details_counts != ''].value_counts().sort_values(ascending=False)

                if not incident_details_counts.empty:
                    fig_pie_job_incident_details = px.pie(
                        incident_details_counts, 
                        values=incident_details_counts.values, 
                        names=incident_details_counts.index, 
                        title=f'{selected_job_type} のインシデント内容別件数',
                        hole=0.3,
                        color_discrete_sequence=px.colors.sequential.Plasma
                    )
                    fig_pie_job_incident_details.update_traces(textposition='inside', textinfo='percent+label', sort=False)
                    st.plotly_chart(fig_pie_job_incident_details, use_container_width=True)
                else:
                    st.info(f"{selected_job_type} のインシデント内容データはありません。")
            else:
                st.info(f"{selected_job_type} のインシデントデータはありません。")

    st.markdown("--- ")

    # --- 3行目: 時系列グラフ ---
    st.subheader("月別インシデント発生件数")
    df_time = df.copy()
    df_time['発生日時'] = pd.to_datetime(df_time['発生日時'])
    # 月別カウントを降順でソート
    monthly_counts = df_time.set_index('発生日時').resample('ME').size().sort_index(ascending=False)
    monthly_counts.index = monthly_counts.index.strftime('%Y-%m')
    
    fig_line_monthly = px.line(
        monthly_counts, 
        x=monthly_counts.index, 
        y=monthly_counts.values, 
        title='月別インシデント発生件数',
        labels={'x':'年月', 'y':'件数'},
        markers=True # マーカーを表示
    )
    # 時系列グラフのX軸は通常昇順なので、ここではソート順を調整しない
    st.plotly_chart(fig_line_monthly, use_container_width=True)
