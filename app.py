import streamlit as st
import google.generativeai as genai
from streamlit_local_storage import LocalStorage
import json
from PIL import Image
import io

# --- ① アプリの基本設定 ---
st.set_page_config(
    page_title="レシートデータ化くん (逆転の発想版)",
    page_icon="💡"
)

# --- ② ローカルストレージの準備 ---
try:
    localS = LocalStorage()
except Exception as e:
    st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。エラー詳細: {e}")
    st.stop()

# --- ③ Geminiに渡す、魂のプロンプト（画像解析用）---
GEMINI_PROMPT = """
あなたは、与えられたレシートの**画像を直接解析する**、超高精度なデータ抽出AIです。
あなたの使命は、レシートの画像の中から「店名」「日付」「合計金額」の3つの情報だけを完璧に抽出し、指定されたJSON形式で出力することです。

# 厳格なルール
1.  **画像を、あなたの目で、直接、見てください。**
2.  **店名の抽出:** 画像の最上部やロゴなどから、店名や会社名を特定してください。
3.  **日付の抽出:** 「年」「月」「日」「/」などの記号を含む、日付を探してください。
4.  **合計金額の抽出:**
    *   「合計」「御会計」「会計」「総計」「Total」といったキーワードを探してください。
    *   これらのキーワードの近くにある、**最も重要な数値（通常は最も大きいか、最後に出てくる）**を「合計金額」として抽出してください。
    *   「小計」「お預り」「お釣り」は、合計金額ではありません。絶対に間違えないでください。
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
def run_gemini_direct_app(gemini_api_key):
    st.title("💡 レシートデータ化くん")
    st.subheader("【逆転の発想版】")
    st.info("レシート画像をアップロードすると、AIが直接画像を解析して、重要な情報を抽出します。")

    uploaded_file = st.file_uploader(
        "処理したいレシート画像を、ここにアップロードしてください。",
        type=['png', 'jpg', 'jpeg']
    )

    if st.button("⬆️ このレシートを解析する"):
        if uploaded_file is None:
            st.warning("画像がアップロードされていません。")
            st.stop()
        
        if not gemini_api_key:
            st.warning("サイドバーで、Gemini APIキーを入力し、保存してください。")
            st.stop()

        try:
            with st.spinner("🧠 AIが、レシートの画像を直接見て、内容を解析中です..."):
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-1.5-flash-latest') # 最新の高速な画像解析モデル
                
                # アップロードされた画像を開く
                image_bytes = uploaded_file.getvalue()
                img = Image.open(io.BytesIO(image_bytes))

                # 画像と指示書をGeminiに渡す
                gemini_response = model.generate_content([GEMINI_PROMPT, img])
                
                # Geminiからの返答（JSON形式のはず）を解析
                cleaned_json_str = gemini_response.text.strip().replace("```json", "").replace("```", "")
                extracted_data = json.loads(cleaned_json_str)

            st.success("🎉 AIによる解析が完了しました！")
            st.divider()

            # --- 結果の表示 ---
            st.header("🤖 AIの解析結果")
            st.text_input("店名", value=extracted_data.get("store_name", "不明"))
            st.text_input("日付", value=extracted_data.get("purchase_date", "不明"))
            st.text_input("合計金額", value=extracted_data.get("total_amount", "不明"))
            
            with st.expander("JSONデータを確認する"):
                st.json(extracted_data)
                
        except json.JSONDecodeError:
            st.error("🚨 Geminiからの応答を解析できませんでした。AIが予期せぬ形式で返答したようです。")
            st.write("AIからの直接の応答:")
            st.code(gemini_response.text)
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
run_gemini_direct_app(gemini_api_key_input)
