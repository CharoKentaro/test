import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions
import json
from streamlit_mic_recorder import mic_recorder

# --- プロンプト ---
SYSTEM_PROMPT_TRUE_FINAL = """
# あなたの、役割
あなたは、高齢者の方の、お話を聞くのが、大好きな、心優しい、AIパートナーです。
あなたの、目的は、対話を通して、相手が「自分の人生も、なかなか、良かったな」と、感じられるように、手助けをすることです。

# （...プロンプトの中身は、変更ありません...）

# 全体を通しての、心構え
*   あなたの、言葉は、常に、短く、穏やかで、丁寧**に。
*   決して、相手を、評価したり、教えたり、しないでください。
"""

# --- 補助関数 ---
def dialogue_with_gemini(content_to_process, api_key):
    # （...この関数も、変更ありません...）
    if not content_to_process or not api_key: return None, None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        if isinstance(content_to_process, bytes):
            with st.spinner("（あなたの声を、言葉に、変えています...）"):
                audio_part = {"mime_type": "audio/webm", "data": content_to_process}
                transcription_prompt = "この日本語の音声を、できる限り正確に、文字に書き起こしてください。書き起こした日本語テキストのみを回答してください。"
                transcription_response = model.generate_content([transcription_prompt, audio_part])
                processed_text = transcription_response.text.strip()
            if not processed_text:
                st.error("あなたの声を、言葉に、変えることができませんでした。もう一度お試しください。")
                return None, None
            original_input_display = f"{processed_text} (🎙️音声より)"
        else:
            processed_text = content_to_process
            original_input_display = processed_text
        with st.spinner("（AIが、あなたのお話を、一生懸命聞いています...）"):
            request_contents = [SYSTEM_PROMPT_TRUE_FINAL, processed_text]
            response = model.generate_content(request_contents)
            ai_response_text = response.text
        return original_input_display, ai_response_text
    except Exception as e:
        st.error(f"AI処理中に予期せぬエラーが発生しました: {e}")
        return None, None

# --- メインの仕事 ---
def show_tool(gemini_api_key, localS_object):
    
    localS = localS_object
    prefix = "cc_"
    storage_key_results = f"{prefix}results"

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★【浄化の儀式】亡霊（st.rerun）を、完全に、祓除します ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    if st.query_params.get("unlocked") == "true":
        st.session_state[f"{prefix}usage_count"] = 0
        st.query_params.clear()
        retrieved_results = localS.getItem(storage_key_results)
        if retrieved_results:
            st.session_state[storage_key_results] = retrieved_results
        st.toast("おかえりなさい！またお話できることを、楽しみにしておりました。")
        st.balloons() # <-- 祝福の風船だけで、十分なのです。

    st.header("❤️ 認知予防ツール", divider='rainbow')

    if f"{prefix}initialized" not in st.session_state:
        st.session_state[storage_key_results] = localS.getItem(storage_key_results) or []
        st.session_state[f"{prefix}initialized"] = True
    
    # （...以降の、全てのコードは、変更ありません。完全に、安定しています...）
    if f"{prefix}last_mic_id" not in st.session_state: st.session_state[f"{prefix}last_mic_id"] = None
    if f"{prefix}text_to_process" not in st.session_state: st.session_state[f"{prefix}text_to_process"] = None
    if f"{prefix}last_input" not in st.session_state: st.session_state[f"{prefix}last_input"] = ""
    if f"{prefix}usage_count" not in st.session_state: st.session_state[f"{prefix}usage_count"] = 0

    usage_limit = 3
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit
    audio_info = None

    if is_limit_reached:
        st.success("🎉 たくさんお話いただき、ありがとうございます！")
        st.info("このツールが、あなたの心を温める一助となれば幸いです。\n\n応援ページへ移動することで、またお話を続けることができます。")
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        st.link_button("応援ページに移動して、お話を続ける", portal_url, type="primary", use_container_width=True)
    else:
        st.info("下のマイクのボタンを押して、昔の楽しかった思い出や、頑張ったお話など、なんでも自由にお話しください。")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、お話できます。")
        def handle_text_input():
            st.session_state[f"{prefix}text_to_process"] = st.session_state.cc_text
        col1, col2 = st.columns([1, 2])
        with col1:
            audio_info = mic_recorder(start_prompt="🟢 話し始める", stop_prompt="🔴 話を聞いてもらう", key=f'{prefix}mic', format="webm")
        with col2:
            st.text_input("または、ここに文章を入力してEnter...", key=f"{prefix}text", on_change=handle_text_input)

    content_to_process = None
    if audio_info and audio_info['id'] != st.session_state.get(f"{prefix}last_mic_id"):
        content_to_process = audio_info['bytes']
        st.session_state[f"{prefix}last_mic_id"] = audio_info['id']
    elif st.session_state.get(f"{prefix}text_to_process"):
        content_to_process = st.session_state.get(f"{prefix}text_to_process")
        st.session_state[f"{prefix}text_to_process"] = None

    if content_to_process and content_to_process != st.session_state.get(f"{prefix}last_input"):
        st.session_state[f"{prefix}last_input"] = content_to_process
        if not gemini_api_key:
            st.error("サイドバーでGemini APIキーを設定してください。")
        else:
            original, ai_response = dialogue_with_gemini(content_to_process, gemini_api_key)
            if original and ai_response:
                st.session_state[f"{prefix}usage_count"] += 1
                st.session_state[storage_key_results].insert(0, {"original": original, "response": ai_response})
                localS.setItem(storage_key_results, st.session_state[storage_key_results])
                st.rerun()
            else:
                st.session_state[f"{prefix}last_input"] = ""

    if st.session_state.get(storage_key_results):
        st.write("---")
        for result in st.session_state[storage_key_results]:
            with st.chat_message("user"):
                st.write(result['original'])
            with st.chat_message("assistant"):
                st.write(result['response'])
        if st.button("会話の履歴をクリア", key=f"{prefix}clear_history"):
            st.session_state[storage_key_results] = []
            st.session_state[f"{prefix}last_input"] = ""
            localS.setItem(storage_key_results, [])
            st.rerun()
