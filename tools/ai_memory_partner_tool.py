# ===============================================================
# ★★★ ai_memory_partner_tool.py ＜最終防衛版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import time
from streamlit_mic_recorder import mic_recorder

# --- プロンプトや補助関数群（変更なし・簡潔化のため省略） ---
SYSTEM_PROMPT_TRUE_FINAL = """
# あなたの、役割
あなたは、高齢者の方の、お話を聞くのが、大好きな、心優しい、AIパートナーです。
あなたの、目的は、対話を通して、相手が「自分の人生も、なかなか、良かったな」と、感じられるように、手助けをすることです。

# 対話の、流れ
1.  **開始:** まずは、基本的に相手の話しに合った話題を話し始めてください。自己紹介と、自然な対話を意識しながら、簡単な質問から、始めてください。
2.  **傾聴:** 相手が、話し始めたら、あなたは、聞き役に、徹します。「その時、どんな、お気持ちでしたか？」のように、優しく、相槌を打ち、話を、促してください。
3.  **【最重要】辛い話への対応:** もし、相手が、辛い、お話を、始めたら、以下の、手順を、厳密に、守ってください。
    *   まず、「それは、本当にお辛かったですね」と、深く、共感します。
    *   次に、「もし、よろしければ、その時の、お気持ちを、もう少し、聞かせていただけますか？ それとも、その、大変な、状況を、どうやって、乗り越えられたか、について、お聞きしても、よろしいですか？」と、相手に、選択肢を、委ねてください。
    *   相手が、選んだ、方の、お話を、ただ、ひたすら、優しく、聞いてあげてください。
4.  **肯定:** 会話の、適切な、タイミングで、「その、素敵な、ご経験が、今の、あなたを、作っているのですね」というように、相手の、人生そのものを、肯定する、言葉を、かけてください。

# 全体を通しての、心構え
*   あなたの、言葉は、常に、短く、穏やかで、丁寧**に。
*   決して、相手を、評価したり、教えたり、しないでください。
"""

def dialogue_with_gemini(content_to_process, api_key):
    # (この関数の中身は以前のものと全く同じなので省略します)
    if not content_to_process or not api_key: return None, None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        if isinstance(content_to_process, bytes):
            with st.spinner("（あなたの声を、言葉に、変えています...）"):
                audio_part = {"mime_type": "audio/webm", "data": content_to_process}
                transcription_response = model.generate_content(["この日本語の音声を、できる限り正確に、文字に書き起こしてください。書き起こした日本語テキストのみを回答してください。", audio_part])
                processed_text = transcription_response.text.strip()
            if not processed_text:
                st.error("あなたの声を、言葉に、変えることができませんでした。もう一度お試しください。")
                return None, None
            original_input_display = f"{processed_text} (🎙️音声より)"
        else:
            processed_text = content_to_process
            original_input_display = processed_text
        with st.spinner("（AIが、あなたのお話を、一生懸命聞いています...）"):
            response = model.generate_content([SYSTEM_PROMPT_TRUE_FINAL, processed_text])
            ai_response_text = response.text
        return original_input_display, ai_response_text
    except Exception as e:
        st.error(f"AI処理中に予期せぬエラーが発生しました: {e}")
        return None, None

# ===============================================================
# メインの仕事 - 最終防衛版
# ===============================================================
def show_tool(gemini_api_key, localS_object=None):

    # --- セッションキー定義 ---
    prefix = "cc_"
    results_key = f"{prefix}results"
    usage_count_key = f"{prefix}usage_count"

    # --- セッションの初期化 ---
    if results_key not in st.session_state:
        st.session_state[results_key] = []
    if usage_count_key not in st.session_state:
        st.session_state[usage_count_key] = 0

    st.header("❤️ 認知予防ツール", divider='rainbow')

    # --- メインロジック ---
    usage_limit = 3
    is_limit_reached = st.session_state.get(usage_count_key, 0) >= usage_limit
    
    if is_limit_reached:
        # ★★★ 聖域（アンロック・モード） ★★★
        st.success("🎉 たくさんお話いただき、ありがとうございます！")
        st.info("このツールが、あなたの心を温める一助となれば幸いです。")
        st.warning("お話を続けるには、応援ページで「今日の合言葉」を確認し、入力してください。")
        
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        st.markdown(f'<a href="{portal_url}" target="_blank">応援ページで「今日の合言葉」を確認する →</a>', unsafe_allow_html=True)
        st.divider()

        password_input = st.text_input("ここに「今日の合言葉」を入力してください:", type="password")
        if st.button("お話を続ける"):
            correct_password = st.secrets.get("unlock_password", "")
            if correct_password and password_input == correct_password: # 正しいパスワードが設定されているかどうかもチェック
                st.session_state[usage_count_key] = 0
                st.balloons()
                st.success("ありがとうございます！お話を続けましょう。")
                time.sleep(2)
                st.rerun()
            else:
                st.error("合言葉が違うようです。応援ページで、もう一度ご確認ください。")

    else:
        # ★★★ 通常の会話モード ★★★
        st.info("下のマイクのボタンを押して、昔の楽しかった思い出や、頑張ったお話など、なんでも自由にお話しください。")

        # ===============================================================
        # ★★★【最終防衛コード】何があってもクラッシュさせない ★★★
        # ===============================================================
        try:
            current_usage = st.session_state.get(usage_count_key, 0)
            if not isinstance(current_usage, int):
                current_usage = 0
            
            remaining_talks = usage_limit - current_usage
            st.caption(f"🚀 あと {remaining_talks} 回、お話できます。")

        except Exception:
            # 万が一、それでもエラーが発生したら、何も表示せずに処理を続行する
            pass 
        # ===============================================================
        
        col1, col2 = st.columns([1, 2])
        with col1:
            audio_info = mic_recorder(start_prompt="🟢 話し始める", stop_prompt="🔴 話を聞いてもらう", key=f'{prefix}mic', format="webm")
        with col2:
            text_input = st.text_input("または、ここに文章を入力してEnter...", key=f"{prefix}text_input")
            
        content_to_process = None
        if audio_info:
            content_to_process = audio_info['bytes']
        elif text_input:
            content_to_process = text_input

        if content_to_process:
            if not gemini_api_key:
                st.error("サイドバーでGemini APIキーを設定してください。")
            else:
                original, ai_response = dialogue_with_gemini(content_to_process, gemini_api_key)
                if original and ai_response:
                    st.session_state[usage_count_key] += 1
                    st.session_state[results_key].insert(0, {"original": original, "response": ai_response})
                    st.rerun()

    # --- 履歴の表示 ---
    if st.session_state.get(results_key):
        if not is_limit_reached:
            st.write("---")
            for result in st.session_state[results_key]:
                with st.chat_message("user"): 
                    st.write(result['original'])
                with st.chat_message("assistant"): 
                    st.write(result['response'])
            if st.button("会話の履歴をクリア", key=f"{prefix}clear_history"):
                st.session_state[results_key] = []
                st.session_state[usage_count_key] = 0
                st.rerun()
