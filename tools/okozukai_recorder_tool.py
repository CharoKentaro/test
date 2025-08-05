# ===============================================================
# ★★★ app.py ＜ゼロからの再出発版＞ ★★★
# ===============================================================
import streamlit as st

st.set_page_config(page_title="シンプル保存テスト", page_icon="💾")

st.title("💾 シンプル保存テスト")
st.info(
    "このアプリの目的はただ一つです。"
    "下のボックスに入力した数値が、スマホでリロードしても消えずに残るか、それだけを検証します。"
)

# --- 定義 ---
# URLで使う、シンプルで短いキー
URL_KEY = "value" 

# --- ロジック ---

# 1. ページが読み込まれたら、まずURLを見る
try:
    # URLに ?value=... があれば、その値を取得して数値に変換する
    # なければ、デフォルト値として 0.0 を使う
    current_value = float(st.query_params.get(URL_KEY, 0.0))
except (AttributeError, ValueError):
    st.error("お使いのStreamlitのバージョンが古いか、URLの値が不正です。")
    current_value = 0.0

# 2. ユーザーが値を変更したら、即座にURLを書き換えるコールバック関数
def update_url():
    # 入力ボックスの現在の値を取得
    new_value = st.session_state["input_widget"]
    # URLを直接書き換える (?value=... の部分)
    st.query_params[URL_KEY] = str(float(new_value))

# 3. UIの表示
st.divider()

# number_inputウィジェットを配置
st.number_input(
    label="ここに数値を入力してください",
    value=current_value,  # 表示する値は、URLから取得した値
    step=1000.0,
    key="input_widget",  # ウィジェットを特定するためのキー
    on_change=update_url,  # 値が変更されたら、update_url関数を呼び出す
    help="入力後、Enterキーを押すか、枠の外をクリックするとURLが更新されます。"
)

st.divider()

# --- 結果の確認 ---
st.subheader("現在の保存されている値")

# 強調表示で、現在の値を分かりやすく見せる
st.markdown(f"## **`{current_value:,.0f}`**")

st.warning(
    "操作方法：数値を入力した後、ブラウザの「リロード（再読み込み）」ボタンを押してください。"
    "この数値が消えなければ、私たちの勝利です。"
)
