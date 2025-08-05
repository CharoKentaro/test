# ===============================================================
# ★★★ okozukai_recorder_tool.py ＜最後の切り札・URL完全依存版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import time
import pandas as pd
from datetime import datetime

# LocalStorage は、もうこの事件では使わない
# from streamlit_local_storage import LocalStorage 

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
    st.error("【最終推理モード】LocalStorageは使わず、URLだけでデータを保存するテストです。")

    prefix = "okozukai_"
    # URLで使う、短くて分かりやすいキーを定義
    key_allowance_url = f"{prefix}ma" 
    key_spent_url = f"{prefix}ts"
    
    # 複雑なデータ（履歴など）は、この実験ではセッション内のみで一時的に管理
    key_all_receipts_session = f"{prefix}all_receipts"
    key_preview_session = f"{prefix}receipt_preview"

    # --- Step 1: 初期化 ---
    # URLのクエリパラメータが唯一の信頼できる情報源
    try:
        # URLから値を取得し、float型に変換。なければ0.0
        allowance_from_url = float(st.query_params.get(key_allowance_url, 0.0))
        spent_from_url = float(st.query_params.get(key_spent_url, 0.0))
    except (AttributeError, ValueError):
        st.warning("お使いのStreamlitのバージョンが古いか、URLの値が不正です。")
        allowance_from_url = 0.0
        spent_from_url = 0.0

    # セッションステートを、常にURLの値で上書きして同期する
    st.session_state[key_allowance_url] = allowance_from_url
    st.session_state[key_spent_url] = spent_from_url
    if key_preview_session not in st.session_state:
        st.session_state[key_preview_session] = None
        st.session_state[key_all_receipts_session] = []


    # 確認モードの処理 (この実験では簡易的に)
    if st.session_state[key_preview_session]:
        st.subheader("📝 支出の確認")
        # (中略)...
        if st.button("💰 この金額で支出を確定する"):
            # 本来はここでAI解析結果の金額を取得する
            corrected_amount = 100 # 仮の値
            new_spent = st.session_state[key_spent_url] + corrected_amount
            # URLの spent パラメータを更新
            st.query_params[key_spent_url] = str(new_spent)
            st.session_state[key_preview_session] = None
            st.success("支出を記録しました！"); time.sleep(1); st.rerun()

    # --- 通常モード ---
    else:
        st.info("レシートを登録して、今月使えるお金を管理しよう！")

        # --- ★★★ これが、犯人を追い詰める最後の尋問です ★★★ ---
        with st.expander("💳 今月のお小遣い設定", expanded=(st.session_state[key_allowance_url] == 0)):
            
            # コールバック関数: 値が変更されたら、即座にURLを書き換える
            def update_url_callback():
                new_val = st.session_state[f"{prefix}allowance_input"]
                st.query_params[key_allowance_url] = str(float(new_val))

            st.number_input(
                "今月のお小遣いを入力してください",
                value=st.session_state[key_allowance_url],
                step=1000.0,
                min_value=0.0,
                key=f"{prefix}allowance_input",
                on_change=update_url_callback,
                help="入力後、Enterキーを押すか、他の場所をクリックするとURLに保存されます。"
            )

        st.divider()
        st.subheader("📊 現在の状況")
        # 表示は常にセッションステート（URLと同期済み）から行う
        display_allowance = st.session_state[key_allowance_url]
        display_spent = st.session_state[key_spent_url]
        remaining_balance = calculate_remaining_balance(display_allowance, display_spent)

        col1, col2, col3 = st.columns(3)
        col1.metric("今月の予算", f"{display_allowance:,.0f} 円")
        col2.metric("使った金額", f"{display_spent:,.0f} 円")
        col3.metric("残り予算", f"{remaining_balance:,.0f} 円")

        # (以降のレシート登録機能などは、この実験では動作を簡略化しています)
        st.divider()
        st.info("この実験では、レシート登録・履歴機能は一時的に無効化されています。")
