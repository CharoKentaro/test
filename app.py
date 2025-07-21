import streamlit as st
import google.generativeai as genai
from streamlit_local_storage import LocalStorage
import json
from PIL import Image
import io
import time
import pandas as pd
from datetime import datetime

# --- ① アプリの基本設定 ---
st.set_page_config(
    page_title="お小遣いレコーダー",
    page_icon="💰",
    layout="wide" # 【地味な進化】画面を広く使って見やすくする
)

# --- ② ローカルストレージの準備 ---
try:
    localS = LocalStorage()
except Exception as e:
    st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。エラー詳細: {e}")
    st.stop()

# --- ③ 魂のプロンプト（変更なし） ---
GEMINI_PROMPT = """
あなたは、レシートの画像を直接解析する、超優秀な経理アシスタントAIです。
# 指示
レシートの画像の中から、以下の情報を注意深く、正確に抽出してください。
1.  **合計金額 (total_amount)**: 支払いの総額。
2.  **購入品リスト (items)**: 購入した「品物名(name)」と「その単価(price)」のリスト。
# 出力形式
*   抽出した結果を、必ず以下のJSON形式で出力してください。
*   数値は、数字のみを抽出してください（円やカンマは不要）。
*   値が見つからない場合は、数値項目は "0"、リスト項目は空のリスト `[]` としてください。
*   「小計」「お預り」「お釣り」「店名」「合計」といった単語そのものは、購入品リストに含めないでください。
*   JSON以外の、前置きや説明は、絶対に出力しないでください。
{
  "total_amount": "ここに合計金額の数値",
  "items": [
    { "name": "ここに品物名1", "price": "ここに単価1" },
    { "name": "ここに品物名2", "price": "ここに単価2" }
  ]
}
"""

# --- ④ 補助関数 ---
def calculate_remaining_balance(monthly_allowance, total_spent):
    return monthly_allowance - total_spent

def format_balance_display(balance):
    if balance >= 0:
        return f"🟢 **{balance:,.0f} 円**"
    else:
        return f"🔴 **{abs(balance):,.0f} 円 (予算オーバー)**"

# --- ⑤ メイン処理 ---

# --- 【革命的進化】セッションステートの初期化 ---
if "initialized" not in st.session_state:
    st.session_state.monthly_allowance = float(localS.getItem("monthly_allowance") or 0.0)
    st.session_state.total_spent = float(localS.getItem("total_spent") or 0.0)
    st.session_state.receipt_preview = None
    # 全レシートデータを格納する「金庫」を準備
    st.session_state.all_receipts = localS.getItem("all_receipt_data") or []
    st.session_state.initialized = True

# --- サイドバー ---
with st.sidebar:
    st.header("⚙️ API設定")
    saved_gemini_key = localS.getItem("gemini_api_key")
    gemini_api_key_input = st.text_input(
        "Gemini APIキー", type="password",
        value=saved_gemini_key if isinstance(saved_gemini_key, str) else ""
    )
    if st.button("Geminiキーを記憶"):
        localS.setItem("gemini_api_key", gemini_api_key_input)
        st.success("Gemini APIキーを記憶しました！")
    
    st.divider()
    st.caption("💡 使い方のヒント...")

# --- メイン画面 ---
st.title("💰 AIお小遣いレコーダー")

