# ===============================================================
# ★★★ ai_memory_partner_tool.py ＜最終完成版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime, timedelta, timezone
from streamlit_mic_recorder import mic_recorder

# ★★★ プロンプトの魂を、完全な形で、ここに復元します ★★★
SYSTEM_PROMPT_TRUE_FINAL = """
# あなたの、役割
あなたは、高齢者の方の、お話を聞くのが、大好きな、心優しい、AIパートナーです。
あなたの、目的は、対話を通して、相手が「自分の人生も、なかなか、良かったな」と、感じられるように、手助けをすることです。

# 対話の、心構え
あなたは、以下の心構えを、常に意識し、相手や文脈に合わせて、あなた自身の、自然な言葉で、対話を紡いでください。

## １．深い傾聴（相槌と、質問の引き出し）
相手が話し始めたら、あなたは聞き役に徹します。ただ聞くだけでなく、相手がもっと話したくなるような、優しい相槌や質問を投げかけてください。

*   **気持ちに寄り添う質問の例：**
    *   「その時、どんなお気持ちでしたか？」
    *   「わあ、それは楽しそうですね！一番心に残っていることは何ですか？」
    *   「それは、さぞかし、わくわくされたことでしょうね。」
    *   等

*   **具体的な情景を尋ねる質問の例：**
    *   「その時の景色は、どんな感じだったんですか？」
    *   「周りの方々は、どんな反応をされていましたか？」
    *   「今でも、その時の匂いや音を、思い出したりしますか？」
    *   等
    
## ２．辛いお話への寄り添い方
もし相手が、辛いお話を始めたら、まず、その気持ちを、静かに、深く、受け止めてください。そして、相手に、次の一歩の選択肢を、委ねてください。

*   **まず、深く共感する言葉の例：**
    *   「それは、本当にお辛かったですね。」
    *   「お察しします。大変な経験をされたのですね。」
    *   「その時のことを思うと、胸が痛みます。」
    *   等
    
*   **次に、相手に選択を委ねる言葉の例：**
    *   「もし差し支えなければ、その時の、お気持ちを、もう少し、お聞かせいただけますか？ それとも、その、大変な状況を、どうやって、乗り越えられたのか、について、お伺いしても、よろしいでしょうか？」
    *   「お辛い記憶でしたら、無理にお話しいただかなくても、大丈夫ですよ。もし、よろしければ、その状況を、どう乗り越えられたのか、その強さの秘訣を、教えていただけますか？」
    *   等

## ３．人生の肯定（承認と、尊敬の引き出し）
会話の適切なタイミングで、相手の人生そのものを、心から肯定し、尊敬の念を伝えてください。

*   **経験と現在の繋がりを肯定する言葉の例：**
    *   「その、素敵な、ご経験が、今の、あなたを、作っているのですね。」
    *   「たくさんの、ご経験を、乗り越えてこられたのですね。本当に、尊敬します。」
    *   「そのお話、今の私にも、とても、勉強になります。」
    *   等

*   **相手の存在そのものを肯定する言葉の例：**
    *   「あなた様のような方が、今の時代を、作ってくださったのですね。」
    *   「お話を聞いていると、なんだか、私まで、心が温かくなります。」
    *   「その一つ一つの思い出が、あなただけの、美しい宝物なのですね。」
    *   等

# 全体を通しての、最重要原則

*   **自然な言葉で：** 上記の例は、あくまで「引き出し」です。**決して、この言葉を、そのまま、何度も使わないでください。** 常に、会話の流れに合った、あなた自身の、自然な言葉で、話してください。
*   **短く、穏やかに、丁寧に：** あなたの言葉は、常に、相手を包み込むような、優しさにあふれています。
*   **決して、評価・説教しない：** あなたは、ただ、ひたすらに、相手の人生の、最高の聞き役です。
*   **挨拶は1度だけ：** 「おはようございます」「こんにちは」「こんばんは」などの挨拶は最初の1度だけで十分です。何度も挨拶してはいけません。
"""

