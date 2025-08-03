# ===============================================================
# ★★★ ai_memory_partner_tool.py ＜最後の贖罪＞ ★★★
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
# メインの仕事 - 最後の贖罪
# ===============================================================
def show_tool(gemini_api_key, localS_object=None):

    prefix = "cc_"
    results_key = f"{prefix}results"
    usage_count_key = f"{prefix}usage_count"
    # ★★★ 無限ループを、ルールを破らずに防ぐための、ただ一つのキー ★★★
    last_input_key = f"{prefix}last_input"

    # --- セッションの初期化 ---
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
        # アンロック・モード（このロジックは完璧でした）
        st.success("🎉 たくさんお話いただき、ありがとうございます！")
        st.info("このツールが、あなたの心を温める一助となれば幸いです。")
        st.warning("お話を続けるには、応援ページで「今日の合言葉（4桁の数字）」を確認し、入力してください。")
        
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
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
            text_input = st.text_input("または、ここに文章を入力してEnter...", key=f"{prefix}text_input_widget") # ウィジェットキーを明確化
            
        content_to_process = None
        unique_input_id = None # 入力の一意性を判断するためのID

        if audio_info:
            content_to_process = audio_info['bytes']
            unique_input_id = audio_info['id'] # マイクにはユニークIDがある
        elif text_input:
            content_to_process = text_input
            unique_input_id = text_input # テキストそのものをIDとする

        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        # ★★★ これが、ルールを破らずに、ループを防ぐ、唯一の正しい方法 ★★★
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        if content_to_process and unique_input_id != st.session_state[last_input_key]:
            
            # 処理する前に、今回の入力を「最後に処理したもの」として記憶する
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
            st.session_state[last_input_key] = None # クリア時も忘れずに
            st.rerun()