# --- 確認モード ---
if st.session_state.receipt_preview:
    st.header("📝 支出の確認")
    st.info("AIが読み取った内容を確認・修正し、問題なければ「確定」してください。")

    preview_data = st.session_state.receipt_preview
    
    corrected_amount = st.number_input(
        "AIが読み取った合計金額はこちらです。必要なら修正してください。", 
        value=preview_data['total_amount'], min_value=0.0, step=1.0, key="correction_input"
    )

    st.subheader("📋 品目リスト（直接編集できます）")
    if preview_data['items']:
        df_items = pd.DataFrame(preview_data['items'])
        df_items['price'] = pd.to_numeric(df_items['price'], errors='coerce').fillna(0)
    else:
        df_items = pd.DataFrame([{"name": "", "price": 0}]) # 空の場合も入力行を用意
        st.info("AIは品目を検出できませんでした。手動で追加・修正してください。")

    edited_df = st.data_editor(
        df_items, num_rows="dynamic",
        column_config={
            "name": st.column_config.TextColumn("品物名", required=True, width="large"),
            "price": st.column_config.NumberColumn("金額（円）", format="%d円", required=True),
        },
        key="data_editor", use_container_width=True
    )

    st.divider()
    st.subheader("📊 支出後の残高プレビュー")
    # ... (プレビュー表示部分は変更なし)

    st.divider()
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("💰 この金額で支出を確定する", type="primary"):
            # 【革命的進化】レシートデータを金庫に保存
            new_receipt_record = {
                "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "total_amount": corrected_amount,
                "items": edited_df.to_dict('records') # 編集後の品目リストを保存
            }
            st.session_state.all_receipts.append(new_receipt_record)
            localS.setItem("all_receipt_data", st.session_state.all_receipts)

            # 合計支出額も更新
            st.session_state.total_spent += corrected_amount
            localS.setItem("total_spent", st.session_state.total_spent)
            
            st.session_state.receipt_preview = None
            
            st.success(f"🎉 {corrected_amount:,.0f} 円の支出を記録し、金庫に保存しました！")
            st.balloons()
            time.sleep(2) 
            st.rerun()
    with cancel_col:
        if st.button("❌ キャンセル"):
            st.session_state.receipt_preview = None
            st.rerun()

# --- 通常モード ---
else:
    st.info("レシートを登録して、今月使えるお金を管理しよう！")
    
    # --- 今月のお小遣い設定 ---
    # ... (変更なし)

    # --- 現在の残高表示 ---
    # ... (変更なし)

    # --- レシート解析機能 ---
    st.divider()
    st.header("📸 レシートを登録する")
    # ... (変更なし)

    # --- 【革命的進化】全データ書き出しコーナー ---
    st.divider()
    st.header("🗂️ 全データの書き出し")
    
    if st.session_state.all_receipts:
        st.info(f"現在、{len(st.session_state.all_receipts)} 件のレシートデータが金庫に保存されています。")
        
        # ダウンロード用のデータを作成（全品目をフラットなリストに）
        flat_list_for_csv = []
        for receipt in st.session_state.all_receipts:
            for item in receipt['items']:
                flat_list_for_csv.append({
                    "日付": receipt['date'],
                    "品物名": item['name'],
                    "金額": item['price'],
                    "レシート合計": receipt['total_amount']
                })
        
        df_for_csv = pd.DataFrame(flat_list_for_csv)
        csv_string = df_for_csv.to_csv(index=False, encoding='utf-8-sig')

        st.download_button(
           label="✅ 全支出履歴をCSVでダウンロード",
           data=csv_string,
           file_name=f"all_receipts_{datetime.now().strftime('%Y%m%d')}.csv",
           mime="text/csv",
           type="primary"
        )
    else:
        st.warning("まだ保存されているレシートデータがありません。")


    # --- データ管理機能 ---
    st.divider()
    st.header("🔄 データ管理")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("支出履歴のみリセット", type="secondary"):
            st.session_state.total_spent = 0.0
            localS.setItem("total_spent", 0.0)
            # 【革命的進化】全レシートデータもリセット
            st.session_state.all_receipts = []
            localS.setItem("all_receipt_data", [])
            st.success("支出履歴と全レシートデータをリセットしました！")
            st.rerun()
    with col2:
        if st.button("【完全初期化】全データをリセット", type="secondary", help="予算設定も含め、すべてのデータを消去します。"):
            st.session_state.monthly_allowance = 0.0
            st.session_state.total_spent = 0.0
            st.session_state.receipt_preview = None
            st.session_state.all_receipts = []
            st.session_state.initialized = False
            localS.setItem("monthly_allowance", 0.0)
            localS.setItem("total_spent", 0.0)
            localS.setItem("all_receipt_data", [])
            st.success("すべてのデータをリセットしました！")
            st.rerun()
