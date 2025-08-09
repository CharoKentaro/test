# ===============================================================
# ★★★ career_analyzer_tool.py ＜コピペ方式・最終完成版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import json

# --- プロンプト定義 (変更なし) ---
ANALYSIS_PROMPT = """あなたは、非常に優秀なキャリアアナリストです。与えられた求人情報ページのテキストから、以下の項目を正確に、かつ情熱をもって抽出し、分析してください。# 命令* 以下の情報を、指定されたJSON形式で厳密に出力してください。* 情報が見つからない場合は、該当する値に「情報なし」と記述してください。* 特に「給与・報酬」については、月給、年収、時給など、見つけられる限りの情報を詳細に記述してください。* JSON以外の、前置きや説明は、絶対に出力しないでください。# JSON出力形式{"summary": "この求人情報の最も重要なポイントを3行で要約","salary": "給与・報酬に関する情報（例：月給 30万円～50万円、想定年収 450万円～750万円）","required_skills": ["必須スキルや経験のリスト項目1","必須スキルや経験のリスト項目2"],"preferred_skills": ["歓迎されるスキルや経験のリスト項目1","歓迎されるスキルや経験のリスト項目2"],"attraction": "この仕事ならではの魅力や、やりがい、得られる経験などを2〜3個の箇条書きで記述"}"""

# --- AI分析を行う関数 ---
def analyze_job_posting_text(job_text, gemini_key):
    try:
        with st.spinner("AIが求人情報を分析・要約しています..."):
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            full_prompt = [ANALYSIS_PROMPT, f"## 分析対象の求人情報テキスト:\n{job_text}"]
            response = model.generate_content(full_prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            analysis_result = json.loads(cleaned_response)
        return analysis_result
    except json.JSONDecodeError:
        st.error("AIからの応答を解析できませんでした。")
        st.code(response.text)
        return None
    except Exception as e:
        st.error(f"分析中に予期せぬエラーが発生しました: {e}"); return None

# --- メイン関数 ---
def show_tool(gemini_api_key):
    st.header("👔 AIキャリアアナリスト", divider='rainbow')
    st.info("求人情報の本文を下のボックスに貼り付けるだけで、AIが内容を分析・要約します。")

    # ★★★ URL入力欄から、複数行テキスト入力欄に変更 ★★★
    job_text = st.text_area("分析したい求人情報のテキストをここに貼り付けてください", height=250, placeholder="ここに求人情報の本文をコピー＆ペースト...")

    if st.button("この内容で分析する", type="primary", use_container_width=True):
        if not gemini_api_key: st.warning("サイドバーからGemini APIキーを設定してください。")
        elif not job_text: st.warning("分析するテキストを入力してください。")
        else:
            result = analyze_job_posting_text(job_text, gemini_api_key)
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
        attraction = result.get("attraction", [])
        if isinstance(attraction, list):
            for point in attraction: st.markdown(f"- {point}")
        else: st.write(str(attraction))
