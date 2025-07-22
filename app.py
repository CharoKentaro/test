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
    page_icon="💰"
)

# --- ② ローカルストレージの準備 ---
try:
    localS = LocalStorage()
except Exception as e:
    st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。エラー詳細: {e}")
    st.stop()

# --- ③ 魂のプロンプト ---
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

# --- セッションステートの初期化に「金庫」を追加 ---
if "initialized" not in st.session_state:
    st.session_state.monthly_allowance = float(localS.getItem("monthly_allowance") or 0.0)
    st.session_state.total_spent = float(localS.getItem("total_spent") or 0.0)
    st.session_state.receipt_preview = None
    # 全レシートデータを格納する「金庫」を準備
    st.session_state.all_receipts = localS.getItem("all_receipt_data") or []
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
        localS.setItem("gemini_api_key", gemini_api_key_input, key="set_api_key")
        st.success("Gemini APIキーを記憶しました！")

    st.divider()
    st.caption("💡 使い方のヒント")
    st.caption("1. 今月の予算を設定")
    st.caption("2. レシートを撮影 or アップロード")
    st.caption("3. AI解析結果を確認・修正")
    st.caption("4. 支出を確定＆品目リストを保存")
    st.caption("5. 全履歴をいつでもダウンロード")


# --- メイン画面の描画 ---
st.title("💰 お小遣いレコーダー")

# --- 確認モードの処理 ---
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
        df_items = pd.DataFrame([{"name": "", "price": 0}])
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

    # 確定・キャンセルボタン
    st.divider()
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("💰 この金額で支出を確定する", type="primary"):
            new_receipt_record = {
                "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "total_amount": corrected_amount,
                "items": edited_df.to_dict('records')
            }
            st.session_state.all_receipts.append(new_receipt_record)
            localS.setItem("all_receipt_data", st.session_state.all_receipts, key="confirm_set_receipts")

            st.session_state.total_spent += corrected_amount
            localS.setItem("total_spent", st.session_state.total_spent, key="confirm_set_total")

            st.session_state.receipt_preview = None

            st.success(f"🎉 {corrected_amount:,.0f} 円の支出を記録し、履歴に保存しました！")
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

    st.divider()
    st.header("💳 今月のお小遣い設定")
    new_allowance = st.number_input(
        "今月のお小遣いを入力してください",
        value=st.session_state.monthly_allowance, step=1000.0, min_value=0.0
    )
    if st.button("この金額で設定する"):
        st.session_state.monthly_allowance = new_allowance
        localS.setItem("monthly_allowance", new_allowance, key="set_allowance")
        st.success(f"今月のお小遣いを {new_allowance:,.0f} 円に設定しました！")
        st.rerun()

    st.divider()
    st.header("📊 現在の状況")
    current_allowance = st.session_state.monthly_allowance
    current_spent = st.session_state.total_spent
    remaining_balance = calculate_remaining_balance(current_allowance, current_spent)
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

    st.divider()
    st.header("📸 レシートを登録する")

    # --- ▼▼▼【ちゃろ様ご提案機能】ここからが変更箇所です ▼▼▼ ---
    st.write("##### 方法１：カメラで直接撮影する")
    camera_image = st.camera_input(
        "📷 **カメラを起動して撮影**",
        help="スマホのカメラでレシートを直接撮影して読み込ませます。"
    )

    st.write("##### 方法２：保存済みの画像を選ぶ")
    file_uploader = st.file_uploader(
        "📁 **画像をアップロード**",
        type=['png', 'jpg', 'jpeg'],
        help="撮影済みのレシート画像をファイルから選択します。"
    )

    # カメラ入力かファイルアップロードのどちらかが使用された場合に `uploaded_file` に画像データを格納
    uploaded_file = camera_image or file_uploader
    # --- ▲▲▲ ここまでが変更箇所です ▲▲▲ ---

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
                        cleaned_text = gemini_response.text.strip()
                        json_start_index = cleaned_text.find('{')
                        json_end_index = cleaned_text.rfind('}') + 1

                        if json_start_index != -1 and json_end_index != 0:
                            json_str = cleaned_text[json_start_index:json_end_index]
                            extracted_data = json.loads(json_str)
                        else:
                            raise ValueError("AIの応答から有効なJSONを見つけられませんでした。")

                    st.session_state.receipt_preview = {
                        "total_amount": float(extracted_data.get("total_amount", 0)),
                        "items": extracted_data.get("items", [])
                    }
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ 処理中に予期せぬエラーが発生しました: {e}")
                    if 'gemini_response' in locals():
                        st.code(gemini_response.text, language="text")

    st.divider()
    st.header("🗂️ 全支出履歴の書き出し")

    if st.session_state.all_receipts:
        st.info(f"現在、{len(st.session_state.all_receipts)} 件のレシートデータが保存されています。")

        flat_list_for_csv = []
        for receipt in st.session_state.all_receipts:
            # 【堅牢性向上のための修正】itemsがNoneまたは空の場合の処理を追加
            items = receipt.get('items')
            if not items: 
                continue
            for item in items:
                item_name = item.get('name', 'N/A')
                item_price = item.get('price', 0)
                flat_list_for_csv.append({
                    "日付": receipt.get('date', 'N/A'),
                    "品物名": item_name,
                    "金額": item_price,
                    "レシート合計": receipt.get('total_amount', 0)
                })

        if flat_list_for_csv:
            df_for_csv = pd.DataFrame(flat_list_for_csv)
            csv_string = df_for_csv.to_csv(index=False, encoding='utf-8-sig')

            st.download_button(
               label="✅ 全支出履歴をCSVでダウンロード",
               data=csv_string,
               file_name=f"all_receipts_history_{datetime.now().strftime('%Y%m%d')}.csv",
               mime="text/csv",
               type="primary"
            )
        else:
            st.warning("保存されているデータに有効な品目がありません。")
    else:
        st.warning("まだ保存されているレシートデータがありません。")

    st.divider()
    st.header("🔄 データ管理")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("支出履歴とレシートデータをリセット", type="secondary"):
            st.session_state.total_spent = 0.0
            st.session_state.all_receipts = []
            localS.setItem("total_spent", 0.0, key="reset_spent")
            localS.setItem("all_receipt_data", [], key="reset_receipts")
            st.success("支出履歴と全レシートデータをリセットしました！")
            st.rerun()
    with col2:
        if st.button("【完全初期化】全データをリセット", type="secondary", help="予算設定も含め、すべてのデータを消去します。"):
            st.session_state.monthly_allowance = 0.0
            st.session_state.total_spent = 0.0
            st.session_state.receipt_preview = None
            st.session_state.all_receipts = []
            st.session_state.initialized = False
            localS.setItem("monthly_allowance", 0.0, key="full_reset_allowance")
            localS.setItem("total_spent", 0.0, key="full_reset_spent")
            localS.setItem("all_receipt_data", [], key="full_reset_receipts")
            st.success("すべてのデータをリセットしました！")
            st.rerun()
