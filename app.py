import streamlit as st
import google.generativeai as genai
from streamlit_local_storage import LocalStorage
import json
from PIL import Image
import io

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

# --- ③ Geminiに渡す、魂のプロンプト（シンプル版）---
GEMINI_PROMPT = """
あなたは、レシートの画像を直接解析する、経理アシスタントAIです。
# 指示
レシートの画像の中から、「合計金額」「お預り金額」「お釣り」の3つの、支出に関わる重要な数字だけを、注意深く、抽出してください。
# 出力形式
*   抽出した結果を、必ず以下のJSON形式で出力してください。
*   数値は、数字のみを抽出してください（円やカンマは不要）。
*   値が見つからない場合は、"0" と記載してください。
*   JSON以外の、前置きや説明は、絶対に出力しないでください。

{
  "total_amount": "ここに合計金額の数値",
  "tendered_amount": "ここにお預り金額の数値",
  "change_amount": "ここにお釣り金額の数値"
}
"""

# --- ④ メインの処理を実行する関数 ---
def run_allowance_recorder_app(gemini_api_key):
    st.title("💰 お小遣いレコーダー")
    st.info("レシートを登録して、今月使えるお金を管理しよう！")
    
    # --- ★★★ ここが、魂の、新機能 ★★★ ---
    st.divider()
    st.header("今月のお小遣い設定")
    
    # セッションステートの初期化
    if 'monthly_allowance' not in st.session_state:
        st.session_state.monthly_allowance = float(localS.getItem("monthly_allowance") or 0.0)
    
    new_allowance = st.number_input(
        "今月のお小遣いを入力してください", 
        value=st.session_state.monthly_allowance,
        step=1000.0
    )
    if st.button("この金額で設定する"):
        st.session_state.monthly_allowance = new_allowance
        localS.setItem("monthly_allowance", new_allowance)
        st.success(f"今月のお小遣いを {new_allowance:,.0f} 円に設定しました！")

    st.header(f"今、自由に使えるお金： {st.session_state.monthly_allowance:,.0f} 円")
    st.divider()

    # --- レシート解析機能 ---
    st.header("レシートを登録する")
    uploaded_file = st.file_uploader("処理したいレシート画像を、ここにアップロードしてください。", type=['png', 'jpg', 'jpeg'])

    if st.button("⬆️ このレシートを解析して支出を記録する"):
        if not all([uploaded_file, gemini_api_key]):
            st.warning("画像と、Gemini APIキーが設定されているか確認してください。")
            st.stop()

        try:
            with st.spinner("🧠 AIがレシートを解析中..."):
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                image = Image.open(uploaded_file)
                gemini_response = model.generate_content([GEMINI_PROMPT, image])
                cleaned_json_str = gemini_response.text.strip().replace("```json", "").replace("```", "")
                extracted_data = json.loads(cleaned_json_str)
            
            st.success("🎉 AIによる解析が完了しました！")
            
            # --- 支出の反映 ---
            try:
                total_amount = float(extracted_data.get("total_amount", 0))
                
                # ユーザーが確認・修正できる入力欄
                corrected_total = st.number_input("AIが読み取った合計金額はこちらです。必要なら修正してください。", value=total_amount)
                
                if st.button("この金額で支出を確定する"):
                    st.session_state.monthly_allowance -= corrected_total
                    localS.setItem("monthly_allowance", st.session_state.monthly_allowance)
                    st.success(f"{corrected_total:,.0f} 円の支出を記録しました！")
                    st.balloons()
                    # ページをリフレッシュして最新の残高を反映
                    st.rerun()

            except (ValueError, TypeError):
                st.error("AIが金額を数値として正しく認識できませんでした。手動で入力してください。")
                if st.button("手動で支出を記録する"):
                    manual_total = st.number_input("支出した合計金額を手動で入力してください。")
                    st.session_state.monthly_allowance -= manual_total
                    localS.setItem("monthly_allowance", st.session_state.monthly_allowance)
                    st.success(f"{manual_total:,.0f} 円の支出を記録しました！")
                    st.rerun()

        except Exception as e:
            st.error(f"❌ 処理中に予期せぬエラーが発生しました: {e}")

# --- ⑤ サイドバーと、APIキー入力 ---
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

# --- ⑥ メイン処理の、実行 ---
run_allowance_recorder_app(gemini_api_key_input)
