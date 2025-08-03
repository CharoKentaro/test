# ===============================================================
# ★★★ ai_memory_partner_tool.py ＜最終決戦仕様＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import time
import uuid 
from google.cloud import firestore 
from google.oauth2 import service_account
import json
from streamlit_mic_recorder import mic_recorder

# --- プロンプトや補助関数（変更なしなので、コードを省略） ---
SYSTEM_PROMPT_TRUE_FINAL = """...""" # この中身は同じ
@st.cache_resource
def init_firestore_client():
    try:
        creds_json_str = st.secrets["firebase_credentials"]
        creds_dict = json.loads(creds_json_str)
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        db = firestore.Client(credentials=credentials)
        return db
    except Exception as e:
        st.error(f"保管庫への接続に失敗しました: {e}")
        return None
def save_history_to_firestore(db, session_id, history):
    if db and session_id:
        try:
            doc_ref = db.collection('conversations').document(session_id)
            doc_ref.set({'history': history})
        except Exception as e:
            st.warning(f"履歴の保存に失敗しました: {e}")
def load_history_from_firestore(db, session_id):
    if db and session_id:
        try:
            doc_ref = db.collection('conversations').document(session_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict().get('history', [])
            else:
                return []
        except Exception as e:
            st.error(f"履歴の読み込みに失敗しました: {e}")
            return []
    return []
def dialogue_with_gemini(content_to_process, api_key):
    # (この関数の中身は以前のものと全く同じなので省略します)
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

# ===============================================================
# メインの仕事 - 最終決戦仕様
# ===============================================================
def show_tool(gemini_api_key, localS_object=None):

    db = init_firestore_client()
    if not db:
        st.error("データベースに接続できません。アプリを再起動してみてください。")
        return

    prefix = "cc_"
    session_id_key = f"{prefix}session_id"
    results_key = f"{prefix}results"
    
    st.header("❤️ 認知予防ツール", divider='rainbow')

    if "initialized" not in st.session_state:
        query_params = st.query_params.to_dict()
        retrieved_session_id = query_params.get("session_id")

        if retrieved_session_id:
            st.session_state[session_id_key] = retrieved_session_id
            st.session_state[results_key] = load_history_from_firestore(db, retrieved_session_id)
            # URLから合鍵を削除して、リロード時の再読み込みを防ぐ
            st.query_params.clear()
            st.toast("おかえりなさい！お話の続きを始めましょう。")
        else:
            st.session_state[session_id_key] = str(uuid.uuid4())
            st.session_state[results_key] = []
        
        st.session_state["initialized"] = True

    if f"{prefix}last_mic_id" not in st.session_state: st.session_state[f"{prefix}last_mic_id"] = None
    if f"{prefix}text_to_process" not in st.session_state: st.session_state[f"{prefix}text_to_process"] = None
    if f"{prefix}last_input" not in st.session_state: st.session_state[f"{prefix}last_input"] = ""
    if f"{prefix}usage_count" not in st.session_state:
        history = st.session_state.get(results_key, [])
        st.session_state[f"{prefix}usage_count"] = len([item for item in history if 'original' in item])


    usage_limit = 3
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit
    
    audio_info = None

    if is_limit_reached:
        st.success("🎉 たくさんお話いただき、ありがとうございます！")
        st.info("このツールが、あなたの心を温める一助となれば幸いです。\n\n応援ページへ移動することで、またお話を続けることができます。")

        current_session_id = st.session_state.get(session_id_key)
        portal_url_base = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        portal_url_with_key = f"{portal_url_base}?session_id={current_session_id}"

        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        # ★★★ ここが、最後の武器です！st.link_button を使わない！ ★★★
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        
        # JavaScriptを埋め込んだ、ただのHTMLリンクを生成します。
        # これにより、ブラウザに「このページのURLを書き換えなさい」と直接命令します。
        button_html = f'''
        <a href="{portal_url_with_key}" target="_self" style="
            display: inline-block; 
            padding: 0.75rem 1rem; 
            background-color: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 0.25rem; 
            font-weight: bold;
            text-align: center;
            width: 95%;
        ">
            応援ページに移動して、お話を続ける
        </a>
        '''
        # st.markdownを使って、HTMLを画面に表示します
        st.markdown(button_html, unsafe_allow_html=True)
        
    else:
        # この部分は変更なし
        st.info("下のマイクのボタンを押して、昔の楽しかった思い出や、頑張ったお話など、なんでも自由にお話しください。")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、お話できます。")
        def handle_text_input():
            st.session_state[f"{prefix}text_to_process"] = st.session_state.get(f"{prefix}text", "")
        col1, col2 = st.columns([1, 2])
        with col1:
            audio_info = mic_recorder(start_prompt="🟢 話し始める", stop_prompt="🔴 話を聞いてもらう", key=f'{prefix}mic', format="webm")
        with col2:
            st.text_input("または、ここに文章を入力してEnter...", key=f"{prefix}text", on_change=handle_text_input)

    # --- 以降の処理（content_to_process, AIとの対話, 表示部分）は変更なし ---
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
                st.session_state[results_key].insert(0, {"original": original, "response": ai_response})
                current_session_id = st.session_state.get(session_id_key)
                save_history_to_firestore(db, current_session_id, st.session_state[results_key])
                st.rerun()
            else:
                st.session_state[f"{prefix}last_input"] = ""
    if st.session_state.get(results_key):
        st.write("---")
        for result in st.session_state[results_key]:
            with st.chat_message("user"): st.write(result['original'])
            with st.chat_message("assistant"): st.write(result['response'])
        if st.button("会話の履歴をクリア（このセッションのみ）", key=f"{prefix}clear_history"):
            st.session_state[results_key] = []
            st.session_state[f"{prefix}last_input"] = ""
            st.session_state[f"{prefix}usage_count"] = 0
            current_session_id = st.session_state.get(session_id_key)
            save_history_to_firestore(db, current_session_id, [])
            st.success("会話の履歴をクリアしました。"); time.sleep(1); st.rerun()
