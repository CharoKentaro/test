# ===============================================================
# ★★★ ai_memory_partner_tool.py ＜最後のコード＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime, timedelta, timezone
from streamlit_mic_recorder import mic_recorder

# --- プロンプトや補助関数（省略） ---
SYSTEM_PROMPT_TRUE_FINAL = """..."""
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
            response = model.generate_content([SYSTEM_PROMPT_TRUE_FINAL, processed_text])
            ai_response_text = response.text
        return original_input_display, ai_response_text
    except Exception as e:
        st.error(f"AI処理中に予期せぬエラーが発生しました: {e}")
        return None, None

# ===============================================================
# メインの仕事 - 最後のコード
# ===============================================================
def show_tool(gemini_api_key, localS_object=None):

    prefix = "cc_"
    results_key = f"{prefix}results"
    usage_count_key = f"{prefix}usage_count"
    text_input_key = f"{prefix}text_input" # テキスト入力ウィジェット専用のキー

    # --- セッションの初期化 ---
    if results_key not in st.session_state:
        st.session_state[results_key] = []
    if usage_count_key not in st.session_state:
        st.session_state[usage_count_key] = 0
    if text_input_key not in st.session_state:
        st.session_state[text_input_key] = ""

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★ これが、新しい、入力処理のロジックです ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    
    # マイクとテキストの入力を、まずウィジェットとして定義する
    st.header("❤️ 認知予防ツール", divider='rainbow')
    usage_limit = 3
    is_limit_reached = st.session_state.get(usage_count_key, 0) >= usage_limit
    
    # 処理すべき内容を保持する変数
    content_to_process = None
    
    if is_limit_reached:
        # アンロック・モード
        st.success("🎉 たくさんお話いただき、ありがとうございます！")
        st.info("このツールが、あなたの心を温める一助となれば幸いです。")
        st.warning("お話を続けるには、応援ページで「今日の合言葉」を確認し、入力してください。")
        
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        st.markdown(f'<a href="{portal_url}" target="_blank">応援ページで「今日の合言葉」を確認する →</a>', unsafe_allow_html=True)
        st.divider()

        password_input = st.text_input("ここに「今日の合言葉」を入力してください:", type="password")
        if st.button("お話を続ける"):
            JST = timezone(timedelta(hours=+9))
            today_str = datetime.now(JST).strftime('%Y%m%d')
            secret_word = st.secrets.get("unlock_secret", "")
            correct_password = f"{today_str}-{secret_word}"
            
            if secret_word and password_input == correct_password:
                st.session_state[usage_count_key] = 0
                st.balloons()
                st.success("ありがとうございます！お話を続けましょう。")
                time.sleep(2)
                st.rerun() # ここでのrerunは、モード切替のため安全
            else:
                st.error("合言葉が違うようです。応援ページで、もう一度ご確認ください。")
    else:
        # 通常会話モード
        st.info("下のマイクのボタンを押して、昔の楽しかった思い出や、頑張ったお話など、なんでも自由にお話しください。")
        try:
            remaining_talks = usage_limit - st.session_state.get(usage_count_key, 0)
            st.caption(f"🚀 あと {remaining_talks} 回、お話できます。")
        except: pass 
        
        col1, col2 = st.columns([1, 2])
        with col1:
            audio_info = mic_recorder(start_prompt="🟢 話し始める", stop_prompt="🔴 話を聞いてもらう", key=f'{prefix}mic', format="webm")
        with col2:
            # テキスト入力は、on_changeを使わず、シンプルに定義
            st.text_input("または、ここに文章を入力してEnter...", key=text_input_key)
        
        # --- 入力があったかどうかを判定 ---
        # マイク入力
        if audio_info:
            content_to_process = audio_info['bytes']
        # テキスト入力
        elif st.session_state[text_input_key]:
            # ① 内容をコピーする
            content_to_process = st.session_state[text_input_key]
            # ② ウィジェットの状態を、ただちにクリアする
            st.session_state[text_input_key] = ""

    # ★★★ AIとの対話は、すべてのウィジェット描画が終わった後に行う ★★★
    if content_to_process:
        if not gemini_api_key:
            st.error("サイドバーでGemini APIキーを設定してください。")
        else:
            # ③ コピーした内容で、処理を行う
            original, ai_response = dialogue_with_gemini(content_to_process, gemini_api_key)
            if original and ai_response:
                st.session_state[usage_count_key] += 1
                st.session_state[results_key].insert(0, {"original": original, "response": ai_response})
                # ★★★ もう、rerunはしない ★★★
                st.experimental_rerun() # st.rerunの代替として、より安全な再実行を試みる

    # --- 履歴の表示 ---
    if st.session_state.get(results_key) and not is_limit_reached:
        st.write("---")
        for result in st.session_state[results_key]:
            with st.chat_message("user"): st.write(result['original'])
            with st.chat_message("assistant"): st.write(result['response'])
        if st.button("会話の履歴をクリア", key=f"{prefix}clear_history"):
            st.session_state[results_key] = []
            st.session_state[usage_count_key] = 0
            st.rerun() # ここでのrerunは、ユーザーのアクション起因なので安全
