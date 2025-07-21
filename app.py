import streamlit as st
from google.api_core.client_options import ClientOptions
from google.cloud import vision
import google.generativeai as genai
from streamlit_local_storage import LocalStorage
import json
import re

# --- ① アプリの基本設定 ---
st.set_page_config(
    page_title="レシートデータ化くん (最終形態)",
    page_icon="🏆"
)

# --- ② ローカルストレージの準備 ---
try:
    localS = LocalStorage()
except Exception as e:
    st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。エラー詳細: {e}")
    st.stop()

# --- ③ 人間の知性（Pythonロジック）で使うキーワード ---
KEYWORDS = {
    "total": ["合計", "会計", "御会計", "総計", "TOTAL"],
    "tendered": ["お預り", "預り", "お預かり", "TENDERED", "支払"],
    "change": ["お釣り", "おつり", "釣銭", "CHANGE"]
}

# --- ④ Geminiに渡す、魂のプロンプト（最終判断用）---
GEMINI_PROMPT = """
あなたは、経理のプロフェッショナルです。
これから、部下（Python）がレシートをOCRで読み取り、キーワードで絞り込んだ「候補の行」をあなたに報告します。
あなたの仕事は、その報告書を元に、最終的な数値を判断し、JSON形式で出力することです。

# 思考プロセス
1.  各候補の行の中から、金額と思われる数値を抽出してください。
2.  数値は、円マーク(¥)やカンマ(,)が含まれている場合がありますが、数字の部分だけを抜き出してください。
3.  もし候補が複数ある場合は、レシートの文脈上、最も妥当なものを一つだけ選んでください。
4.  候補がない、または、数値が見つからない場合は、正直に "不明" と記載してください。
5.  最終的なアウトプットは、以下のJSON形式以外、絶対に出力しないでください。

# 報告書フォーマット
{
  "total_candidates": ["（合計の候補行1）", "（合計の候補行2）"],
  "tendered_candidates": ["（お預りの候補行）"],
  "change_candidates": ["（お釣りの候補行）"]
}

# あなたの最終成果物（JSON）
{
  "store_name": "（店名候補から判断した店名）",
  "purchase_date": "（日付候補から判断した日付）",
  "total_amount": "（合計の候補から判断した最終的な合計金額）",
  "tendered_amount": "（お預りの候補から判断した最終的なお預り金額）",
  "change_amount": "（お釣りの候補から判断した最終的なお釣り金額）"
}
"""

# --- ⑤ メインの処理を実行する関数 ---
def run_hybrid_app(vision_api_key, gemini_api_key):
    st.title("🏆 レシートデータ化くん")
    st.subheader("【ハイブリッドAI搭載・最終形態】")
    st.info("支出に関わるデータを、AIと人間の知能で協力して、正確に抽出します。")

    uploaded_file = st.file_uploader(
        "処理したいレシート画像を、ここにアップロードしてください。", type=['png', 'jpg', 'jpeg']
    )

    if st.button("⬆️ このレシートを解析する"):
        # ...（入力チェックは省略）...

        try:
            # --- STEP 1: Vision API（目）が文字を認識する ---
            with st.spinner("STEP 1/3: 専門家AI（目）がレシートの文字を読み取っています..."):
                # ...（Vision APIの呼び出しコードは前回と同じ）...
                client_options = ClientOptions(api_key=vision_api_key)
                client = vision.ImageAnnotatorClient(client_options=client_options)
                content = uploaded_file.getvalue()
                image = vision.Image(content=content)
                response = client.text_detection(image=image)
                raw_text = response.text_annotations[0].description if response.text_annotations else ""

            # --- STEP 2: 人間の知性（Python）が候補を絞り込む ---
            with st.spinner("STEP 2/3: 人間の知性（Python）が、重要な手がかりを探しています..."):
                lines = raw_text.split('\n')
                candidates = {
                    "total_candidates": [],
                    "tendered_candidates": [],
                    "change_candidates": [],
                    "store_name_candidates": [lines[0]] if lines else [], # 暫定的に1行目を店名候補
                    "date_candidates": [line for line in lines if re.search(r'\d{4}年|\d{1,2}月|\d{1,2}日|/', line)]
                }
                for line in lines:
                    for key, keywords in KEYWORDS.items():
                        for keyword in keywords:
                            if keyword in line:
                                candidates[f"{key}_candidates"].append(line)
                                break
            
            # --- STEP 3: Gemini（頭脳）が最終判断を下す ---
            with st.spinner("STEP 3/3: 専門家AI（頭脳）が、最終的な結論を出しています..."):
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Pythonからの報告書を作成
                report_for_gemini = json.dumps(candidates, ensure_ascii=False, indent=2)
                
                gemini_response = model.generate_content([GEMINI_PROMPT, "部下からの報告書です。", report_for_gemini])
                
                cleaned_json_str = gemini_response.text.strip().replace("```json", "").replace("```", "")
                extracted_data = json.loads(cleaned_json_str)

            st.success("🎉 AIチームによる解析が完了しました！")
            st.divider()

            # --- 結果の表示 ---
            st.header("🤖 解析結果")
            st.text_input("店名", value=extracted_data.get("store_name", "不明"))
            st.text_input("日付", value=extracted_data.get("purchase_date", "不明"))
            st.text_input("合計金額", value=extracted_data.get("total_amount", "不明"))
            st.text_input("お預り金額", value=extracted_data.get("tendered_amount", "不明"))
            st.text_input("お釣り", value=extracted_data.get("change_amount", "不明"))

            with st.expander("🤖 AIチームの作業記録を見る"):
                st.subheader("【STEP 1】AI（目）が読み取った生データ")
                st.text_area("", value=raw_text, height=200)
                st.subheader("【STEP 2】人間の知性（Python）による候補の絞り込み")
                st.json(candidates)
                st.subheader("【STEP 3】AI（頭脳）への最終報告書")
                st.code(report_for_gemini, language="json")
                st.subheader("【最終成果物】AI（頭脳）からの最終納品物")
                st.json(extracted_data)

        except Exception as e:
            st.error(f"❌ 処理中に予期せぬエラーが発生しました: {e}")

# --- ⑥ サイドバーと、APIキー入力 ---
with st.sidebar:
    # ...（サイドバーのコードは前回と同じ）...
    st.header("⚙️ API設定")
    saved_vision_key = localS.getItem("vision_api_key")
    vision_api_key_input = st.text_input("1. Vision APIキー（目）", type="password", value=saved_vision_key if isinstance(saved_vision_key, str) else "")
    if st.button("Visionキーを記憶"):
        localS.setItem("vision_api_key", vision_api_key_input)
        st.success("Vision APIキーを記憶しました！")
    saved_gemini_key = localS.getItem("gemini_api_key")
    gemini_api_key_input = st.text_input("2. Gemini APIキー（頭脳）", type="password", value=saved_gemini_key if isinstance(saved_gemini_key, str) else "")
    if st.button("Geminiキーを記憶"):
        localS.setItem("gemini_api_key", gemini_api_key_input)
        st.success("Gemini APIキーを記憶しました！")

# --- ⑦ メイン処理の、実行 ---
run_hybrid_app(vision_api_key_input, gemini_api_key_input)
