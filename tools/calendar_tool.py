import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime
import urllib.parse
import pytz

import time # sleepのために追加

# ===============================================================
# 補助関数 (変更なし)
# ===============================================================
def create_google_calendar_url(details):
    try:
        jst = pytz.timezone('Asia/Tokyo')
        start_time_jst = jst.localize(datetime.fromisoformat(details['start_time']))
        end_time_jst = jst.localize(datetime.fromisoformat(details['end_time']))
        start_time_utc = start_time_jst.astimezone(pytz.utc).strftime('%Y%m%dT%H%M%SZ')
        end_time_utc = end_time_jst.astimezone(pytz.utc).strftime('%Y%m%dT%H%M%SZ')
        dates = f"{start_time_utc}/{end_time_utc}"
    except (ValueError, KeyError):
        dates = ""
    base_url = "https://www.google.com/calendar/render?action=TEMPLATE"
    params = {
        "text": details.get('title', ''),
        "dates": dates,
        "location": details.get('location', ''),
        "details": details.get('details', '')
    }
    return f"{base_url}&{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"

# ===============================================================
# 専門家のメインの仕事（応援システムを戴冠）
# ===============================================================
def show_tool(gemini_api_key):
    st.header("📅 AI秘書", divider='rainbow')

    # --- 【帰還者の祝福】 ---
    if st.query_params.get("unlocked") == "true":
        st.session_state["cal_usage_count"] = 0
        st.query_params.clear()
        st.toast("おかえりなさい！音声入力の回数がリセットされました。")
        st.balloons()
        time.sleep(1)
        st.rerun()

    # --- 状態管理の初期化 ---
    if "cal_messages" not in st.session_state:
        st.session_state.cal_messages = [{"role": "assistant", "content": "こんにちは！ご予定を、下の方法でお伝えください。"}]
    if "cal_last_mic_id" not in st.session_state: st.session_state.cal_last_mic_id = None
    if "cal_last_file_name" not in st.session_state: st.session_state.cal_last_file_name = None
    
    # --- 【門番の存在保証】 ---
    if "cal_usage_count" not in st.session_state:
        st.session_state.cal_usage_count = 0

    # --- 統合AI処理関数 (変更なし) ---
    def process_input(user_input):
        with st.chat_message("assistant"):
            if not gemini_api_key:
                st.error("サイドバーでGemini APIキーを設定してください。")
                return
            try:
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                with st.spinner("（あなたの、言葉を、解読しています...）"):
                    if isinstance(user_input, bytes):
                        audio_part = {"mime_type": "audio/webm", "data": user_input}
                        transcription_prompt = "この日本語の音声を、できる限り正確に、文字に書き起こしてください。書き起こした日本語テキストのみを回答してください。"
                        transcription_response = model.generate_content([transcription_prompt, audio_part])
                        prompt_text = transcription_response.text.strip()
                        if not prompt_text:
                            st.warning("音声を認識できませんでした。もう一度お試しください。")
                            return
                    else:
                        prompt_text = user_input
                st.session_state.cal_messages.append({"role": "user", "content": prompt_text})
                with st.spinner("AIが予定を組み立てています..."):
                    jst = pytz.timezone('Asia/Tokyo')
                    current_time_jst = datetime.now(jst).isoformat()
                    system_prompt = f"""
                    あなたは予定を解釈する優秀なアシスタントです。ユーザーのテキストから「title」「start_time」「end_time」「location」「details」を抽出してください。
                    - 現在の日時は `{current_time_jst}` (JST)です。これを基準に日時を解釈してください。
                    - 日時は `YYYY-MM-DDTHH:MM:SS` 形式で出力してください。
                    - `end_time` が不明な場合は、`start_time` の1時間後を自動設定してください。
                    - 必ず以下のJSON形式のみで回答してください。他の言葉は一切含めないでください。
                    ```json
                    {{ "title": "（件名）", "start_time": "YYYY-MM-DDTHH:M:SS", "end_time": "YYYY-MM-DDTHH:MM:SS", "location": "（場所）", "details": "（詳細）" }}
                    ```
                    """
                    schedule_model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=system_prompt)
                    response = schedule_model.generate_content(prompt_text)
                    json_text = response.text.strip().lstrip("```json").rstrip("```").strip()
                    schedule_details = json.loads(json_text)
                    calendar_url = create_google_calendar_url(schedule_details)
                    display_start_time = "未設定"
                    if schedule_details.get('start_time'):
                        try: display_start_time = datetime.fromisoformat(schedule_details['start_time']).strftime('%Y年%m月%d日 %H:%M')
                        except: display_start_time = "AIが日付の解析に失敗"
                    ai_response = f"""以下の内容で承りました。よろしければリンクをクリックしてカレンダーに登録してください。\n\n- **件名:** {schedule_details.get('title', '未設定')}\n- **日時:** {display_start_time}\n- **場所:** {schedule_details.get('location', '未設定')}\n- **詳細:** {schedule_details.get('details', '未設定')}\n\n[📅 Googleカレンダーにこの予定を追加する]({calendar_url})"""
                    st.session_state.cal_messages.append({"role": "assistant", "content": ai_response})
            except Exception as e:
                st.session_state.cal_messages.append({"role": "assistant", "content": f"申し訳ありません、エラーが発生しました。({e})"})

    # --- UIの表示 ---
    # チャット履歴は常に表示
    for message in st.session_state.cal_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- 【運命の分岐路】(UIとロジックの完全なる調和) ---
    usage_limit = 5
    is_limit_reached = st.session_state.get("cal_usage_count", 0) >= usage_limit

    st.write("---")
    if is_limit_reached:
        st.success("🎉 たくさんの音声入力、ありがとうございます！")
        st.info("このAI秘書が、あなたの、毎日を、少しでも、豊かにできたなら、幸いです。\n\n下のボタンから応援ページに移動することで、音声入力を続けることができます。")
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        st.link_button("応援ページに移動して、音声入力を続ける", portal_url, type="primary")
    else:
        st.caption(f"🚀 あと {usage_limit - st.session_state.get('cal_usage_count', 0)} 回、音声入力ができます。応援後、リセットされます。（テキスト入力は無制限です）")
        col1, col2 = st.columns(2)
        with col1:
            audio_info = mic_recorder(start_prompt="🎤 マイクで録音", stop_prompt="⏹️ 停止", key='cal_mic_recorder')
        with col2:
            uploaded_file = st.file_uploader("📁 音声ファイルをアップロード", type=['wav', 'mp3', 'm4a', 'flac'], key="cal_uploader")

    # テキスト入力は、常に、ページ下部に、存在し続けます
    text_prompt = st.chat_input("キーボードで予定を入力...", key="cal_text_input")

    # --- 入力があった場合の処理 ---
    user_input_data = None
    input_type_is_voice = False

    if text_prompt:
        user_input_data = text_prompt
    elif not is_limit_reached and audio_info and audio_info['id'] != st.session_state.cal_last_mic_id:
        st.session_state.cal_last_mic_id = audio_info['id']
        user_input_data = audio_info['bytes']
        input_type_is_voice = True
    elif not is_limit_reached and uploaded_file and uploaded_file.name != st.session_state.cal_last_file_name:
        st.session_state.cal_last_file_name = uploaded_file.name
        user_input_data = uploaded_file.getvalue()
        input_type_is_voice = True

    if user_input_data:
        if input_type_is_voice:
            st.session_state.cal_usage_count += 1
        process_input(user_input_data)
        st.rerun()
