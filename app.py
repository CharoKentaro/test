import streamlit as st
import google.generativeai as genai
from streamlit_local_storage import LocalStorage
import json
from PIL import Image
import io
import time
import pandas as pd # 【進化箇所】データ処理の達人、pandasをインポート
from datetime import datetime # 【進化箇所】ファイル名生成のためインポート

# --- ① アプリの基本設定 ---
st.set_page_config(
    page_title="お小遣いレコーダー",
    page_icon="💰"
)

# --- ② ローカルストレージの準備 ---
try:
    localS = LocalStorage()
except Exception as e:
    st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。エラー詳細: {e}")
    st.stop()

# --- ③【進化箇所】魂のプロンプトをアップグレード ---
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

# --- ④ 残高計算・表示関数 ---
def calculate_remaining_balance(monthly_allowance, total_spent):
    return monthly_allowance - total_spent

def format_balance_display(balance):
    if balance >= 0:
        return f"🟢 **{balance:,.0f} 円**"
    else:
        return f"🔴 **{abs(balance):,.0f} 円 (予算オーバー)**"

# --- ⑤ メイン処理 ---

# --- セッションステートの初期化 ---
if "initialized" not in st.session_state:
    st.session_state.monthly_allowance = float(localS.getItem("monthly_allowance") or 0.0)
    st.session_state.total_spent = float(localS.getItem("total_spent") or 0.0)
    st.session_state.receipt_preview = None # 確認モード用の状態
    st.session_state.initialized = True

# --- サイドバー（APIキー設定など）---
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
    st.caption("💡 使い方のヒント")
    st.caption("1. 今月の予算を設定")
    st.caption("2. レシート画像をアップロード") 
    st.caption("3. AI解析結果を確認・修正")
    st.caption("4. 支出を確定＆品目リストを保存")

# --- メイン画面の描画 ---
st.title("💰 お小遣いレコーダー")

# --- 確認モードの処理 ---
if st.session_state.receipt_preview:
    st.header("📝 支出の確認")
    st.info("AIが読み取った内容を確認・修正し、問題なければ「確定」してください。")

    preview_data = st.session_state.receipt_preview
    
    # 金額の修正欄
    corrected_amount = st.number_input(
        "AIが読み取った合計金額はこちらです。必要なら修正してください。", 
        value=preview_data['total_amount'],
        min_value=0.0,
        step=1.0,
        key="correction_input"
    )

    # 【進化箇所】データエディタで品目リストを表示・編集
    st.subheader("📋 品目リスト（直接編集できます）")
    # AIの抽出結果をDataFrameに変換
    if preview_data['items']:
        df_items = pd.DataFrame(preview_data['items'])
        # price列を数値型に変換（エラーは0にする）
        df_items['price'] = pd.to_numeric(df_items['price'], errors='coerce').fillna(0)
    else:
        # 品目が無い場合は空のDataFrameを作成
        df_items = pd.DataFrame(columns=['name', 'price'])
        st.info("AIは品目を検出できませんでした。手動で追加できます。")

    # データエディタを表示
    edited_df = st.data_editor(
        df_items,
        num_rows="dynamic", # 行の追加・削除を可能に
        column_config={
            "name": st.column_config.TextColumn("品物名", required=True, width="large"),
            "price": st.column_config.NumberColumn("金額（円）", format="%d円", required=True),
        },
        key="data_editor",
        use_container_width=True
    )

    # プレビュー表示
    st.divider()
    st.subheader("📊 支出後の残高プレビュー")
    current_allowance = st.session_state.monthly_allowance
    current_spent = st.session_state.total_spent
    projected_spent = current_spent + corrected_amount
    projected_balance = calculate_remaining_balance(current_allowance, projected_spent)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("今月の予算", f"{current_allowance:,.0f} 円")
    with col2:
        st.metric("使った金額", f"{projected_spent:,.0f} 円", delta=f"+{corrected_amount:,.0f} 円", delta_color="inverse")
    with col3:
        st.metric("残り予算", f"{projected_balance:,.0f} 円", delta=f"-{corrected_amount:,.0f} 円", delta_color="inverse")

    # 【進化箇所】CSVダウンロードボタン
    # DataFrameをCSV形式の文字列に変換
    csv_string = edited_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
       label="✅ 完成した品目リストをCSVでダウンロード",
       data=csv_string,
       file_name=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_receipt_details.csv",
       mime="text/csv",
    )

    # 確定・キャンセルボタン
    st.divider()
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("💰 この金額で支出を確定する", type="primary"):
            st.session_state.total_spent += corrected_amount
            localS.setItem("total_spent", st.session_state.total_spent)
            st.session_state.receipt_preview = None
            
            st.success(f"🎉 {corrected_amount:,.0f} 円の支出を記録しました！")
            st.balloons()
            time.sleep(2) 
            st.rerun()
    with cancel_col:
        if st.button("❌ キャンセル"):
            st.session_state.receipt_preview = None
            st.rerun()

