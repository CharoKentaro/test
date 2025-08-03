# ===============================================================
# ★★★ ai_memory_partner_tool.py ＜アルティメット・ギャンビット版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import time
import uuid 
from google.cloud import firestore 
from google.oauth2 import service_account
import json
from streamlit_mic_recorder import mic_recorder

# --- プロンプトや補助関数群（省略） ---
SYSTEM_PROMPT_TRUE_FINAL = """..."""
@st.cache_resource
def init_firestore_client():
    try:
        creds_json_str = st.secrets["firebase_credentials"]
        creds_dict = json.loads(creds_json_str)
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        db = firestore.Client(credentials=credentials)
        return db
    except: return None
def save_history_to_firestore(db, session_id, history):
    try:
        if db and session_id:
            doc_ref = db.collection('conversations').document(session_id)
            doc_ref.set({'history': history})
    except: pass
def load_history_from_firestore(db, session_id):
    try:
        if db and session_id:
            doc_ref = db.collection('conversations').document(session_id)
            doc = doc_ref.get()
            if doc.exists: return doc.to_dict().get('history', [])
    except: return []
    return []
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
# メインの仕事 - アルティメット・ギャンビット
# ===============================================================
def show_tool(gemini_api_key, localS_object): # ★★★ localS を正しく受け取る

    db = init_firestore_client()
    if not db:
        st.error("データベースに接続できません。アプリを再起動してみてください。")
        return

    # --- セッションキー定義 ---
    prefix = "cc_"
    session_id_key = f"{prefix}session_id"
    results_key = f"{prefix}results"
    usage_count_key = f"{prefix}usage_count"
    
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★ 「一時的な通行証」を使った、聖別の儀 ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    if session_id_key not in st.session_state:
        # LocalStorageから通行証(session_id)を探す
        retrieved_session_id = localS_object.getItem(session_id_key)
        
        if retrieved_session_id:
            # 通行証があった場合 = 帰還ユーザー
            st.session_state[session_id_key] = retrieved_session_id
            history = load_history_from_firestore(db, retrieved_session_id)
            st.session_state[results_key] = history
            st.session_state[usage_count_key] = 0 # 帰還者は無条件で0回に
            st.toast("おかえりなさい！応援ありがとうございます！")
            
            # ★★★ 使用済みの通行証は、即座に破棄する ★★★
            localS_object.removeItem(session_id_key)
        else:
            # 通行証がなかった場合 = 新規ユーザー
            st.session_state[session_id_key] = str(uuid.uuid4())
            st.session_state[results_key] = []
            st.session_state[usage_count_key] = 0

    st.header("❤️ 認知予防ツール", divider='rainbow')

    usage_limit = 3
    is_limit_reached = st.session_state.get(usage_count_key, 0) >= usage_limit
    
    if is_limit_reached:
        # ★★★ 旅立ちの儀 ★★★
        st.success("🎉 たくさんお話いただき、ありがとうございます！")
        st.info("このツールが、あなたの心を温める一助となれば幸いです。\n\n応援ページへ移動することで、またお話を続けることができます。")

        current_session_id = st.session_state[session_id_key]
        
        # 1. 履歴をFirebaseに保存する
        save_history_to_firestore(db, current_session_id, st.session_state[results_key])
        # 2. 通行証をLocalStorageに書き込む
        localS_object.setItem(session_id_key, current_session_id)
        
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        button_html = f'<a href="{portal_url}" target="_self" style="display: inline-block; padding: 0.75rem 1rem; background-color: #28a745; color: white; text-decoration: none; border-radius: 0.5rem; font-weight: bold; text-align: center; width: 95%;">応援ページに移動して、お話を続ける</a>'
        st.markdown(button_html, unsafe_allow_html=True)
    
    else:
        # 通常のアプリ動作
        st.info("下のマイクのボタンを押して、昔の楽しかった思い出や、頑張ったお話など、なんでも自由にお話しください。")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(usage_count_key, 0)} 回、お話できます。")
        
        col1, col2 = st.columns([1, 2])
        with col1: audio_info = mic_recorder(start_prompt="🟢 話し始める", stop_prompt="🔴 話を聞いてもらう", key=f'{prefix}mic', format="webm")
        with col2: text_input = st.text_input("または、ここに文章を入力してEnter...", key=f"{prefix}text_input")
            
        content_to_process = None
        if audio_info: content_to_process = audio_info['bytes']
        elif text_input: content_to_process = text_input

        if content_to_process:
            if not gemini_api_key:
                st.error("サイドバーでGemini APIキーを設定してください。")
            else:
                original, ai_response = dialogue_with_gemini(content_to_process, gemini_api_key)
                if original and ai_response:
                    st.session_state[usage_count_key] += 1
                    st.session_state[results_key].insert(0, {"original": original, "response": ai_response})
                    st.rerun()

    if st.session_state.get(results_key):
        st.write("---")
        for result in st.session_state[results_key]:
            with st.chat_message("user"): st.write(result['original'])
            with st.chat_message("assistant"): st.write(result['response'])
        if st.button("会話の履歴をクリア", key=f"{prefix}clear_history"):
            st.session_state[results_key] = []
            st.session_state[usage_count_key] = 0
            save_history_to_firestore(db, st.session_state[session_id_key], [])
            st.rerun()
