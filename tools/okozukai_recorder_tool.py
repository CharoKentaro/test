# ===============================================================
# ★★★ okozukai_recorder_tool.py ＜真の最終完成版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
from streamlit_local_storage import LocalStorage
import json
from PIL import Image
import time
import pandas as pd
from datetime import datetime

# --- (プロンプトや補助関数は変更なし) ---
GEMINI_PROMPT = """..."""
def calculate_remaining_balance(monthly_allowance, total_spent):
    return monthly_allowance - total_spent
def format_balance_display(balance):
    if balance >= 0:
        return f"🟢 **{balance:,.0f} 円**"
    else:
        return f"🔴 **{abs(balance):,.0f} 円 (予算オーバー)**"

# --- メイン関数 ---
def show_tool(gemini_api_key):
    st.header("💰 お小遣い管理", divider='rainbow')

    # --- 原点回帰：シンプル is Best ---
    try:
        # このツールが必要なその場で、シンプルにインスタンス化する
        localS = LocalStorage()
    except Exception as e:
        st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。詳細: {e}")
        st.stop()

    prefix = "okozukai_"
    key_allowance = f"{prefix}monthly_allowance"
    key_total_spent = f"{prefix}total_spent"
    key_all_receipts = f"{prefix}all_receipt_data"

    if f"{prefix}initialized" not in st.session_state:
        st.session_state[key_allowance] = float(localS.getItem(key_allowance) or 0.0)
        st.session_state[key_total_spent] = float(localS.getItem(key_total_spent) or 0.0)
        st.session_state[key_all_receipts] = localS.getItem(key_all_receipts) or []
        st.session_state[f"{prefix}receipt_preview"] = None
        st.session_state[f"{prefix}initialized"] = True

    # (確認モードの処理は変更なし)
    if st.session_state[f"{prefix}receipt_preview"]:
        # ...(省略)...
        pass
    # --- 通常モード ---
    else:
        st.info("レシートを登録して、今月使えるお金を管理しよう！")

        # --- ★★★ ちゃろさんが見つけた「正解」のロジック ★★★ ---
        with st.expander("💳 今月のお小遣い設定", expanded=(st.session_state[key_allowance] == 0)):
             with st.form(key=f"{prefix}allowance_form"):
                new_allowance = st.number_input(
                    "今月のお小遣いを入力してください",
                    value=st.session_state[key_allowance], step=1000.0, min_value=0.0
                )
                if st.form_submit_button("この金額で設定する", use_container_width=True, type="primary"):
                    # 1. セッションステートを更新
                    st.session_state[key_allowance] = float(new_allowance)
                    # 2. LocalStorageに保存
                    localS.setItem(key_allowance, float(new_allowance))
                    st.success(f"今月のお小遣いを {float(new_allowance):,.0f} 円に設定しました！")
                    # 3. 完了後にリフレッシュ
                    time.sleep(1)
                    st.rerun()
        
        st.divider()
        st.subheader("📊 現在の状況")
        current_allowance = st.session_state[key_allowance]
        current_spent = st.session_state[key_total_spent]
        remaining_balance = calculate_remaining_balance(current_allowance, current_spent)
        col1, col2, col3 = st.columns(3)
        col1.metric("今月の予算", f"{current_allowance:,.0f} 円")
        col2.metric("使った金額", f"{current_spent:,.0f} 円")
        col3.metric("残り予算", f"{remaining_balance:,.0f} 円")
        
        # (以降のコードは変更なし)
        # ...
