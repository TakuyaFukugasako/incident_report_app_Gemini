import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="新規報告", page_icon="📝")

st.title("📝 新規報告フォーム")
st.markdown("---")

# st.formを使うと、中の項目をすべて入力してから一度に送信できる
with st.form(key='report_form', clear_on_submit=True):
    
    # --- 基本情報（ここまでは前回と同様） ---
    st.subheader("基本情報")
    
     # ---影響度レベル---
    st.write("**影響度レベル**")
    # 選択肢を文字列のリストとして定義
    level_options = ["0", "1", "2", "3a", "3b", "4", "5", "その他"]
    level = st.selectbox("選択してください",level_options, index=1,)
    
    with st.expander("レベル定義を確認する 📖"):
            # tableを使うとレイアウトが整う
            st.subheader("インシデント")
            incident_df = pd.DataFrame({
                'レベル': ['0', '1', '2'],
                '説明': [
                    "間違ったことが実施される前に気づいた場合。",
                    "間違ったことが実施されたが、患者様かつ職員には影響・変化がなかった場合。",
                    "間違ったことが実施されたが、患者様かつ職員に処置や治療を行う必要はなかった。（患者観察の強化など）"
                ]
            }).set_index('レベル')
            st.dataframe(
        incident_df,
        use_container_width=True, # テーブルをコンテナの幅いっぱいに広げる
        column_config={
            "説明": st.column_config.TextColumn(
                "説明", # ヘッダー名
                width="large", # 列の幅を "small", "medium", "large" から選べる
            )
        }
    )

            st.subheader("アクシデント")
            accident_df = pd.DataFrame({
                'レベル': ['3a', '3b', '4', '5'],
                '説明': [
                    "事故により、簡単な処置や治療を要した。（消毒、湿布、鎮痛剤の投与など）",
                    "事故により、濃厚な処置や治療を要した。（骨折、手術、入院日数の延長など）",
                    "事故により、永続的な障害や後遺症が残った。",
                    "事故が死因になった。"
                ]
            }).set_index('レベル')
            st.dataframe(
        accident_df,
        use_container_width=True,
        column_config={
            "説明": st.column_config.TextColumn("説明", width="large")
        }
    )

            st.subheader("その他")
            st.markdown("- 盗難、自殺、災害、クレーム、発注ミス、個人情報流出、針刺し事故など")
            
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        # --- 発生日時セクション ---
        st.write("**発生日時**") # 共通の見出し
        sub_col1, sub_col2 = st.columns([2, 1]) # 横に並べるための内部列
        with sub_col1:
            occurrence_date = st.date_input("発生日", label_visibility="collapsed")
        with sub_col2:
            occurrence_time = st.time_input("発生時刻", label_visibility="collapsed")
            
        # --- 報告者セクション ---
        st.write("**報告者**")
        # 報告者用に「新しく」列を作成
        reporter_col1, reporter_col2 = st.columns([2, 1]) # 比率はお好みで [3, 2] などに変更可能
        with reporter_col1:
            reporter_name = st.text_input("報告者氏名", label_visibility="collapsed", placeholder="氏名を入力")
        with reporter_col2:
            job_type = st.selectbox("職種",
                            ["Dr", "Ns", "PT", "At", "RT", "その他"],
                            label_visibility="collapsed")
            
        # --- 事故との関連性 ---
        st.write("**事故との関連性**")

        # 複数選択を可能にする st.multiselect
        connection_with_accident = st.multiselect(
            "関連性をすべて選択してください",  # このラベルが不要なら label_visibility="collapsed" を追加
            options=["当事者", "発見者", "患者本人より訴え", "患者家族より訴え"],
            default=[],
            label_visibility="collapsed")
        
        # --- 総実務経験 ---
        st.write("**総実務経験**")
        location = st.selectbox("総実務経験", 
                                ["1年未満", "1～3年未満", "3～5年未満", "5～10年未満", "10年以上"],
                                label_visibility="collapsed")
        
        # --- 入職年数 ---
        st.write("**入職年数**")
        location = st.selectbox("入職年数", 
                                ["1年未満", "1～3年未満", "3～5年未満", "5～10年未満", "10年以上"],
                                label_visibility="collapsed")
        
    with col2:
        
        # --- 患者情報 ---
        st.write("**患者情報**")
        patient_col1, patient_col2 = st.columns([1, 2])
        with patient_col1:
            patient_ID = st.text_input("患者ID", label_visibility="collapsed", placeholder="IDを入力")
        with patient_col2:
            patient_name = st.text_input("患者氏名", label_visibility="collapsed", placeholder="氏名を入力")
        
        # --- 発生場所 ---
        st.write("**発生場所**")
        location = st.selectbox("発生場所",
                                ["1FMRI室", "1F操作室", "1F撮影室", "1Fエコー室", "1F廊下", "1Fトイレ",
                                    "2F受付", "2F待合", "2F診察室", "2F処置室", "2Fトイレ",
                                    "3Fリハビリ室", "3F受付", "3F待合","3Fトイレ",
                                    "4Fリハビリ室", "4F受付", "4F待合","4Fトイレ"],
            label_visibility="collapsed")
        

    st.markdown("---")
    
    # ▼▼▼ 状況と対策（自由記述）▼▼▼
    st.subheader("状況と対策")
    situation = st.text_area("発生の状況と直後の対応（詳細に記入）")
    countermeasure = st.text_area("今後の対策（箇条書きで記入）")
    
    st.markdown("---")
        
    # --- 詳細情報（ここからが追加・変更部分） ---
    st.subheader("インシデントの詳細")

    # ▼▼▼ 内容 ▼▼▼
    with st.expander("内容（関連する箇所にチェック）", expanded=True):
        # 大分類
        content_category = st.radio(
            "大分類を選択してください",
            ["診察・リハビリ", "転倒・転落", "薬剤", "検査・処置", "放射線", "リハビリ", "ME機器", "コミュニケーション", "その他"]
        )
        
        content_details = []
        content_other_text = ""

        # 大分類に応じた詳細項目を表示
        if content_category == "診察・リハビリ":
            content_details = st.multiselect("詳細", ["患者間違い", "予約日時の間違い", "予約漏れ", "検査の種類間違い", "その他"])
            if "その他" in content_details:
                content_other_text = st.text_input("その他（内容を具体的に）", key="content_shinsatsu_other")
        
        elif content_category == "転倒・転落":
            content_details = st.multiselect("詳細", ["転倒", "転落", "滑落"])
            st.write("⇒ 転倒・転落後の状態")
            injury_details = st.multiselect("外傷の有無など", ["外傷なし", "擦過傷", "表皮剥離", "打撲", "骨折", "その他"])
            if "その他" in injury_details:
                injury_other_text = st.text_input("その他（外傷の詳細）", key="content_tentou_other")

        elif content_category == "薬剤":
            content_details = st.multiselect("詳細", ["注射・点滴", "内服", "外用薬", "その他"])
            st.write("⇒ 薬剤ミスの内容")
            med_error_details = st.multiselect("エラー詳細", ["患者間違い", "薬剤間違い", "投与方法", "未投与", "投与量", "投与時間", "投与速度", "その他"])
            if "その他" in med_error_details:
                med_error_other_text = st.text_input("その他（エラー詳細）", key="content_yakuzai_other")
        
        # (同様に他のカテゴリも追加できます)
        # ... 検査・処置, 放射線, ME機器 など ...

    # ▼▼▼ 発生・発見の原因 ▼▼▼
    with st.expander("発生・発見の原因（複数選択可）", expanded=True):
        cause_options = {
            "不適切な指示": ["口頭指示", "検査伝票・指示ラベル・処方箋の誤記", "その他"],
            "無確認": ["検査伝票・指示ラベル・処方箋で確認せず", "思い込み・勘違い", "疑問に思ったが確認せず", "ダブルチェックせず", "正しい確認方法を知らなかった", "機器・器具の操作方法を確認しなかった", "患者情報を確認しなかった", "その他"],
            "指示の見落としなど": ["指示の見落とし", "指示の見誤り", "その他"],
            "患者観察の不足": ["処置・検査・手技中または直前直後における観察不足", "投薬中または直前直後における観察不足"],
            "説明・知識・経験の不足": ["説明不足", "業務に対する知識不足", "業務に対する技術不足"],
            "偶発症・災害": ["偶発症", "不可抗力（患者に関する発見）", "不可抗力（施設設備等に関する発見・災害被害等）"]
        }
        
        selected_causes = {}
        for category, options in cause_options.items():
            selected_causes[category] = st.multiselect(category, options)
            # 各カテゴリで「その他」が選ばれたら入力欄を表示
            if "その他" in selected_causes[category]:
                st.text_input(f"【{category}】その他の詳細", key=f"cause_{category}_other")
    
    # ▼▼▼ マニュアルとの関連 ▼▼▼
    with st.expander("マニュアルとの関連", expanded=True):
        manual_relation = st.radio(
            "手順に対して",
            ["手順に従っていた", "手順に従っていなかった", "手順がなかった", "不慣れ・不手際"]
        )
    
    # --- フォームの送信ボタン ---
    submit_button = st.form_submit_button(label='この内容で報告する')

