import streamlit as st
import pandas as pd
import datetime
import json
from db_utils import add_report, add_draft, delete_draft, DateTimeEncoder # 必要な関数をインポート

# --- 認証チェック ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/0_Login.py")

st.set_page_config(page_title="新規報告", page_icon="✍️", layout="wide")

# --- 1. データとセッションステートの準備 --- 

# --- デフォルト値の定義 ---
defaults = {
    'level': "1",
    'occurrence_date': datetime.date.today(),
    'occurrence_time': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).time(),
    'reporter_name': "",
    'job_type': "Dr",
    'connection_with_accident': [],
    'years_of_experience': "1年未満",
    'years_since_joining': "1年未満",
    'patient_ID': "",
    'patient_name': "",
    'patient_gender': "",
    'patient_age': None,
    'dementia_status': "",
    'patient_status_change_accident': "無",
    'patient_status_change_patient_explanation': "無",
    'patient_status_change_family_explanation': "無",
    'location': "1FMRI室",
    'situation': "",
    'countermeasure': "",
    'content_category': "診察",
    'content_details_shinsatsu': [],
    'content_details_shochi': [],
    'content_details_uketsuke': [],
    'content_details_houshasen': [],
    'content_details_rehabili': [],
    'content_details_tentou': [],
    'content_details_kanjataio': [],
    'content_details_kiki': [],
    'content_details_sonota': [],
    'injury_details': [],
    'injury_other_text': "",
    'cause_不適切な指示': [],
    'cause_不適切な指示_other': "",
    'cause_無確認': [],
    'cause_無確認_other': "",
    'cause_指示の見落としなど': [],
    'cause_指示の見落としなど_other': "",
    'cause_患者観察の不足': [],
    'cause_患者観察の不足_other': "",
    'cause_説明・知識・経験の不足': [],
    'cause_説明・知識・経験の不足_other': "",
    'cause_偶発症・災害': [],
    'cause_偶発症・災害_other': "",
    'manual_relation': "手順に従っていた"
}

# --- 原因選択肢の定義 ---
cause_options = {
    "不適切な指示": ["口頭指示", "検査伝票・指示ラベル・処方箋の誤記", "その他"],
    "無確認": ["検査伝票・指示ラベル・処方箋で確認せず", "思い込み・勘違い", "疑問に思ったが確認せず", "ダブルチェックせず", "正しい確認方法を知らなかった", "機器・器具の操作方法を確認しなかった", "患者情報を確認しなかった", "その他"],
    "指示の見落としなど": ["指示の見落とし", "指示の見誤り", "その他"],
    "患者観察の不足": ["処置・検査・手技中または直前直後における観察不足", "投薬中または直前直後における観察不足"],
    "説明・知識・経験の不足": ["説明不足", "業務に対する知識不足", "業務に対する技術不足"],
    "偶発症・災害": ["偶発症", "不可抗力（患者に関する発見）", "不可抗力（施設設備等に関する発見・災害被害等）"],
    "発生時の状況": ["多忙であった", "時間に追われていた", "疲弊していた", "集中できる環境ではなかった", "人員不足"]
}

# --- セッションステートの初期化関数 ---
def init_session_state():
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    # ログインユーザー名を報告者名のデフォルト値に設定
    if 'reporter_name' not in st.session_state or not st.session_state.reporter_name:
        st.session_state.reporter_name = st.session_state.get("username", "")

# --- 下書き読み込み処理 (ウィジェット表示前に実行) ---
if "loaded_draft" in st.session_state:
    draft_data = st.session_state.loaded_draft
    for k, v in draft_data.items():
        if k == 'occurrence_date' and v:
            st.session_state[k] = datetime.date.fromisoformat(v)
        elif k == 'occurrence_time' and v:
            st.session_state[k] = datetime.time.fromisoformat(v)
        else:
            st.session_state[k] = v
    del st.session_state["loaded_draft"]
    st.session_state.draft_loaded_message = True

# --- セッションステートの初期化を実行 ---
init_session_state()

# --- カテゴリ変更時の詳細項目クリアロジック ---
if 'prev_content_category' not in st.session_state:
    st.session_state.prev_content_category = st.session_state.content_category
elif st.session_state.prev_content_category != st.session_state.content_category:
    for key in list(st.session_state.keys()):
        if key.startswith("content_details_"):
            st.session_state[key] = []
    st.session_state.injury_details = []
    st.session_state.injury_other_text = ""
    st.session_state.prev_content_category = st.session_state.content_category

# --- 2. ページUIの表示 --- 

# --- メッセージ表示エリア ---
if st.session_state.get("report_submitted"):
    st.success("報告がデータベースに保存されました。")
    st.balloons()
    del st.session_state.report_submitted

if st.session_state.get("draft_loaded_message"):
    st.success("下書きを読み込みました。")
    del st.session_state.draft_loaded_message

st.title("✍️ 新規報告フォーム")
st.markdown("--- ")

