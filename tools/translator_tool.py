# ===============================================================
# ★★★ translator_tool.py ＜ちゃろさんの設計思想・完全統合版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import time
import json
from streamlit_mic_recorder import mic_recorder
from google.api_core import exceptions

# --- 補助関数 (ちゃろさんの高機能版) ---
def translate_with_gemini(content_to_process, api_key):
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
                st.error("あなたの声を、言葉に、変えることができませんでした。")
                return None, None
            original_input_display = f"{processed_text} (🎙️音声より)"
        else:
            processed_text = content_to_process
            original_input_display = processed_text

        with st.spinner("AIが、最適な、3つの、翻訳候補を、考えています..."):
            system_prompt = """
            # 命令書: 言語ニュアンスの、探求者としての、あなたの、責務
            あなたは、プロフェッショナルな、翻訳アシスタントです。
            あなたの、唯一の、任務は、ユーザーから、渡された、日本語を、分析し、ニュアンスの異なる、3つの、プロフェッショナルな、英訳候補を、生成し、以下の、JSON形式で、厳格に、出力することです。
            ## JSON出力に関する、絶対的な、契約条件：
            あなたの回答は、必ず、以下のJSON構造に、厳密に、従うこと。このJSONオブジェクト以外の、いかなるテキストも、絶対に、絶対に、含めてはならない。
            ```json
            {
              "candidates": [
                {
                  "translation": "ここに、1つ目の、最も、標準的な、翻訳候補を記述します。",
                  "nuance": "この翻訳が持つ、ニュアンス（例：「最も一般的」「フォーマル」など）を、簡潔に、説明します。"
                },
                {
                  "translation": "ここに、2つ目の、少し、ニュアンスの異なる、翻訳候補を記述します。",
                  "nuance": "この翻訳が持つ、ニュアンス（例：「より丁寧」「やや婉曲的」など）を、簡潔に、説明します。"
                },
                {
                  "translation": "ここに、3つ目の、さらに、異なる、視点からの、翻訳候補を記述します。",
                  "nuance": "この翻訳が持つ、ニュアンス（例：「最も簡潔」「直接的」など）を、簡潔に、説明します。"
                }
              ]
            }
            ```
            ## 最重要ルール:
            - `translation` は、必ず、プロフェッショナルな英語で、記述すること。
            - `nuance` は、必ず、その、違いが、一目でわかる、**簡潔な【日本語】**で、記述すること。
            """
            request_contents = [system_prompt, processed_text]
            response = model.generate_content(request_contents)
            raw_response_text = response.text
        
        json_start_index = raw_response_text.find('{')
        json_end_index = raw_response_text.rfind('}')
        if json_start_index != -1 and json_end_index != -1:
            pure_json_text = raw_response_text[json_start_index : json_end_index + 1]
            try:
                translated_proposals = json.loads(pure_json_text)
                return original_input_display, translated_proposals
            except json.JSONDecodeError:
                st.error("AIの応答データの構造が破損していました。")
                return None, None
        else:
            st.error("AIから予期せぬ形式の応答がありました。")
            return None, None
    except exceptions.ResourceExhausted:
        st.error("APIキーの上限に達したようです。")
        return None, None
    except Exception as e:
        st.error(f"AI処理中に予期せぬエラーが発生しました: {e}")
        return None, None

# --- メイン関数 ---
def show_tool(gemini_api_key):
    st.header("🤝 翻訳ツール", divider='rainbow')

    prefix = "translator_"
    
    # セッションステートの初期化
    if f"{prefix}usage_count" not in st.session_state: st.session_state[f"{prefix}usage_count"] = 0
    if f"{prefix}results" not in st.session_state: st.session_state[f"{prefix}results"] = []
    if f"{prefix}last_mic_id" not in st.session_state: st.session_state[f"{prefix}last_mic_id"] = None
    if f"{prefix}text_to_process" not in st.session_state: st.session_state[f"{prefix}text_to_process"] = None
    if f"{prefix}last_input" not in st.session_state: st.session_state[f"{prefix}last_input"] = ""

    # 応援機能のロジック
    usage_limit = 1
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit
    
   # --- UIロジックの分岐 ---