# --- データ保存処理 ---
if submit_button:
    if not reporter_name or not situation or not countermeasure:
        # エラーメッセージをリストで管理
        error_messages = []
        if not reporter_name:
            error_messages.append("報告者氏名")
        if not situation:
            error_messages.append("発生の状況と直後の対応")
        if not countermeasure:
            error_messages.append("今後の対策")
        
        # st.error() で入力が必須であることをユーザーに伝える
        st.error(f"以下の必須項目を入力してください: {', '.join(error_messages)}")
    else:
        # この else ブロックの中に、今までのDB保存処理をすべて移動する
        from db_utils import add_report
        # 発生日時を結合
        occurrence_datetime = datetime.datetime.combine(occurrence_date, occurrence_time)
        
        # 選択された詳細項目を文字列に変換
        connection_str = ", ".join(connection_with_accident)
        # (他の multiselect 項目も同様に文字列に変換)
        
        # 2. インシデント内容 (multiselect)
        #    ※ご自身のコードに合わせて変数名を調整してください
        #    例: content_details がリストの場合
        content_details_str = ", ".join(content_details if isinstance(content_details, list) else [])
        if 'content_other_text' in locals() and content_other_text:
            content_details_str += f", その他: {content_other_text}"

        # 3. 発生原因 (複数のmultiselect)
        #    ※ご自身のコードに合わせて変数名を調整してください
        cause_list = []
        if 'selected_causes' in locals() and isinstance(selected_causes, dict):
            for category, items in selected_causes.items():
                if items:
                    cause_list.append(f"{category}: {', '.join(items)}")
        cause_summary_str = " | ".join(cause_list)
        
        # データベースに保存するデータを辞書としてまとめる
        # ※キーの名前は db_utils.py のテーブル定義と一致させる
        new_data = {
            "occurrence_datetime": occurrence_datetime,
            "reporter_name": reporter_name,
            "job_type": job_type,
            "level": level,
            "location": location,
            "connection_with_accident": connection_str,
            "content_details": "...", # ここにはインシデント内容の文字列を入れる
            "cause_details": "...",   # ここには発生原因の文字列を入れる
            "manual_relation": "...", # ここにはマニュアル関連の選択結果を入れる
            "situation": situation,
            "countermeasure": countermeasure
        }
        
        # データベースに追加
        add_report(new_data)
        
        st.success("報告がデータベースに保存されました。")
        
        # (2) session_stateに 'data_version' がなければ初期化
        if 'data_version' not in st.session_state:
            st.session_state.data_version = 0
        # (3) バージョン番号を1つ上げる
        st.session_state.data_version += 1
        
        st.balloons()