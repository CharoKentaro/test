import streamlit as st
from google.api_core.client_options import ClientOptions
from google.cloud import vision
import google.generativeai as genai
from streamlit_local_storage import LocalStorage
import json
from PIL import Image, ImageOps
import io

# --- ① アプリの基本設定 ---
st.set_page_config(
    page_title="レシートデータ化くん (一点突破・最終決戦)",
    page_icon="🔥"
)

# --- ② ローカルストレージの準備 ---
try:
    localS = LocalStorage()
except Exception as e:
    st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。エラー詳細: {e}")
    st.stop()

# --- ③ Geminiに渡す、魂のプロンプト（変更なし）---
GEMINI_PROMPT = """
あなたは、OCRで読み取られたレシートのテキストデータを解析し、構造化する、世界最高の経理AIです。
これから渡されるテキストは、レシートをOCRで読み取った「生のテキスト」です。改行や誤字が含まれる可能性があります。
以下の、最も重要なルールと思考プロセスに従って、テキスト全体を注意深く分析し、必要な情報を完璧に抽出してください。

# 最重要ルール
1.  **キーワードと金額は、同じ行にあるとは限りません。**
    *   キーワード（例：「合計」）の**すぐ下の行**に、金額が書かれていることが非常に多いです。常に、複数行にまたがる関係性を考慮してください。
2.  **店名の抽出:** テキストの最上部にある文字列が、最も店名である可能性が高いです。
3.  **日付の抽出:** 「年」「月」「日」「/」などの記号を含む、日付らしい文字列を探してください。
4.  **金額情報の抽出:**
    *   「合計」「会計」「御会計」を探し、その近くにある数値を「合計金額」とします。
    *   「お預り」「預り」を探し、その近くにある数値を「お預り金額」とします。
    *   「お釣り」「釣銭」を探し、その近くにある数値を「お釣り金額」とします。
    *   **もし、キーワードが見つからなくても、文脈から判断してください。** 例えば、レシートの最後に単独で書かれている「¥〇〇」や「〇〇円」は、合計金額である可能性が極めて高いです。
5.  **出力形式:**
    *   抽出した結果を、必ず以下のJSON形式で出力してください。
    *   数値は、数字のみを抽出してください（円やカンマは不要）。
    *   値が見つからない場合は、正直に "不明" と記載してください。
    *   JSON以外の、前置きや説明は、絶対に出力しないでください。

{
  "store_name": "ここに抽出した店名",
  "purchase_date": "ここに抽出した日付",
  "total_amount": "ここに抽出した合計金額の数値",
  "tendered_amount": "ここに抽出したお預り金額の数値",
  "change_amount": "ここに抽出したお釣り金額の数値"
}
"""

# --- ④ メインの処理を実行する関数 ---
def run_final_battle_app(vision_api_key, gemini_api_key):
    st.title("🔥 レシートデータ化くん")
    st.subheader("【一点突破・最終決戦仕様】")

    uploaded_file = st.file_uploader(
        "処理したいレシート画像を、ここにアップロードしてください。", 
        type=['png', 'jpg', 'jpeg']
    )

    if st.button("⬆️ このレシートを解析する"):
        if not all([uploaded_file, vision_api_key, gemini_api_key]):
            st.warning("画像と、2種類のAPIキーがすべて設定されているか確認してください。")
            st.stop()

        try:
            # ★★★ ここが、最後の、希望 ★★★
            # STEP 0: 人間の知恵（Python）で、AIのために、最高のお膳立てをする
            with st.spinner("STEP 0/3: AIのために、画像を最高の状態に処理しています..."):
                image = Image.open(uploaded_file).convert('L') # グレースケール化
                # 白黒二値化の閾値。128を基準に調整する可能性がある
                threshold = 128
                image = image.point(lambda x: 0 if x < threshold else 255, '1')
                
                # Streamlitで表示するために、画像を保存
                st.image(image, caption="AIが読み取る、白黒二値化された画像", width=300)

                # APIに渡すために、画像をバイトデータに変換
                buf = io.BytesIO()
                image.save(buf, format='PNG')
                processed_image_bytes = buf.getvalue()

            # STEP 1: Vision API（目）が、お膳立てされた画像を、読む
            with st.spinner("STEP 1/3: AI（目）が、お膳立てされた画像を読んでいます..."):
                client_options = ClientOptions(api_key=vision_api_key)
                client = vision.ImageAnnotatorClient(client_options=client_options)
                vision_image = vision.Image(content=processed_image_bytes)
                response = client.text_detection(image=vision_image)
                raw_text = response.text_annotations[0].description if response.text_annotations else ""
                if response.error.message: st.error(f"Vision APIエラー: {response.error.message}"); st.stop()
            
            # STEP 2: Gemini（頭脳）が、最終判断
            with st.spinner("STEP 2/3: AI（頭脳）が、最終結論を出しています..."):
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                gemini_response = model.generate_content([GEMINI_PROMPT, "---レシート生テキスト---", raw_text])
                cleaned_json_str = gemini_response.text.strip().replace("```json", "").replace("```", "")
                extracted_data = json.loads(cleaned_json_str)

            st.success("🎉 解析が完了しました！")
            st.divider()
            
            # 結果表示
            st.text_input("店名", value=extracted_data.get("store_name", "不明"))
            st.text_input("日付", value=extracted_data.get("purchase_date", "不明"))
            st.text_input("合計金額", value=extracted_data.get("total_amount", "不明"))
            st.text_input("お預り金額", value=extracted_data.get("tendered_amount", "不明"))
            st.text_input("お釣り", value=extracted_data.get("change_amount", "不明"))

            with st.expander("🤖 AIチームの作業記録を見る"):
                st.subheader("【STEP 1】AI（目）が読み取った生データ")
                st.text_area("", value=raw_text, height=200)
                st.subheader("【STEP 2】AI（頭脳）が最終的に納品したJSONデータ")
                st.json(extracted_data)

        except Exception as e:
            st.error(f"❌ 処理中に予期せぬエラーが発生しました: {e}")

# --- ⑤ サイドバーと、APIキー入力 ---
with st.sidebar:
    st.header("⚙️ API設定")
    saved_vision_key = localS.getItem("vision_api_key")
    vision_api_key_input = st.text_input(
        "1. Vision APIキー（目）", 
        type="password", 
        value=saved_vision_key if isinstance(saved_vision_key, str) else ""
    )
    if st.button("Visionキーを記憶"):
        localS.setItem("vision_api_key", vision_api_key_input)
        st.success("Vision APIキーを記憶しました！")

    saved_gemini_key = localS.getItem("gemini_api_key")
    gemini_api_key_input = st.text_input(
        "2. Gemini APIキー（頭脳）", 
        type="password", 
        value=saved_gemini_key if isinstance(saved_gemini_key, str) else ""
    )
    if st.button("Geminiキーを記憶"):
        localS.setItem("gemini_api_key", gemini_api_key_input)
        st.success("Gemini APIキーを記憶しました！")

# --- ⑥ メイン処理の、実行 ---
run_final_battle_app(vision_api_key_input, gemini_api_key_input)
