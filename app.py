# ===============================================================
# ★★★ app.py ＜真の、そして唯一の最終完成版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import json
from pathlib import Path
from PIL import Image
import time
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------------
# Section 1: 永続化のための関数群 (成功した実験からそのまま流用)
# ---------------------------------------------------------------

# 唯一の信頼できる記憶装置
STATE_FILE = Path("multitool_state.json")

def read_app_state():
    """サーバー上のファイルからアプリ全体の全データを読み込む"""
    if STATE_FILE.exists():
        with STATE_FILE.open("r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def write_app_state(data):
    """アプリ全体の全データをサーバー上のファイルに書き込む"""
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------------------------------------------------------------
# Section 2: 各ツールの補助関数 (必要なものをここに集約)
# ---------------------------------------------------------------

# お小遣いツール用
def calculate_remaining_balance(monthly_allowance, total_spent):
    return monthly_allowance - total_spent

def format_balance_display(balance):
    if balance >= 0:
        return f"🟢 **{balance:,.0f} 円**"
    else:
        return f"🔴 **{abs(balance):,.0f} 円 (予算オーバー)**"

# ---------------------------------------------------------------
# Section 3: メインのUIとロジック
# ---------------------------------------------------------------

st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

# --- アプリ全体のデータ管理 ---
# 起動時に一度だけ、サーバーファイルから全データを読み込む
if 'app_state' not in st.session_state:
    st.session_state.app_state = read_app_state()

# --- サイドバー (APIキー管理) ---
with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()
    
    # APIキーはセッションステートで管理
    if 'gemini_api_key' not in st.session_state.app_state:
        st.session_state.app_state['gemini_api_key'] = ''

    with st.expander("⚙️ APIキーの設定", expanded=(not st.session_state.app_state['gemini_api_key'])):
        with st.form("api_key_form"):
            api_key_input = st.text_input(
                "Gemini APIキー", 
                type="password", 
                value=st.session_state.app_state['gemini_api_key']
            )
            if st.form_submit_button("💾 保存", use_container_width=True):
                st.session_state.app_state['gemini_api_key'] = api_key_input
                write_app_state(st.session_state.app_state)
                st.success("キーを保存しました！"); time.sleep(1); st.rerun()

    st.divider()
    tool_selection = st.radio(
        "利用するツールを選択してください:",
        ("💰 お小遣い管理", "🤝 翻訳ツール", "📅 カレンダー登録", "📝 議事録作成", "🧠 賢者の記憶", "❤️ 認知予防ツール"),
        key="tool_selection"
    )
    st.divider()

# --- メインコンテンツ ---
api_key = st.session_state.app_state.get('gemini_api_key', '')

if tool_selection == "💰 お小遣い管理":
    st.header("💰 お小遣い管理", divider='rainbow')

    # お小遣いツール専用のキーを定義
    key_allowance = "okozukai_monthly_allowance"
    key_total_spent = "okozukai_total_spent"
    key_all_receipts = "okozukai_all_receipts"

    # セッションステート内に、お小遣いデータがなければ初期化
    if key_allowance not in st.session_state.app_state:
        st.session_state.app_state[key_allowance] = 0.0
        st.session_state.app_state[key_total_spent] = 0.0
        st.session_state.app_state[key_all_receipts] = []

    # --- UIとロジック ---
    with st.expander("💳 今月のお小遣い設定", expanded=(st.session_state.app_state[key_allowance] == 0)):
        with st.form(key="allowance_form"):
            new_allowance = st.number_input(
                "今月のお小遣いを入力してください",
                value=float(st.session_state.app_state[key_allowance]),
                step=1000.0
            )
            if st.form_submit_button("この金額で設定する", type="primary"):
                st.session_state.app_state[key_allowance] = new_allowance
                # データを書き込む際は、必ずアプリ全体のデータを書き込む
                write_app_state(st.session_state.app_state)
                st.success(f"お小遣いを {new_allowance:,.0f} 円に設定しました！")
                time.sleep(1)
                st.rerun()

    st.divider()
    st.subheader("📊 現在の状況")
    
    current_allowance = st.session_state.app_state[key_allowance]
    current_spent = st.session_state.app_state[key_total_spent]
    remaining_balance = calculate_remaining_balance(current_allowance, current_spent)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("今月の予算", f"{current_allowance:,.0f} 円")
    col2.metric("使った金額", f"{current_spent:,.0f} 円")
    col3.metric("残り予算", f"{remaining_balance:,.0f} 円")

    # (以降、レシート登録など、他の機能もこの app.py の中に同様に記述していく)

else:
    # 他のツールが選択された場合の表示
    st.header(f"🔧 {tool_selection}", divider='rainbow')
    st.info("このツールは現在開発中です。")
