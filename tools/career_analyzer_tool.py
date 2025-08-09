# ===============================================================
# ★★★ career_analyzer_tool.py ＜AIキャリアアナリスト＞ ★★★
# ===============================================================
import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
import time

# --- プロンプト定義 ---
ANALYSIS_PROMPT = """
あなたは、非常に優秀なキャリアアナリストです。
与えられた求人情報ページのテキストから、以下の項目を正確に、かつ情熱をもって抽出し、分析してください。

# 命令
* 以下の情報を、指定されたJSON形式で厳密に出力してください。
* 情報が見つからない場合は、該当する値に「情報なし」と記述してください。
* 特に「給与・報酬」については、月給、年収、時給など、見つけられる限りの情報を詳細に記述してください。
* JSON以外の、前置きや説明は、絶対に出力しないでください。

# JSON出力形式
{
  "summary": "この求人情報の最も重要なポイントを3行で要約",
  "salary": "給与・報酬に関する情報（例：月給 30万円～50万円、想定年収 450万円～750万円）",
  "required_skills": [
    "必須スキルや経験のリスト項目1",
    "必須スキルや経験のリスト項目2"
  ],
  "preferred_skills": [
    "歓迎されるスキルや経験のリスト項目1",
    "歓迎されるスキルや経験のリスト項目2"
  ],
  "attraction": "この仕事ならではの魅力や、やりがい、得られる経験などを2〜3個の箇条書きで記述"
}
"""

# --- スクレイピングとAI分析を行う関数 ---
def analyze_job_posting(url, api_key):
    try:
        # 1. URLからHTMLを取得
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        with st.spinner("求人ページの情報を読み込んでいます..."):
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 2. HTMLからテキスト情報だけを抽出
            soup = BeautifulSoup(response.content, "html.parser")
            # bodyタグの中のテキストを取得し、余分な空白や改行を整理
            page_text = ' '.join(soup.body.get_text(separator=' ', strip=True).split())

        # 3. テキストをAIに渡して分析させる
        with st.spinner("AIが求人情報を分析・要約しています..."):
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            full_prompt = [ANALYSIS_PROMPT, f"## 分析対象の求人情報テキスト:\n{page_text}"]
            response = model.generate_content(full_prompt)
            
            # 4. AIの応答をJSONとして解析
            # マークダウンの ```json ``` を取り除く
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            analysis_result = json.loads(cleaned_response)

        return analysis_result

    except requests.exceptions.RequestException as e:
        st.error(f"URLの読み込みに失敗しました: {e}")
        return None
    except json.JSONDecodeError:
        st.error("AIからの応答を解析できませんでした。ページの形式が複雑すぎるか、AIの応答形式が正しくない可能性があります。")
        st.code(response.text) # デバッグ用にAIの生応答を表示
        return None
    except Exception as e:
        st.error(f"分析中に予期せぬエラーが発生しました: {e}")
        return None

# --- メイン関数 ---
def show_tool(gemini_api_key):
    st.header("👔 AIキャリアアナリスト", divider='rainbow')
    st.info("求人情報のURLを貼り付けるだけで、AIがその内容を分析・要約します。")

    url = st.text_input("分析したい求人ページのURLを入力してください", placeholder="https://...")

    if st.button("このURLの求人情報を分析する", type="primary", use_container_width=True):
        if not gemini_api_key:
            st.warning("サイドバーからGemini APIキーを設定してください。")
        elif not url:
            st.warning("URLを入力してください。")
        else:
            # 分析を実行し、結果をセッションステートに保存
            result = analyze_job_posting(url, gemini_api_key)
            st.session_state.analysis_result = result
    
    # --- 分析結果の表示 ---
    if 'analysis_result' in st.session_state and st.session_state.analysis_result:
        st.divider()
        st.subheader("🤖 AIによる分析結果")
        result = st.session_state.analysis_result

        # 各項目を美しく表示
        st.markdown("##### 📝 **要約**")
        st.write(result.get("summary", "情報なし"))

        st.markdown("##### 💰 **給与・報酬**")
        st.write(result.get("salary", "情報なし"))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### ✅ **必須スキル**")
            required = result.get("required_skills", [])
            if required:
                for skill in required: st.markdown(f"- {skill}")
            else:
                st.write("情報なし")
        
        with col2:
            st.markdown("##### ✨ **歓迎スキル**")
            preferred = result.get("preferred_skills", [])
            if preferred:
                for skill in preferred: st.markdown(f"- {skill}")
            else:
                st.write("情報なし")

        st.markdown("##### 🚀 **この仕事の魅力**")
        attraction = result.get("attraction", "情報なし")
        # 箇条書きが文字列で返ってきた場合も対応
        if isinstance(attraction, str):
            st.write(attraction)
        elif isinstance(attraction, list):
             for point in attraction: st.markdown(f"- {point}")
        else:
            st.write("情報なし")