# --- 大分類の選択 ---
st.subheader("1. インシデントの大分類を選択してください")
content_category = st.radio(
    "大分類", 
    ["診察", "処置", "受付", "放射線業務", "リハビリ業務", "転倒・転落", "患者対応", "機器関連", "その他"],
    key="content_category",
    horizontal=True,
    label_visibility="collapsed"
)
st.markdown("--- ")

# --- フォーム --- 
with st.form(key='report_form', clear_on_submit=False):
    st.subheader("2. 詳細を入力してください")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- 基本情報 ---
    st.subheader("基本情報")
    level_options = ["0", "1", "2", "3a", "3b", "4", "5", "その他"]
    level = st.selectbox("影響度レベル", level_options, key='level')
    
    with st.expander("レベル定義の確認"):
        st.subheader("インシデント")
        incident_df = pd.DataFrame({
            'レベル': ['0', '1', '2'],
            '説明': [
                "間違ったことが実施される前に気づいた場合。",
                "間違ったことが実施されたが、患者様かつ職員には影響・変化がなかった場合。",
                "間違ったことが実施されたが、患者様かつ職員に処置や治療を行う必要はなかった。（患者観察の強化など）"
            ]
        }).set_index('レベル')
        st.dataframe(incident_df, use_container_width=True, column_config={"説明": st.column_config.TextColumn("説明", width="large")})

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
        st.dataframe(accident_df, use_container_width=True, column_config={"説明": st.column_config.TextColumn("説明", width="large")})

        st.subheader("その他")
        st.markdown("- 盗難、自殺、災害、クレーム、発注ミス、個人情報流出、針刺し事故など")

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
        col_family_radio.radio(" ", ["有", "無"], key="patient_status_change_family_explanation", horizontal=True, label_visibility="collapsed")

    st.markdown("--- ")
    st.subheader("状況と対策")
    st.text_area("発生の状況と直後の対応（詳細に記入）", key="situation")
    st.text_area("今後の対策（箇条書きで記入）", key="countermeasure")
    
    st.markdown("--- ")
    st.subheader("インシデントの詳細")
    st.markdown(f"<h3 style='margin-bottom: 0;'>選択中の大分類: <span style='color: #3498db;'>{st.session_state.content_category}</span></h3>", unsafe_allow_html=True)

    with st.expander("内容（関連する箇所にチェック）", expanded=True):
        # 各カテゴリの詳細入力（キーをsession_stateと一致させる）
        if st.session_state.content_category == "診察":
            st.multiselect("詳細", ["患者間違い", "オーダー間違い", "予約間違い", "案内間違い", "紛失", "カルテ記載間違い", "伝達漏れ", "返却忘れ", "確認漏れ", "情報漏洩", "未処置帰宅"], key="content_details_shinsatsu")
        elif st.session_state.content_category == "処置":
            st.multiselect("詳細", ["患者間違い", "部位間違い", "案内間違い", "カルテ記載間違い", "確認漏れ", "伝達漏れ", "ラベル間違い", "針刺し事故", "検体採り間違い", "不適切な前処置", "未処置帰宅", "薬液間違い"], key="content_details_shochi")
        elif st.session_state.content_category == "受付":
            st.multiselect("詳細", ["患者間違い", "予約間違い", "案内間違い", "紛失", "カルテ記載間違い", "伝達漏れ", "返却忘れ", "確認漏れ", "情報漏洩", "会計間違い", "郵送関係"], key="content_details_uketsuke")
        elif st.session_state.content_category == "放射線業務":
            st.multiselect("詳細", ["患者間違い", "機器登録間違い", "マーカー間違い", "骨密度解析間違い", "MRI室金属持ち込み", "画像転送忘れ", "左右間違い", "案内間違い", "紛失", "カルテ記載間違い", "伝達間違い", "返却忘れ", "確認漏れ", "情報漏洩", "MRI完全吸着", "技師コメント間違い", "装置故障"], key="content_details_houshasen")
        elif st.session_state.content_category == "リハビリ業務":
            st.multiselect("詳細", ["患者間違い", "部位間違い", "評価ミス", "計画書関連", "リハビリ処方による受傷", "リハビリ中の軽微な事故", "オーダー間違い", "予約間違い", "案内間違い", "紛失", "カルテ記載間違い", "伝達間違い", "返却忘れ", "確認漏れ", "情報漏洩"], key="content_details_rehabili")
        elif st.session_state.content_category == "転倒・転落":
            st.multiselect("詳細", ["転倒", "転落", "滑落"], key="content_details_tentou")
            st.multiselect("外傷の有無など", ["外傷なし", "擦過傷", "表皮剥離", "打撲", "骨折", "その他"], key="injury_details")
            if "その他" in st.session_state.injury_details:
                st.text_input("その他（外傷の詳細）", key="injury_other_text")
        elif st.session_state.content_category == "患者対応":
            st.multiselect("詳細", ["接遇に対する不満", "検査・治療に対する不満", "医療費に対する不満", "待ち時間に対する不満", "設備・環境に対する不満", "電話対応に対する不満", "患者間のトラブル"], key="content_details_kanjataio")
        elif st.session_state.content_category == "機器関連":
            st.multiselect("詳細", ["破損", "故障", "不具合", "操作ミス"], key="content_details_kiki")
        elif st.session_state.content_category == "その他":
            st.multiselect("詳細", ["盗難", "紛失", "在庫不足", "発注ミス", "不審者", "施錠忘れ", "災害"], key="content_details_sonota")

    with st.expander("発生・発見の原因（複数選択可）", expanded=True):
        for category, options in cause_options.items():
            st.multiselect(category, options, key=f"cause_{category}")
            if "その他" in st.session_state[f"cause_{category}"]:
                st.text_input(f"【{category}】その他の詳細", key=f"cause_{category}_other")
    
    with st.expander("マニュアルとの関連", expanded=True):
        st.radio("手順に対して", ["手順に従っていた", "手順に従っていなかった", "手順がなかった", "不慣れ・不手際"], key="manual_relation")
    
    

    st.markdown("--- ")
    submit_col, draft_col = st.columns([1, 1])
    submit_button = submit_col.form_submit_button(label='✅ この内容で報告する', use_container_width=True,)
    draft_button = draft_col.form_submit_button(label='📝 下書き保存', use_container_width=True,)
