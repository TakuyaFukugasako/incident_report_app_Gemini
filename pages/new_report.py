import streamlit as st
import pandas as pd
import datetime
from db_utils import (
    add_report, save_draft, get_user_drafts, load_draft, delete_draft
)

st.set_page_config(page_title="新規報告", page_icon="📝")
st.title("📝 新規報告フォーム")

# === ユーザー認証（将来の機能）のための仮ユーザー ===
CURRENT_USER = "default_user"

# === session_stateの初期化関数 ===
def initialize_form_state():
    """フォームの値を初期化する"""
    # フォームのキーをリストで管理
    form_keys = [
        'level', 'occurrence_date', 'occurrence_time', 'reporter_name', 'job_type',
        'connection_with_accident', 'total_experience', 'years_at_current_job',
        'patient_ID', 'patient_name', 'location', 'situation', 'countermeasure',
        'content_category', 'content_details', 'injury_details', 'med_error_details',
        'manual_relation'
    ]
    # 原因のキーも追加
    cause_categories = ["不適切な指示", "無確認", "指示の見落としなど", "患者観察の不足", "説明・知識・経験の不足", "偶発症・災害"]
    for cat in cause_categories:
        form_keys.append(f"cause_{cat}")
    
    for key in form_keys:
        st.session_state[key] = None if key not in ['occurrence_date', 'occurrence_time'] else datetime.date.today()
    st.session_state.occurrence_time = datetime.datetime.now().time()
    st.session_state.loaded_draft_id = None
    st.session_state.draft_name = ""


# === 下書き読み込み機能 ===
st.subheader("下書きから再開する")
col_draft1, col_draft2 = st.columns([3, 1])

with col_draft1:
    drafts_df = get_user_drafts(CURRENT_USER)
    draft_options = {row['id']: f"{row['draft_name']} (最終保存: {row['last_saved_at']})" for index, row in drafts_df.iterrows()}
    draft_options[0] = "--- 新規作成 ---"
    
    selected_draft_id = st.selectbox(
        "保存した下書きを選択",
        options=list(draft_options.keys()),
        format_func=lambda x: draft_options[x],
        index=0,
        key="draft_selector"
    )

with col_draft2:
    st.write("　") # スペース調整
    if st.button("この下書きを読み込む"):
        if selected_draft_id != 0:
            draft_data = load_draft(selected_draft_id, CURRENT_USER)
            if draft_data:
                initialize_form_state() # 一旦リセット
                for key, value in draft_data.items():
                    # DBから読み込んだ値をsession_stateにセット
                    if value is not None:
                        # 日時は特別扱い
                        if key == 'occurrence_datetime':
                            dt = pd.to_datetime(value)
                            st.session_state.occurrence_date = dt.date()
                            st.session_state.occurrence_time = dt.time()
                        # 複数選択項目は文字列からリストに変換
                        elif key in ['connection_with_accident', 'content_details', 'injury_details', 'med_error_details'] or key.startswith('cause_'):
                            st.session_state[key] = [item.strip() for item in value.split(',')] if value else []
                        else:
                            st.session_state[key] = value
                st.session_state.loaded_draft_id = selected_draft_id
                st.success(f"下書き「{draft_data['draft_name']}」を読み込みました。")
        else:
            initialize_form_state() # 新規作成を選んだらフォームをクリア
            st.info("フォームを初期化しました。")


st.markdown("---")

