# ===============================================================
# ★★★ app.py ＜支配者への最終抵抗版＞ ★★★
# ===============================================================
import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="最終抵抗テスト", page_icon="💾")
st.title("💾 サーバー直接保存テスト")

# --- 唯一の記憶装置：サーバー上のファイル ---
# このファイルは、ブラウザがリロードしても消えない
STATE_FILE = Path("state.json")

# --- データの読み書きを行う関数 ---

def read_state():
    """サーバー上のファイルから数値を読み込む"""
    if STATE_FILE.exists():
        with STATE_FILE.open("r") as f:
            try:
                data = json.load(f)
                # "value" キーの値を取得、なければ0.0
                return float(data.get("value", 0.0))
            except (json.JSONDecodeError, ValueError):
                # ファイルが空か壊れている場合は0.0を返す
                return 0.0
    else:
        # ファイルが存在しない初回は0.0を返す
        return 0.0

def write_state(value):
    """サーバー上のファイルに数値を書き込む"""
    with STATE_FILE.open("w") as f:
        json.dump({"value": float(value)}, f)
    st.toast("サーバーに値を保存しました！", icon="✅")


# --- アプリのロジック ---

# 1. 起動時に、サーバー上のファイルから現在の値を読み込む
current_value = read_state()

# 2. UIの表示
st.info(
    "このアプリは、ブラウザではなく、サーバーに直接データを保存します。"
    "これでリロードしても値が消えなければ、私たちはついに真犯人を特定したことになります。"
)
st.divider()

# 今回は、ボタンを押した時だけ保存する、最も確実な方法を採用
input_value = st.number_input(
    label="ここに数値を入力してください",
    value=current_value,
    step=1000.0,
    key="input_widget"
)

if st.button("この数値をサーバーに保存する", type="primary"):
    # ボタンが押されたら、書き込み関数を呼び出す
    write_state(input_value)
    # Streamlitに値を再読み込みさせるために、リロードする
    st.rerun()

st.divider()

# --- 結果の確認 ---
st.subheader("現在のサーバーに保存されている値")
st.markdown(f"## **`{current_value:,.0f}`**")

st.warning("この方法は、アプリを利用するすべての人で、同じ値が共有されます。個人用ツールだからこそ使える、最後の切り札です。")
