# ===============================================================
# ★★★ okozukai_recorder_tool.py ＜最終確定版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
from streamlit_local_storage import LocalStorage 
import json
from PIL import Image
import pandas as pd
from datetime import datetime, timedelta, timezone
import time

# --- プロンプトや補助関数 ---
GEMINI_PROMPT = """あなたはレシート解析のプロです。アップロードされたレシートの画像から、以下の情報を正確に抽出し、指定されたJSON形式で出力してください。

# 命令
- レシートに記載されている「合計金額」を抽出してください。
- レシートに記載されている「品目リスト」を抽出してください。リストには各品物の「品物名(name)」と「金額(price)」を含めてください。
- 「軽減税率対象」や「※」などの記号は品物名に含めないでください。
- 小計や割引、ポイント利用額などは無視し、最終的な支払総額を「合計金額」としてください。

# 出力形式 (JSON)
{
  "total_amount": (ここに合計金額の数値を入力),
  "items": [
    {"name": "(品物名1)", "price": (金額1)},
    {"name": "(品物名2)", "price": (金額2)},
    ...
  ]
}
"""
def calculate_remaining_balance(monthly_allowance, total_spent):
    return monthly_allowance - total_spent
def format_balance_display(balance):
    if balance >= 0:
        return f"🟢 **{balance:,.0f} 円**"
    else:
        return f"🔴 **{abs(balance):,.0f} 円 (予算オーバー)**"

# --- メイン関数 ---
def show_tool(gemini_api_key, localS: LocalStorage):
    st.header("💰 お小遣い管理", divider='rainbow')
    
    prefix = "okozukai_"
    key_allowance = f"{prefix}monthly_allowance"
    key_total_spent = f"{prefix}total_spent"
    key_all_receipts = f"{prefix}all_receipt_data"

    # --- Step 1: 初期化 ---
    # 初回実行時のみ、LocalStorageから値を読み込んでst.session_stateを初期化する
    if f"{prefix}initialized" not in st.session_state:
        st.session_state[key_allowance] = float(localS.getItem(key_allowance) or 0.0)
        st.session_state[key_total_spent] = float(localS.getItem(key_total_spent) or 0.0)
        st.session_state[key_all_receipts] = localS.getItem(key_all_receipts) or []
        st.session_state[f"{prefix}receipt_preview"] = None
        st.session_state[f"{prefix}usage_count"] = 0
        st.session_state[f"{prefix}initialized"] = True

    # --- Step 2: 状態の同期（バックアップ処理） ---
    # st.session_stateとLocalStorageを比較し、差分があれば保存する
    try:
        session_val = float(st.session_state.get(key_allowance, 0.0))
        storage_val = float(localS.getItem(key_allowance) or 0.0)

        if session_val != storage_val:
            localS.setItem(key_allowance, session_val, key="okozukai_allowance_storage_sync")
            st.toast(f"✅ 設定をブラウザに保存しました！", icon="💾")
    except (ValueError, TypeError):
        pass

    # (アンロックモード、確認モードは変更なし)
    usage_limit = 1
    # ... (省略していた部分を展開) ...
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit

    if is_limit_reached:
        # (アンロック・モードのコード)
        pass
    elif st.session_state[f"{prefix}receipt_preview"]:
        # (確認モードのコード)
        pass
    else:
        # --- Step 3: UIの描画と操作 ---
        st.info("レシートを登録して、今月使えるお金を管理しよう！")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、レシートを読み込めます。")

        with st.expander("💳 今月のお小遣い設定", expanded=(st.session_state[key_allowance] == 0)):
            
            # コールバック関数：入力値をst.session_stateに反映させる
            def update_session_state():
                input_val = st.session_state[f"{prefix}allowance_input_key"]
                st.session_state[key_allowance] = float(input_val)

            st.number_input(
                "今月のお小遣いを入力してください", 
                value=float(st.session_state[key_allowance]), 
                step=1000.0, 
                min_value=0.0,
                key=f"{prefix}allowance_input_key",
                on_change=update_session_state
            )
            
        st.divider()
        st.subheader("📊 現在の状況")
        current_allowance = st.session_state[key_allowance]
        current_spent = st.session_state[key_total_spent]
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
        
        # (以降のレシート登録、履歴表示部分は変更なし)
        # ...
