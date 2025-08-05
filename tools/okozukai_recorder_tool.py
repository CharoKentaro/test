# ===============================================================
# ★★★ okozukai_recorder_tool.py ＜最終実験・URLパラメータ版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
# LocalStorage はもう使いません
# from streamlit_local_storage import LocalStorage
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

    prefix = "okozukai_"
    
    # --- Step 1: 初期化 ---
    # URLのクエリパラメータから直接データを読み込む
    if f"{prefix}initialized" not in st.session_state:
        # st.query_params を使ってURLから値を取得
        st.session_state[f"{prefix}monthly_allowance"] = float(st.query_params.get(f"{prefix}monthly_allowance", 0.0))
        # 他のデータはセッション内でのみ管理（簡略化のため）
        st.session_state[f"{prefix}total_spent"] = 0.0
        st.session_state[f"{prefix}all_receipts"] = []
        st.session_state[f"{prefix}receipt_preview"] = None
        st.session_state[f"{prefix}initialized"] = True

    # (確認モードは簡略化のため、今回は省略します)
    if st.session_state[f"{prefix}receipt_preview"]:
        # ... (省略) ...
        pass
    # --- 3. 通常モードの表示 ---
    else:
        st.info("レシートを登録して、今月使えるお金を管理しよう！")

        # --- ★★★ これが、LocalStorageを使わない最終実験コードです ★★★ ---
        with st.expander("💳 今月のお小遣い設定", expanded=(st.session_state[f"{prefix}monthly_allowance"] == 0)):
            # フォームも不要、シンプルなon_changeでセッションステートを直接更新
            
            def update_allowance_and_url():
                # Step A: セッションステートを更新
                new_val = st.session_state[f"{prefix}allowance_input"]
                st.session_state[f"{prefix}monthly_allowance"] = float(new_val)
                # Step B: URLを直接書き換える
                st.query_params[f"{prefix}monthly_allowance"] = str(float(new_val))
                st.toast(f"✅ 設定をURLに保存しました！")

            # 現在のセッションステートの値を表示
            current_value = float(st.session_state.get(f"{prefix}monthly_allowance", 0.0))
            
            st.number_input(
                "今月のお小遣いを入力してください",
                value=current_value,
                step=1000.0,
                min_value=0.0,
                key=f"{prefix}allowance_input",
                on_change=update_allowance_and_url,
                help="入力後、Enterキーを押すか、他の場所をクリックするとURLに保存されます。"
            )

        st.divider()
        st.subheader("📊 現在の状況")
        current_allowance = st.session_state[f"{prefix}monthly_allowance"]
        current_spent = st.session_state[f"{prefix}total_spent"]
        remaining_balance = calculate_remaining_balance(current_allowance, current_spent)
        col1, col2, col3 = st.columns(3)
        col1.metric("今月の予算", f"{current_allowance:,.0f} 円")
        col2.metric("使った金額", f"{current_spent:,.0f} 円")
        col3.metric("残り予算", f"{remaining_balance:,.0f} 円")
        
        st.markdown(f"#### 🎯 今使えるお金は…")
        st.markdown(f"<p style='text-align: center; font-size: 2.5em; font-weight: bold;'>{format_balance_display(remaining_balance)}</p>", unsafe_allow_html=True)
        if current_allowance > 0:
            progress_ratio = min(current_spent / current_allowance, 1.0)
            st.progress(progress_ratio)
            st.caption(f"予算使用率: {progress_ratio * 100:.1f}%")
        
        # (以降のレシート登録、履歴表示は簡略化のため省略)
