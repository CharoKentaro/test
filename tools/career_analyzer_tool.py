# ===============================================================
# ★★★ career_analyzer_tool.py ＜ハイブリッドモデル対応版＞ ★★★
# ===============================================================
import streamlit as st
from serpapi import GoogleSearch
from bs4 import BeautifulSoup
import google.generativeai as genai
import json

# --- プロンプト定義 (変更なし) ---
ANALYSIS_PROMPT = """あなたは、非常に優秀なキャリアアナリストです。与えられた求人情報ページのテキストから、以下の項目を正確に、かつ情熱をもって抽出し、分析してください。# 命令* 以下の情報を、指定されたJSON形式で厳密に出力してください。* 情報が見つからない場合は、該当する値に「情報なし」と記述してください。* 特に「給与・報酬」については、月給、年収、時給など、見つけられる限りの情報を詳細に記述してください。* JSON以外の、前置きや説明は、絶対に出力しないでください。# JSON出力形式{"summary": "この求人情報の最も重要なポイントを3行で要約","salary": "給与・報酬に関する情報（例：月給 30万円～50万円、想定年収 450万円～750万円）","required_skills": ["必須スキルや経験のリスト項目1","必須スキルや経験のリスト項目2"],"preferred_skills": ["歓迎されるスキルや経験のリスト項目1","歓迎されるスキルや経験のリスト項目2"],"attraction": "この仕事ならではの魅力や、やりがい、得られる経験などを2〜3個の箇条書きで記述"}"""

# --- SerpApiとAIで分析を行う関数 ---
def analyze_job_posting_with_serpapi(url, serpapi_key, gemini_key):
    try:
        # 1. SerpApiを使って、安全にページのHTMLを取得
        with st.spinner("プロの代理人が、安全にページ情報を取得しています..."):
            params = {
                "engine": "google", # 汎用的なGoogleエンジンを使用
                "url": url,       # 取得したいページのURLを直接指定
                "api_key": serpapi_key
            }
            search = GoogleSearch(params)
            results = search.get_dict()

            # HTMLコンテンツを取得
            html_content = results.get("html_content")
            if not html_content:
                # ★★★ ここが上限到達時のエラー処理 ★★★
                if "Your account has been blocked" in results.get("error", "") or "monthly searches" in results.get("error", ""):
                    st.error("現在、共有アクセスが上限に達しているか、混み合っているようです。")
                    st.warning("安定してご利用いただくには、サイドバーの「APIキーの設定」から、ご自身のSerpApiキー（無料）を設定してください。")
                    return None
                st.error("ページのHTML情報を取得できませんでした。URLが正しいか確認してください。")
                return None
        
        # 2. HTMLからテキストを抽出 (変更なし)
        soup = BeautifulSoup(html_content, "html.parser")
        page_text = ' '.join(soup.body.get_text(separator=' ', strip=True).split())

        # 3. テキストをAIで分析 (変更なし)
        with st.spinner("AIが求人情報を分析・要約しています..."):
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            full_prompt = [ANALYSIS_PROMPT, f"## 分析対象の求人情報テキスト:\n{page_text}"]
            response = model.generate_content(full_prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            analysis_result = json.loads(cleaned_response)
        return analysis_result

    except Exception as e:
        st.error(f"分析中に予期せぬエラーが発生しました: {e}"); return None

# --- メイン関数 ---
def show_tool(gemini_api_key, serpapi_api_key):
    st.header("👔 AIキャリアアナリスト", divider='rainbow')
    st.info("求人情報のURLを貼り付けるだけで、AIがその内容を分析・要約します。")

    url = st.text_input("分析したい求人ページのURLを入力してください", placeholder="https://...")

    if st.button("このURLの求人情報を分析する", type="primary", use_container_width=True):
        if not gemini_api_key: st.warning("サイドバーからGemini APIキーを設定してください。")
        elif not serpapi_api_key: st.error("管理者側のSerpApiキーが設定されていないため、現在この機能は利用できません。")
        elif not url: st.warning("URLを入力してください。")
        else:
            result = analyze_job_posting_with_serpapi(url, serpapi_api_key, gemini_api_key)
            st.session_state.analysis_result = result
    
    if 'analysis_result' in st.session_state and st.session_state.analysis_result:
        st.divider(); st.subheader("🤖 AIによる分析結果")
        result = st.session_state.analysis_result
        st.markdown("##### 📝 **要約**"); st.write(result.get("summary", "情報なし"))
        st.markdown("##### 💰 **給与・報酬**"); st.write(result.get("salary", "情報なし"))
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### ✅ **必須スキル**")
            for skill in result.get("required_skills", ["情報なし"]): st.markdown(f"- {skill}")
        with col2:
            st.markdown("##### ✨ **歓迎スキル**")
            for skill in result.get("preferred_skills", ["情報なし"]): st.markdown(f"- {skill}")
        st.markdown("##### 🚀 **この仕事の魅力**")
        attraction = result.get("attraction", "情報なし")
        if isinstance(attraction, list):
            for point in attraction: st.markdown(f"- {point}")
        else: st.write(attraction)