# === 一時保存機能 ===
st.subheader("内容の一時保存")
draft_name_input = st.text_input("下書きの名称（必須）", key='draft_name')
if st.button("現在の内容を一時保存する"):
    if not st.session_state.draft_name:
        st.warning("一時保存するには「下書きの名称」を入力してください。")
    else:
        # 全ての入力ウィジェットの値をsession_stateから集める
        draft_data_to_save = {}
        form_keys_for_save = [
            'level', 'reporter_name', 'job_type', 'total_experience', 'years_at_current_job',
            'patient_ID', 'patient_name', 'location', 'situation', 'countermeasure', 'manual_relation'
        ]
        for key in form_keys_for_save:
            draft_data_to_save[key] = st.session_state.get(key)
        
        # 複数選択項目を文字列に変換
        draft_data_to_save['connection_with_accident'] = ", ".join(st.session_state.get('connection_with_accident', []))
        
        # 日時を結合
        if st.session_state.get('occurrence_date') and st.session_state.get('occurrence_time'):
            draft_data_to_save['occurrence_datetime'] = datetime.datetime.combine(st.session_state.occurrence_date, st.session_state.occurrence_time)
        
        # 動的な詳細項目
        content_cat = st.session_state.get('content_category')
        content_details_str = ""
        if content_cat == "診察・リハビリ": content_details_str = ", ".join(st.session_state.get('content_shinsatsu_details', []))
        elif content_cat == "転倒・転落": content_details_str = ", ".join(st.session_state.get('content_tentou_details', []))
        elif content_cat == "薬剤": content_details_str = ", ".join(st.session_state.get('content_yakuzai_details', []))
        draft_data_to_save['content_details'] = content_details_str
        
        # 原因
        cause_list = []
        cause_categories = ["不適切な指示", "無確認", "指示の見落としなど", "患者観察の不足", "説明・知識・経験の不足", "偶発症・災害"]
        for cat in cause_categories:
            items = st.session_state.get(f"cause_{cat}", [])
            if items:
                cause_list.append(f"{cat}: {', '.join(items)}")
        draft_data_to_save['cause_details'] = " | ".join(cause_list)

        # 下書き名と、更新の場合はIDも追加
        draft_data_to_save['draft_name'] = st.session_state.draft_name
        if st.session_state.get('loaded_draft_id'):
            draft_data_to_save['id'] = st.session_state.loaded_draft_id
        
        save_draft(CURRENT_USER, draft_data_to_save)
        st.success(f"下書き「{st.session_state.draft_name}」を保存しました。")
        st.cache_data.clear() # キャッシュをクリアして下書きリストを更新
        st.rerun() # ページをリロードしてUIを最新に保つ

st.markdown("---")