if draft_button:
    draft_title = f"下書き - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    draft_data = {k: v for k, v in st.session_state.items() if k not in ['loaded_draft', 'FormSubmitter'] and not k.startswith('FormSubmitter')}
    add_draft(draft_title, json.dumps(draft_data, cls=DateTimeEncoder, ensure_ascii=False))
    st.success(f"「{draft_title}」を下書きとして保存しました。下書き管理ページから再開できます。")

if submit_button:
    if not st.session_state.reporter_name or not st.session_state.situation or not st.session_state.countermeasure:
        st.error("報告者氏名、発生の状況、今後の対策は必須項目です。")
    else:
        content_details_list = []
        if st.session_state.content_category == "診察":
            content_details_list.extend(st.session_state.content_details_shinsatsu)
        elif st.session_state.content_category == "処置":
            content_details_list.extend(st.session_state.content_details_shochi)
        elif st.session_state.content_category == "受付":
            content_details_list.extend(st.session_state.content_details_uketsuke)
        elif st.session_state.content_category == "放射線業務":
            content_details_list.extend(st.session_state.content_details_houshasen)
        elif st.session_state.content_category == "リハビリ業務":
            content_details_list.extend(st.session_state.content_details_rehabili)
        elif st.session_state.content_category == "転倒・転落":
            content_details_list.extend(st.session_state.content_details_tentou)
            if st.session_state.injury_details:
                injury_str = f"(外傷: {', '.join(st.session_state.injury_details)})"
                if st.session_state.get('injury_other_text'):
                    injury_str += f" その他: {st.session_state.injury_other_text}"
                content_details_list.append(injury_str)
        elif st.session_state.content_category == "患者対応":
            content_details_list.extend(st.session_state.content_details_kanjataio)
        elif st.session_state.content_category == "機器関連":
            content_details_list.extend(st.session_state.content_details_kiki)
        elif st.session_state.content_category == "その他":
            content_details_list.extend(st.session_state.content_details_sonota)
        content_details_str = ", ".join(content_details_list)

        cause_list = []
        for category, options in cause_options.items():
            items = st.session_state.get(f"cause_{category}", [])
            if items:
                item_str = f"{category}: {', '.join(items)}"
                if "その他" in items and st.session_state.get(f"cause_{category}_other"):
                    item_str += f" ({st.session_state[f'cause_{category}_other']})"
                cause_list.append(item_str)
        cause_summary_str = " | ".join(cause_list)

        new_data = {
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
            "content_category": st.session_state.content_category,
            "content_details": content_details_str,
            "content_details_shinsatsu": st.session_state.content_details_shinsatsu,
            "content_details_shochi": st.session_state.content_details_shochi,
            "content_details_uketsuke": st.session_state.content_details_uketsuke,
            "content_details_houshasen": st.session_state.content_details_houshasen,
            "content_details_rehabili": st.session_state.content_details_rehabili,
            "content_details_kanjataio": st.session_state.content_details_kanjataio,
            "content_details_kiki": st.session_state.content_details_kiki,
            "content_details_sonota": st.session_state.content_details_sonota,
            "injury_details": st.session_state.injury_details,
            "injury_other_text": st.session_state.injury_other_text,
            "cause_details": cause_summary_str,
            "manual_relation": st.session_state.manual_relation,
            "situation": st.session_state.situation,
            "countermeasure": st.session_state.countermeasure
        }
        
        add_report(new_data)

        if st.session_state.get('loaded_draft_id'):
            delete_draft(st.session_state.loaded_draft_id)
            del st.session_state['loaded_draft_id']

        for key in defaults.keys():
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state.report_submitted = True
        st.rerun()
