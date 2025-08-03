import streamlit as st
from streamlit_local_storage import LocalStorage
import time

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★【最終作戦】第六の英雄の、召喚状を、一旦、破棄します ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# これにより、プラットフォームの、不可解な、呪いを、回避します。
from tools import translator_tool, okozukai_recorder_tool, calendar_tool, gijiroku_tool, kensha_no_kioku_tool

# --- アプリの基本設定 (変更なし) ---
st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

# --- サイドバー (最終形態) ---
with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()

    tool_selection = st.radio(
        "利用するツールを選択してください:",
        ("🤝 翻訳ツール", "💰 お小遣い管理", "📅 AI秘書", "📝 議事録作成", "🧠 賢者の記憶", "❤️ 認知予防ツール"),
        key="tool_selection"
    )
    st.divider()

    localS = LocalStorage()
    saved_key = localS.getItem("gemini_api_key")
    gemini_default = saved_key if isinstance(saved_key, str) else ""
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = gemini_default
    with st.expander("⚙️ APIキーの設定", expanded=not st.session_state.gemini_api_key):
        with st.form("api_key_form", clear_on_submit=False):
            st.session_state.gemini_api_key = st.text_input("Gemini APIキー", type="password", value=st.session_state.gemini_api_key)
            col1, col2 = st.columns(2)
            with col1: save_button = st.form_submit_button("💾 保存", use_container_width=True)
            with col2: reset_button = st.form_submit_button("🔄 クリア", use_container_width=True)
    if save_button:
        localS.setItem("gemini_api_key", st.session_state.gemini_api_key, key="storage_api_key_save")
        st.success("キーをブラウザに保存しました！"); time.sleep(1); st.rerun()
    if reset_button:
        localS.setItem("gemini_api_key", None, key="storage_api_key_clear");
        st.session_state.gemini_api_key = ""
        st.success("キーをクリアしました。"); time.sleep(1); st.rerun()
    st.divider()
    st.markdown("""<div style="font-size: 0.9em;"><a href="https://aistudio.google.com/app/apikey" target="_blank">Gemini APIキーの取得はこちら</a></div>""", unsafe_allow_html=True)

# ★★★★★ 『偉大なる、仕分け人』の、最終契約書 ★★★★★
if st.session_state.tool_selection == "🤝 翻訳ツール":
    translator_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
    
elif st.session_state.tool_selection == "💰 お小遣い管理":
    okozukai_recorder_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))

elif st.session_state.tool_selection == "📅 AI秘書":
    calendar_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "📝 議事録作成":
    gijiroku_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "🧠 賢者の記憶":
    kensha_no_kioku_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
    
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★【ちゃろ様の叡智・実装】第六英雄の、記憶喪失を、完全に、治療する ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
elif st.session_state.tool_selection == "❤️ 認知予防ツール":
    
    import google.generativeai as genai
    from streamlit_mic_recorder import mic_recorder

    # --- 英雄が、心に、刻んでいる、魂の、プロンプト ---
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

    # --- 英雄が、振るう、聖なる、対話の、剣 ---
    def dialogue_with_gemini(content_to_process, api_key):
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
            
    # --- ここからが、英雄の、帝国民への、奉仕活動の、全てです ---
    prefix = "cc_"
    storage_key_results = f"{prefix}results"
    
    # ★★★【最重要】新たなる叡智：『聖なる封印』の、導入 ★★★
    storage_key_initialized = f"{prefix}initialized_seal"

    # --- 帰還者の、祝福（The Return Journey）---
    if st.query_params.get("unlocked") == "true":
        st.session_state[f"{prefix}usage_count"] = 0
        st.query_params.clear()

        # ★★★【神の一閃・実装】『聖なる封印』を、意図的に、破棄する ★★★
        if storage_key_initialized in st.session_state:
            del st.session_state[storage_key_initialized]
        
        st.toast("おかえりなさい！またお話できることを、楽しみにしておりました。")
        st.balloons(); time.sleep(1.5); st.rerun()

    # ★★★ 聖なる封印の儀式 (The Sacred Seal Ritual) ★★★
    if storage_key_initialized not in st.session_state:
        retrieved_results = localS.getItem(storage_key_results)
        st.session_state[storage_key_results] = retrieved_results if retrieved_results else []
        st.session_state[storage_key_initialized] = True

    # --- これより先は、封印された、安定した『会話』の世界 ---
    st.header("❤️ 認知予防ツール", divider='rainbow')
    
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
        gemini_api_key = st.session_state.get('gemini_api_key', '')
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
