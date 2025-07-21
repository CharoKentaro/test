import streamlit as st
from google.api_core.client_options import ClientOptions
from google.cloud import vision
import google.generativeai as genai
from streamlit_local_storage import LocalStorage
import json

# --- ① アプリの基本設定 ---
st.set_page_config(
    page_title="レシートデータ化くん (デュアルAI実験版)",
    page_icon="🤖"
)

# --- ② ローカルストレージの準備 ---
try:
    localS = LocalStorage()
except Exception as e:
    st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。エラー詳細: {e}")
    st.stop()

# --- ③ Geminiに渡す、魂のプロンプト ---
# この指示書を改善していくことが、今後の精度向上の鍵となります
GEMINI_PROMPT = """
あなたは、OCRで読み取られたレシートのテキストデータを解析し、構造化する超高精度な経理アシスタントAIです。
以下のルールと思考プロセスに従って、与えられたテキストから「店名」「日付」「合計金額」を完璧に抽出してください。

# 厳格なルール
1.  **入力テキストの特性を理解する:** このテキストはOCR（光学文字認識）によって生成されたものであり、誤字（例：「合計」が「合言」になる）や、不要な情報が混入している可能性があります。
2.  **店名の抽出:**
    *   テキストの最上部にある、会社名や店舗名らしき文字列を「店名」とします。
    *   「〇〇ストア」「〇〇商店」「〇〇スーパー」などのキーワードは、強いヒントになります。
3.  **日付の抽出:**
    *   「年」「月」「日」「/」などの記号を含む、日付らしい文字列を探してください。
    *   「2024/07/21」「2024年7月21日」などの形式が一般的です。
    *   もし年が省略されていても、月日を抽出してください。
4.  **合計金額の抽出:**
    *   「合計」「御会計」「会計」「総計」「Total」といったキーワードを探してください。**OCRによる誤字の可能性を考慮し、多少の間違いは許容してください。**
    *   これらのキーワードの近くにある、最も大きな数値を「合計金額」と判断してください。
    *   レシートには「小計」「お預り」「お釣り」など、多くの数値が含まれますが、それらは無視してください。
5.  **出力形式:**
    *   抽出した結果を、必ず以下のJSON形式で出力してください。
    *   値が見つからない場合は、正直に "不明" と記載してください。
    *   JSON以外の、前置きや説明、言い訳は、絶対に出力しないでください。

{
  "store_name": "ここに抽出した店名",
  "purchase_date": "ここに抽出した日付",
  "total_amount": "ここに抽出した合計金額"
}
"""


# --- ④ メインの処理を実行する関数 ---
def run_dual_ai_app(vision_api_key, gemini_api_key):
    st.title("🧾 レシートデータ化くん")
    st.subheader("【デュアルAI実験版】")
    st.info("レシート画像をアップロードすると、AIが「店名」「日付」「合計金額」を抽出します。")

    uploaded_file = st.file_uploader(
        "処理したいレシート画像を、ここにアップロードしてください。",
        type=['png', 'jpg', 'jpeg']
    )

    if st.button("⬆️ このレシートを解析する"):
        if uploaded_file is None:
            st.warning("画像がアップロードされていません。")
            st.stop()
        
        if not vision_api_key or not gemini_api_key:
            st.warning("サイドバーで、Vision APIとGemini API、両方のキーを入力し、保存してください。")
            st.stop()

        try:
            # --- STEP 1: Vision API（目）が文字を認識する ---
            with st.spinner("STEP 1/2: 専門家AI（目）が、レシートの文字を正確に読み取っています..."):
                client_options = ClientOptions(api_key=vision_api_key)
                client = vision.ImageAnnotatorClient(client_options=client_options)
                content = uploaded_file.getvalue()
                image = vision.Image(content=content)
                response = client.text_detection(image=image)
                
                if response.error.message:
                    st.error(f"Vision APIエラー: {response.error.message}")
                    st.stop()

                if not response.text_annotations:
                    st.warning("この画像からは文字を検出できませんでした。")
                    st.stop()
                
                # 抽出した全てのテキストを一つの文字列として保持
                raw_text = response.text_annotations[0].description
            
            # --- STEP 2: Gemini（頭脳）が内容を理解・清書する ---
            with st.spinner("STEP 2/2: 専門家AI（頭脳）が、内容を理解し、重要な情報だけを抜き出しています..."):
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-1.5-flash') # 高速なモデルを使用
                
                # 生テキストと指示書をGeminiに渡す
                gemini_response = model.generate_content([raw_text, GEMINI_PROMPT])
                
                # Geminiからの返答（JSON形式のはず）を解析
                # "```json" と "```" を取り除く処理を追加
                cleaned_json_str = gemini_response.text.strip().replace("```json", "").replace("```", "")
                extracted_data = json.loads(cleaned_json_str)

            st.success("🎉 AIによる解析が完了しました！")
            st.divider()

            # --- 結果の表示（私たちが合意した、最強の安全装置）---
            st.header("🤖 AIの解析結果")
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("✅ AIの清書")
                st.text_input("店名", value=extracted_data.get("store_name", "不明"), key="store_name")
                st.text_input("日付", value=extracted_data.get("purchase_date", "不明"), key="purchase_date")
                st.text_input("合計金額", value=extracted_data.get("total_amount", "不明"), key="total_amount")

            with col2:
                st.subheader("📄 AIが読み取った生データ")
                st.text_area("（AIは、このテキストを元に判断しました）", value=raw_text, height=350)
                
        except json.JSONDecodeError:
            st.error("🚨 Geminiからの応答を解析できませんでした。AIが予期せぬ形式で返答したようです。")
            st.write("AIからの直接の応答:")
            st.code(gemini_response.text)
        except Exception as e:
            st.error(f"❌ 処理中に予期せぬエラーが発生しました: {e}")

# --- ⑤ サイドバーと、APIキー入力 ---
with st.sidebar:
    st.header("⚙️ API設定")
    st.info("2種類のAI専門家を連携させるため、2つのキーが必要です。")
    
    # Vision API Key
    saved_vision_key = localS.getItem("vision_api_key")
    vision_api_key_input = st.text_input(
        "1. Vision APIキー（目）", type="password", 
        value=saved_vision_key if isinstance(saved_vision_key, str) else ""
    )
    if st.button("Visionキーを記憶"):
        localS.setItem("vision_api_key", vision_api_key_input)
        st.success("Vision APIキーを記憶しました！")

    # Gemini API Key
    saved_gemini_key = localS.getItem("gemini_api_key")
    gemini_api_key_input = st.text_input(
        "2. Gemini APIキー（頭脳）", type="password",
        value=saved_gemini_key if isinstance(saved_gemini_key, str) else ""
    )
    if st.button("Geminiキーを記憶"):
        localS.setItem("gemini_api_key", gemini_api_key_input)
        st.success("Gemini APIキーを記憶しました！")

# --- ⑥ メイン処理の、実行 ---
run_dual_ai_app(vision_api_key_input, gemini_api_key_input)
