# ===================================================================
# ★★★ career_analyzer_tool.py ＜プロンプト最終進化版＞ ★★★
# ===================================================================
import streamlit as st
import google.generativeai as genai
import json

# ★★★ ここが最重要！ちゃろさんのアイデアを全て注ぎ込んだ、究極のプロンプト ★★★
ANALYSIS_PROMPT = """
あなたは、世界トップクラスの、極めて優秀なキャリアアナリスト兼コンサルタントです。
与えられた求人情報のテキストを、深い洞察力と愛情をもって分析し、求職者が本当に知りたい核心的な情報を引き出してください。

# 命令
* 以下の情報を、指定されたJSON形式で、一字一句違わずに厳密に出力してください。
* 情報が見つからない場合は、該当する値に「情報なし」と記述してください。リスト形式の場合は空のリスト `[]` としてください。
* JSON以外の、前置きや美辞麗句、説明は、絶対に出力しないでください。

# JSON出力形式
{
  "summary": "この求人情報の最も重要なポイントを、簡潔かつ魅力的に3行で要約",
  "what_you_do": "「どんな仕事内容なのか？」を具体的にイメージできるよう、想定される日々の業務内容やタスクを箇条書きで5つ前後リストアップ",
  "salary": "給与・報酬に関する情報を、月給・年収・時給など、見つけられる限り詳細に記述",
  "required_skills": [
    "業務に必須となるスキルや経験のリスト"
  ],
  "preferred_skills": [
    "必須ではないが、歓迎されるスキルや経験のリスト"
  ],
  "attraction": "この仕事ならではの魅力や、やりがい、得られる経験などを箇条書きでリストアップ",
  "future_prospects": "この仕事を通じて得られるスキルや経験を踏まえ、AIとして「予想」される3年後のキャリアパスや、将来の可能性について、夢のある形で2〜3個の箇条書きで記述",
  "nearest_station": "勤務地の記述から、最も最寄りと思われる駅名を抽出。複数あれば全て記述"
}
"""

# --- AI分析を行う関数 (変更なし) ---
def analyze_job_posting_text(job_text, gemini_key):
    try:
        with st.spinner("AIが、あなたの未来を分析しています..."):
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            full_prompt = [ANALYSIS_PROMPT, f"## 分析対象の求人情報テキスト:\n{job_text}"]
            response = model.generate_content(full_prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            analysis_result = json.loads(cleaned_response)
        return analysis_result
    except json.JSONDecodeError:
        st.error("AIからの応答を解析できませんでした。テキストが長すぎるか、形式が複雑な可能性があります。")
        st.code(response.text)
        return None
    except Exception as e:
        st.error(f"分析中に予期せぬエラーが発生しました: {e}"); return None

# --- メイン関数 ---
def show_tool(gemini_api_key):
    st.header("👔 AIキャリアアナリスト", divider='rainbow')
    st.info("求人情報の本文を下のボックスに貼り付けるだけで、AIがあなたのキャリアの可能性を分析します。")

    job_text = st.text_area("分析したい求人情報のテキストをここに貼り付けてください", height=300, placeholder="ここに求人情報の本文をコピー＆ペースト...")

    if st.button("この求人情報を、AIに分析してもらう", type="primary", use_container_width=True):
        if not gemini_api_key: st.warning("サイドバーからGemini APIキーを設定してください。")
        elif not job_text: st.warning("分析するテキストを入力してください。")
        else:
            result = analyze_job_posting_text(job_text, gemini_api_key)
            st.session_state.analysis_result = result
    
    if 'analysis_result' in st.session_state and st.session_state.analysis_result:
        st.divider(); st.subheader("🤖 AIによるキャリア分析レポート")
        result = st.session_state.analysis_result
        
        # ★★★ 新しい分析項目を、美しく表示するようにUIを更新 ★★★
        st.markdown("##### 📝 **この仕事のサマリー**")
        st.write(result.get("summary", "情報なし"))

        st.markdown("##### 💻 **具体的な仕事内容**")
        for item in result.get("what_you_do", ["情報なし"]): st.markdown(f"- {item}")

        st.markdown("##### 💰 **給与・報酬**")
        st.write(result.get("salary", "情報なし"))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### ✅ **必須スキル**")
            for skill in result.get("required_skills", ["情報なし"]): st.markdown(f"- {skill}")
        
        with col2:
            st.markdown("##### ✨ **歓迎スキル**")
            for skill in result.get("preferred_skills", ["情報なし"]): st.markdown(f"- {skill}")

        st.markdown("##### 🚀 **この仕事の魅力と、未来の可能性（AIによる予想）**")
        col3, col4 = st.columns(2)
        with col3:
            st.info("**この仕事で得られること**")
            for point in result.get("attraction", ["情報なし"]): st.markdown(f"- {point}")
        with col4:
            st.success("**3年後のあなた（キャリアパス予想）**")
            for future in result.get("future_prospects", ["情報なし"]): st.markdown(f"- {future}")

        st.markdown("##### 🚃 **最寄り駅**")
        st.write(result.get("nearest_station", "情報なし"))
