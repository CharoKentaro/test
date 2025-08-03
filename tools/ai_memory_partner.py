import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions
import json
from streamlit_mic_recorder import mic_recorder

# --- プロンプト ---
SYSTEM_PROMPT_TRUE_FINAL = """
# ...（プロンプトは変更なし）...
"""

# --- 補助関数 ---
def dialogue_with_gemini(content_to_process, api_key):
    # ...（この関数も変更なし）...
    return original_input_display, ai_response_text

# --- メインの仕事 ---
def show_tool(gemini_api_key, localS_object):
    
    localS = localS_object
    prefix = "cc_"
    storage_key_results = f"{prefix}results"

    if st.query_params.get("unlocked") == "true":
        st.session_state[f"{prefix}usage_count"] = 0
        st.query_params.clear()
        retrieved_results = localS.getItem(storage_key_results)
        if retrieved_results:
            st.session_state[storage_key_results] = retrieved_results
        st.toast("おかえりなさい！またお話できることを、楽しみにしておりました。")
        st.balloons()

    st.header("❤️ 認知予防ツール", divider='rainbow')

    if f"{prefix}initialized" not in st.session_state:
        st.session_state[storage_key_results] = localS.getItem(storage_key_results) or []
        st.session_state[f"{prefix}initialized"] = True
    
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
        st.info("下のボタンを押して、昔の楽しかった思い出や、頑張ったお話など、なんでも自由にお話しください。")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、お話できます。")
        
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        # ★★★【聖杯の、封印】危険な、武器を、折りたたみメニューに、封印します ★★★
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        with st.expander("マイクで話す、または、文章を、入力する", expanded=True):
            def handle_text_input():
                st.session_state[f"{prefix}text_to_process"] = st.session_state.cc_text
            
            # 聖杯（マイク）と、テキスト入力は、この、聖域の、中でだけ、姿を現します。
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
            # 創生の記憶もリセット
            if f"{prefix}initialized" in st.session_state:
                 del st.session_state[f"{prefix}initialized"]
            st.rerun()