# --- 通常モードの処理 ---
else:
    st.info("レシートを登録して、今月使えるお金を管理しよう！")
    
    # --- 今月のお小遣い設定 ---
    st.divider()
    st.header("💳 今月のお小遣い設定")
    new_allowance = st.number_input(
        "今月のお小遣いを入力してください", 
        value=st.session_state.monthly_allowance,
        step=1000.0,
        min_value=0.0
    )
    if st.button("この金額で設定する"):
        st.session_state.monthly_allowance = new_allowance
        localS.setItem("monthly_allowance", new_allowance)
        st.success(f"今月のお小遣いを {new_allowance:,.0f} 円に設定しました！")
        st.rerun()

    # --- 現在の残高表示 ---
    current_allowance = st.session_state.monthly_allowance
    current_spent = st.session_state.total_spent
    remaining_balance = calculate_remaining_balance(current_allowance, current_spent)
    st.divider()
    st.header("📊 現在の状況")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("今月の予算", f"{current_allowance:,.0f} 円")
    with col2:
        st.metric("使った金額", f"{current_spent:,.0f} 円")
    with col3:
        st.metric("残り予算", f"{remaining_balance:,.0f} 円")
    
    st.markdown("### 🎯 今使える自由なお金")
    st.markdown(f"## {format_balance_display(remaining_balance)}")
    
    if current_allowance > 0:
        progress_ratio = min(current_spent / current_allowance, 1.0)
        st.progress(progress_ratio)
        st.caption(f"予算使用率: {progress_ratio * 100:.1f}% ({current_spent:,.0f} 円 / {current_allowance:,.0f} 円)")

    # --- レシート解析機能 ---
    st.divider()
    st.header("📸 レシートを登録する")
    uploaded_file = st.file_uploader("処理したいレシート画像を、ここにアップロードしてください。", type=['png', 'jpg', 'jpeg'])

    if uploaded_file:
        st.image(uploaded_file, caption="アップロードされたレシート", width=300)
        if st.button("⬆️ このレシートを解析する"):
            if not gemini_api_key_input:
                st.warning("サイドバーからGemini APIキーを設定してください。")
            else:
                try:
                    with st.spinner("🧠 AIがレシートを解析中..."):
                        genai.configure(api_key=gemini_api_key_input)
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        image = Image.open(uploaded_file)
                        gemini_response = model.generate_content([GEMINI_PROMPT, image])
                        # AIの応答からJSON部分だけを安全に抽出する
                        cleaned_text = gemini_response.text.strip()
                        json_start_index = cleaned_text.find('{')
                        json_end_index = cleaned_text.rfind('}') + 1
                        
                        if json_start_index != -1 and json_end_index != 0:
                            json_str = cleaned_text[json_start_index:json_end_index]
                            extracted_data = json.loads(json_str)
                        else:
                            raise ValueError("AIの応答から有効なJSONを見つけられませんでした。")
                    
                    # 【進化箇所】AI解析結果を丸ごとセッションステートに保存
                    st.session_state.receipt_preview = {
                        "total_amount": float(extracted_data.get("total_amount", 0)),
                        "items": extracted_data.get("items", [])
                    }
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ 処理中に予期せぬエラーが発生しました: {e}")
                    if 'gemini_response' in locals():
                        st.code(gemini_response.text, language="text")

    # --- データ管理機能 ---
    st.divider()
    st.header("🔄 データ管理")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("支出履歴をリセット", type="secondary"):
            st.session_state.total_spent = 0.0
            localS.setItem("total_spent", 0.0)
            st.success("支出履歴をリセットしました！")
            st.rerun()
    with col2:
        if st.button("全データをリセット", type="secondary"):
            st.session_state.monthly_allowance = 0.0
            st.session_state.total_spent = 0.0
            st.session_state.receipt_preview = None
            st.session_state.initialized = False
            localS.setItem("monthly_allowance", 0.0)
            localS.setItem("total_spent", 0.0)
            st.success("全データをリセットしました！")
            st.rerun()
