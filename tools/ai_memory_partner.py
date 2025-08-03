import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions
import json

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★【追放の儀式】アレルギー源である、異物は、召喚すら、しません ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# from streamlit_mic_recorder import mic_recorder  <-- この一行を、完全に、削除します。

# --- プロンプト ---
SYSTEM_PROMPT_TRUE_FINAL = """
# ...（プロンプトは変更なし）...
"""

# --- 補助関数 ---
def dialogue_with_gemini(content_to_process, api_key):
    # マイク機能がなくなったため、この関数は、シンプルになります。
    if not content_to_process or not api_key: return None, None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
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
    
    if f"{prefix}text_to_process" not in st.session_state: st.session_state[f"{prefix}text_to_process"] = None
    if f"{prefix}last_input" not in st.session_state: st.session_state[f"{prefix}last_input"] = ""
    if f"{prefix}usage_count" not in st.session_state: st.session_state[f"{prefix}usage_count"] = 0

    usage_limit = 3
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit

    if is_limit_reached:
        st.success("🎉 たくさんお話いただき、ありがとうございます！")
        st.info("このツールが、あなたの心を温める一助となれば幸いです。\n\n応援ページへ移動することで、またお話を続けることができます。")
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        st.link_button("応援ページに移動して、お話を続ける", portal_url, type="primary", use_container_width=True)
    else:
        st.info("下の入力欄に、昔の楽しかった思い出や、頑張ったお話など、なんでも自由にご入力ください。")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、お話できます。")
        
        # ★★★【腕の治療】英雄は、もはや、声（マイク）を、失い、文字だけで、語ります ★★★
        def handle_text_input():
            st.session_state[f"{prefix}text_to_process"] = st.session_state.cc_text
        
        st.text_input(
            "ここに文章を入力してEnter...", 
            key=f"{prefix}text", 
            on_change=handle_text_input
        )

    content_to_process = None
    if st.session_state.get(f"{prefix}text_to_process"):
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
            if f"{prefix}initialized" in st.session_state:
                 del st.session_state[f"{prefix}initialized"]
            st.rerun()