# === 本番の入力フォーム ===
with st.form(key='report_form'):
    st.subheader("インシデント報告内容")

    level_options = ["0", "1", "2", "3a", "3b", "4", "5", "その他"]
    st.selectbox("影響度レベル", level_options, key="level", index=level_options.index(st.session_state.level) if st.session_state.get("level") in level_options else 0)
    
    # (expander部分は変更なし) ...
    with st.expander("レベル定義を確認する 📖"):
        pass # 省略。元のコードをここに配置

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**発生日時**")
        c1, c2 = st.columns([2, 1])
        c1.date_input("発生日", key="occurrence_date", label_visibility="collapsed")
        c2.time_input("発生時刻", key="occurrence_time", label_visibility="collapsed")
        
        st.write("**報告者**")
        c1, c2 = st.columns([2, 1])
        c1.text_input("氏名", key="reporter_name", placeholder="氏名を入力", label_visibility="collapsed")
        c2.selectbox("職種", ["Dr", "Ns", "PT", "At", "RT", "その他"], key="job_type", label_visibility="collapsed")
            
        st.write("**事故との関連性**")
        st.multiselect("関連性", ["当事者", "発見者", "患者本人より訴え", "患者家族より訴え"], key="connection_with_accident", label_visibility="collapsed")
        
        st.write("**総実務経験**")
        st.selectbox("総実務経験", ["1年未満", "1～3年未満", "3～5年未満", "5～10年未満", "10年以上"], key="total_experience", label_visibility="collapsed")
        
        st.write("**入職年数**")
        st.selectbox("入職年数", ["1年未満", "1～3年未満", "3～5年未満", "5～10年未満", "10年以上"], key="years_at_current_job", label_visibility="collapsed")
        
    with col2:
        st.write("**患者情報**")
        c1, c2 = st.columns([1, 2])
        c1.text_input("患者ID", key="patient_ID", placeholder="IDを入力", label_visibility="collapsed")
        c2.text_input("患者氏名", key="patient_name", placeholder="氏名を入力", label_visibility="collapsed")
        
        st.write("**発生場所**")
        st.selectbox("発生場所", ["1FMRI室", "1F操作室", ...], key="location", label_visibility="collapsed") # 選択肢は省略

    st.markdown("---")
    
    st.subheader("状況と対策")
    st.text_area("発生の状況と直後の対応（詳細に記入）", key="situation")
    st.text_area("今後の対策（箇条書きで記入）", key="countermeasure")
    
    st.markdown("---")

    st.subheader("インシデントの詳細")
    # ▼▼▼ 内容 ▼▼▼
    with st.expander("内容（関連する箇所にチェック）", expanded=True):
        # 大分類のラジオボタン。選択肢は session_state.content_category に保存される
        st.radio(
            "大分類を選択してください",
            ["診察・リハビリ", "転倒・転落", "薬剤", "検査・処置", "放射線", "リハビリ", "ME機器", "コミュニケーション", "その他"],
            key="content_category" # keyを設定してsession_stateで管理
        )
        
        # --- 大分類に応じた詳細項目を表示 ---
        # st.session_state.content_category の現在の値に応じて表示を切り替える
        category = st.session_state.get('content_category')

        if category == "診察・リハビリ":
            st.multiselect("詳細", ["患者間違い", "予約日時の間違い", "予約漏れ", "検査の種類間違い", "その他"], key="content_details_shinsatsu")
            if "その他" in st.session_state.get('content_details_shinsatsu', []):
                st.text_input("その他（内容を具体的に）", key="content_shinsatsu_other")
        
        elif category == "転倒・転落":
            st.multiselect("詳細", ["転倒", "転落", "滑落"], key="content_details_tentou")
            st.write("⇒ 転倒・転落後の状態")
            st.multiselect("外傷の有無など", ["外傷なし", "擦過傷", "表皮剥離", "打撲", "骨折", "その他"], key="injury_details")
            if "その他" in st.session_state.get('injury_details', []):
                st.text_input("その他（外傷の詳細）", key="injury_details_other")

        elif category == "薬剤":
            st.multiselect("詳細", ["注射・点滴", "内服", "外用薬", "その他"], key="content_details_yakuzai")
            st.write("⇒ 薬剤ミスの内容")
            st.multiselect("エラー詳細", ["患者間違い", "薬剤間違い", "投与方法", "未投与", "投与量", "投与時間", "投与速度", "その他"], key="med_error_details")
            if "その他" in st.session_state.get('med_error_details', []):
                st.text_input("その他（エラー詳細）", key="med_error_details_other")
        
        # (同様に他のカテゴリも、それぞれユニークなkeyを設定して追加します)
        # elif category == "検査・処置":
        #     st.multiselect("詳細", [...], key="content_details_kensa")
        # ...

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
        
        for category, options in cause_options.items():
            # keyはカテゴリ名から生成（例: cause_不適切な指示）
            key_name = f"cause_{category}"
            st.multiselect(category, options, key=key_name)
            # 「その他」の入力欄も、対応するキーを設定
            if "その他" in st.session_state.get(key_name, []):
                st.text_input(f"【{category}】その他の詳細", key=f"{key_name}_other")
    
    # ▼▼▼ マニュアルとの関連 ▼▼▼
    with st.expander("マニュアルとの関連", expanded=True):
        st.radio(
            "手順に対して",
            ["手順に従っていた", "手順に従っていなかった", "手順がなかった", "不慣れ・不手際"],
            key="manual_relation" # keyを設定
        )
    
    # --- フォームの送信ボタン ---
    submit_button = st.form_submit_button(label='この内容で報告する')

# === 報告完了処理 ===
if submit_button:
    # バリデーション
    if not st.session_state.get('reporter_name') or not st.session_state.get('situation') or not st.session_state.get('countermeasure'):
        st.error("必須項目（報告者氏名, 状況, 対策）を入力してください。")
    else:
        # 下書き保存と同じロジックでデータを収集
        report_data = {}
        # ... (一時保存のロジックを参考に、report_data辞書を作成)
        
        add_report(report_data)
        
        # 下書きから作成した場合、その下書きを削除
        if st.session_state.get('loaded_draft_id'):
            delete_draft(st.session_state.loaded_draft_id, CURRENT_USER)
        
        initialize_form_state() # フォームをクリア
        st.success("報告が完了しました。")
        st.cache_data.clear() # 全てのキャッシュをクリア
        if 'data_version' not in st.session_state: st.session_state.data_version = 0
        st.session_state.data_version += 1
        st.balloons()