if is_limit_reached:
    # ★★★ ここが、新しくなった「合言葉システム」です ★★★
    st.success("🎉 たくさんのご利用、ありがとうございます！")
    st.info("このツールが、あなたの世界を広げる一助となれば幸いです。")
    st.warning("翻訳を続けるには、応援ページで「今日の合言葉（4桁の数字）」を確認し、入力してください。")
    
    portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue2.html"
    st.markdown(f'<a href="{portal_url}" target="_blank">応援ページで「今日の合言葉」を確認する →</a>', unsafe_allow_html=True)
    st.divider()

    with st.form("translator_password_form"):
        password_input = st.text_input("ここに「今日の合言葉」を入力してください:", type="password")
        if st.form_submit_button("利用回数をリセットする", use_container_width=True):
            JST = timezone(timedelta(hours=+9))
            today_int = int(datetime.now(JST).strftime('%Y%m%d'))
            seed_str = st.secrets.get("unlock_seed", "0")
            seed_int = int(seed_str) if seed_str.isdigit() else 0
            correct_password = str((today_int + seed_int) % 10000).zfill(4)
            
            if password_input == correct_password:
                st.session_state[f"{prefix}usage_count"] = 0
                st.balloons()
                st.success("ありがとうございます！利用回数がリセットされました。")
                time.sleep(2)
                st.rerun()
            else:
                st.error("合言葉が違うようです。応援ページで、もう一度ご確認ください。")

else:
    # --- 通常モード ---
    st.info("マイクで日本語を話すか、テキストボックスに入力してください。ニュアンスの異なる3つの翻訳候補を提案します。")
    st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、提案を受けられます。")
    
    def handle_text_input():
        st.session_state[f"{prefix}text_to_process"] = st.session_state[f"{prefix}text_input_key"]
    
    col1, col2 = st.columns([1, 2])
    with col1: audio_info = mic_recorder(start_prompt="🎤 話し始める", stop_prompt="⏹️ 提案を受ける", key=f'{prefix}mic', format="webm")
    with col2: st.text_input("または、ここに日本語を入力してEnter...", key=f"{prefix}text_input_key", on_change=handle_text_input)

    content_to_process = None
    if audio_info and audio_info['id'] != st.session_state[f"{prefix}last_mic_id"]:
        content_to_process = audio_info['bytes']
        st.session_state[f"{prefix}last_mic_id"] = audio_info['id']
    elif st.session_state[f"{prefix}text_to_process"]:
        content_to_process = st.session_state[f"{prefix}text_to_process"]
        st.session_state[f"{prefix}text_to_process"] = None

    if content_to_process and content_to_process != st.session_state[f"{prefix}last_input"]:
        st.session_state[f"{prefix}last_input"] = content_to_process
        if not gemini_api_key:
            st.error("サイドバーでGemini APIキーを設定してください。")
        else:
            original, proposals_data = translate_with_gemini(content_to_process, gemini_api_key)
            if proposals_data and "candidates" in proposals_data:
                st.session_state[f"{prefix}usage_count"] += 1
                st.session_state[f"{prefix}results"].insert(0, {"original": original, "candidates": proposals_data["candidates"]})
                st.rerun()
            else:
                st.session_state[f"{prefix}last_input"] = ""

    if st.session_state[f"{prefix}results"]:
        st.divider()
        st.subheader("📜 翻訳履歴")
        for i, result in enumerate(st.session_state[f"{prefix}results"]):
            with st.container(border=True):
                st.markdown(f"**🇯🇵 あなたの入力:** {result['original']}")
                if "candidates" in result and isinstance(result["candidates"], list):
                    st.write("---")
                    cols = st.columns(len(result["candidates"]))
                    for col_index, candidate in enumerate(result["candidates"]):
                        with cols[col_index]:
                            nuance = candidate.get('nuance', 'N/A')
                            translation = candidate.get('translation', '翻訳エラー')
                            st.info(f"**{nuance}**")
                            st.success(translation)
        
        if st.button("翻訳履歴をクリア", key=f"{prefix}clear_history"):
            st.session_state[f"{prefix}results"] = []
            st.session_state[f"{prefix}last_input"] = ""
            st.rerun()
