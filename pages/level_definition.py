import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="レベル定義", page_icon="📖")

st.title("📖 影響度レベル定義")
st.markdown("---")
st.write("インシデント・アクシデント報告における影響度レベルの定義は以下の通りです。")

# --- インシデント ---
st.subheader("インシデント")
incident_data = {
    'レベル': ['0', '1', '2'],
    '説明': [
        "間違ったことが実施される前に気づいた場合。",
        "間違ったことが実施されたが、患者様かつ職員には影響・変化がなかった場合。",
        "間違ったことが実施されたが、患者様かつ職員に処置や治療を行う必要はなかった。（患者観察の強化、採血やレントゲン検査などの必要性は生じた）"
    ]
}
incident_df = pd.DataFrame(incident_data)
# .set_index('レベル') でレベル列を一番左のインデックスにすると見やすくなります
st.table(incident_df.set_index('レベル'))

# --- アクシデント ---
st.subheader("アクシデント")
accident_data = {
    'レベル': ['3a', '3b', '4', '5'],
    '説明': [
        "事故により、患者様もしくは職員に簡単な処置や治療を要した。（消毒、湿布、皮膚縫合、鎮痛剤の投与など）",
        "事故により、患者様もしくは職員に濃厚な処置や治療を要した。（人工呼吸器の装着、骨折、手術、入院日数の延長、外来患者の入院など。）",
        "事故により、永続的な障害や後遺症が残った。",
        "事故が死因になった。"
    ]
}
accident_df = pd.DataFrame(accident_data)
st.table(accident_df.set_index('レベル'))

# --- その他 ---
st.subheader("その他")
st.markdown("""
- **盗難、自殺、災害、クレーム、発注ミス、個人情報流出、針刺し事故など**
""")

st.info("報告の際は、最も適切なレベルを選択してください。")

st.markdown("---") # 区切り線

# ▼▼▼ ここからが追加部分 ▼▼▼
st.write("### 内容を確認したら、下のボタンで報告フォームに戻ってください。")

# ボタンを中央に配置するための工夫
col1, col2, col3 = st.columns([1, 2, 1]) # 左右に空の列を作り、中央の列を大きくする
with col2:
    # use_container_width=True でボタンを列の幅いっぱいに広げる
    if st.button("報告フォームに戻る", type="primary", use_container_width=True):
        # st.switch_page() で指定したページに遷移する
        st.switch_page("pages/new_.py")