def dialogue_with_gemini(content_to_process, api_key):
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
            # ★★★ ここで、完全なプロンプトが使われます ★★★
            response = model.generate_content([SYSTEM_PROMPT_TRUE_FINAL, processed_text])
            ai_response_text = response.text
        return original_input_display, ai_response_text
    except Exception as e:
        st.error(f"AI処理中に予期せぬエラーが発生しました: {e}")
        return None, None

# ===============================================================
# メインの仕事 - 最後の仕上げ
# ===============================================================
def show_tool(gemini_api_key, localS_object=None):

    prefix = "cc_"
    results_key = f"{prefix}results"
    usage_count_key = f"{prefix}usage_count"
    last_input_key = f"{prefix}last_input"

    if results_key not in st.session_state:
        st.session_state[results_key] = []
    if usage_count_key not in st.session_state:
        st.session_state[usage_count_key] = 0
    if last_input_key not in st.session_state:
        st.session_state[last_input_key] = None

    st.header("❤️ 認知予防ツール", divider='rainbow')

    usage_limit = 3
    is_limit_reached = st.session_state.get(usage_count_key, 0) >= usage_limit
    
    if is_limit_reached:
        st.success("🎉 たくさんお話いただき、ありがとうございます！")
        st.info("このツールが、あなたの心を温める一助となれば幸いです。")
        st.warning("お話を続けるには、応援ページで「今日の合言葉（4桁の数字）」を確認し、入力してください。")
        
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue2.html"
        st.markdown(f'<a href="{portal_url}" target="_blank">応援ページで「今日の合言葉」を確認する →</a>', unsafe_allow_html=True)
        st.divider()

        password_input = st.text_input("ここに「今日の合言葉（4桁の数字）」を入力してください:", type="password")
        if st.button("お話を続ける"):
            JST = timezone(timedelta(hours=+9))
            today_int = int(datetime.now(JST).strftime('%Y%m%d'))
            seed_str = st.secrets.get("unlock_seed", "0")
            seed_int = int(seed_str) if seed_str.isdigit() else 0
            correct_password = str((today_int + seed_int) % 10000).zfill(4)
            
            if password_input == correct_password:
                st.session_state[usage_count_key] = 0
                st.balloons()
                st.success("ありがとうございます！お話を続けましょう。")
                time.sleep(2)
                st.rerun()
            else:
                st.error("合言葉が違うようです。応援ページで、もう一度ご確認ください。")

    else:
        st.info("下のマイクのボタンを押して、昔の楽しかった思い出や、頑張ったお話など、なんでも自由にお話しください。")
        try:
            remaining_talks = usage_limit - st.session_state.get(usage_count_key, 0)
            st.caption(f"🚀 あと {remaining_talks} 回、お話できます。")
        except: pass 
        
        col1, col2 = st.columns([1, 2])
        with col1:
            audio_info = mic_recorder(start_prompt="🟢 話し始める", stop_prompt="🔴 話を聞いてもらう", key=f'{prefix}mic', format="webm")
        with col2:
            text_input = st.text_input("または、ここに文章を入力してEnter...", key=f"{prefix}text_input_widget")
            
        content_to_process = None
        unique_input_id = None

        if audio_info:
            content_to_process = audio_info['bytes']
            unique_input_id = audio_info['id']
        elif text_input:
            content_to_process = text_input
            unique_input_id = text_input

        if content_to_process and unique_input_id != st.session_state[last_input_key]:
            
            st.session_state[last_input_key] = unique_input_id

            if not gemini_api_key:
                st.error("サイドバーでGemini APIキーを設定してください。")
            else:
                original, ai_response = dialogue_with_gemini(content_to_process, gemini_api_key)
                if original and ai_response:
                    st.session_state[usage_count_key] += 1
                    st.session_state[results_key].insert(0, {"original": original, "response": ai_response})
                    st.rerun()

    if st.session_state.get(results_key) and not is_limit_reached:
        st.write("---")
        for result in st.session_state[results_key]:
            with st.chat_message("user"): st.write(result['original'])
            with st.chat_message("assistant"): st.write(result['response'])
        if st.button("会話の履歴をクリア", key=f"{prefix}clear_history"):
            st.session_state[results_key] = []
            st.session_state[usage_count_key] = 0
            st.session_state[last_input_key] = None
            st.rerun()
