import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions
import json


# ===============================================================
# 補助関数 (『原点回帰』、シンプル is ベスト・バージョン)
# ===============================================================
def translate_with_gemini(content_to_process, api_key):
    if not content_to_process or not api_key:
        return None, None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        # --- 第一段階：『二段階認証プロセス』(変更なし、我々の、叡智) ---
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
        else: # strの場合
            processed_text = content_to_process
            original_input_display = processed_text

        # --- 第二段階：シンプルになった『脳の仕事（翻訳候補の生成）』 ---
        with st.spinner("AIが、最適な、3つの、翻訳候補を、考えています..."):
            # ★★★ ここが、我々の、新たなる『原点』です ★★★
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
        
        # --- 『JSON純化装置』が、変わらず、我々を、守る (変更なし) ---
        json_start_index = raw_response_text.find('{')
        json_end_index = raw_response_text.rfind('}')
        if json_start_index != -1 and json_end_index != -1:
            pure_json_text = raw_response_text[json_start_index : json_end_index + 1]
            try:
                translated_proposals = json.loads(pure_json_text)
                return original_input_display, translated_proposals
            except json.JSONDecodeError:
                st.error("AIが生成したデータの構造が破損していました。お手数ですが、もう一度お試しください。")
                print("【JSON構造破損エラー】純化後のテキスト:", pure_json_text)
                return None, None
        else:
            st.error("AIから予期せぬ形式の応答がありました。JSONデータが含まれていません。")
            print("【非JSON応答エラー】AIの生応答:", raw_response_text)
            return None, None

    # --- 『二段構えの迎撃システム』も、健在 (変更なし) ---
    except exceptions.ResourceExhausted as e:
        st.error("APIキーの上限に達した可能性があります。少し時間をあけるか、明日以降に再試行してください。")
        return None, None
    except Exception as e:
        error_message = str(e).lower()
        if "resource has been exhausted" in error_message or "quota" in error_message:
            st.error("APIキーの上限に達した可能性があります。少し時間をあけるか、明日以降に再試行してください。")
        else:
            st.error(f"AI処理中に予期せぬエラーが発生しました: {e}")
        return None, None

# ===============================================================
# メインの仕事 (表示部分を、シンプルに、美しく、再設計)
# ===============================================================
def show_tool(gemini_api_key):
    if st.query_params.get("unlocked") == "true":
        st.session_state.translator_usage_count = 0
        st.query_params.clear()
        st.toast("おかえりなさい！利用回数がリセットされました。")
        st.balloons()
        time.sleep(1)
        st.rerun()

    st.header("🤝 翻訳ツール", divider='rainbow')

    if "translator_results" not in st.session_state: st.session_state.translator_results = []
    if "translator_last_mic_id" not in st.session_state: st.session_state.translator_last_mic_id = None
    if "text_to_process" not in st.session_state: st.session_state.text_to_process = None
    if "translator_last_input" not in st.session_state: st.session_state.translator_last_input = ""
    if "translator_usage_count" not in st.session_state: st.session_state.translator_usage_count = 0

    usage_limit = 5
    is_limit_reached = st.session_state.translator_usage_count >= usage_limit

    audio_info = None

    if is_limit_reached:
        st.success("🎉 たくさんのご利用、ありがとうございます！")
        st.info("このツールが、あなたの世界を広げる一助となれば幸いです。\n\n下のボタンから応援ページに移動することで、翻訳を続けることができます。")
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        st.link_button("応援ページに移動して、翻訳を続ける", portal_url, type="primary")
    else:
        st.info("マイクで日本語を話すか、テキストボックスに入力してください。ニュアンスの異なる3つの翻訳候補を提案します。")
        st.caption(f"🚀 あと {usage_limit - st.session_state.translator_usage_count} 回、提案を受けられます。応援後、残りの回数がリセットされます。")
        with st.expander("💡 このツールのAIについて"):
            st.markdown("""
            このツールは、Googleの**Gemini 1.5 Flash**というAIモデルを使用しています。
            現在、このモデルには**1分あたり15回、1日あたり1,500回まで**の無料利用枠が設定されています。
            心ゆくまで、言語の壁を越える旅をお楽しみください！
            """, unsafe_allow_html=True)
        def handle_text_input():
            st.session_state.text_to_process = st.session_state.translator_text
        col1, col2 = st.columns([1, 2])
        with col1:
            audio_info = mic_recorder(start_prompt="🎤 話し始める", stop_prompt="⏹️ 提案を受ける", key='translator_mic', format="webm")
        with col2:
            st.text_input("または、ここに日本語を入力してEnter...", key="translator_text", on_change=handle_text_input)

    content_to_process = None
    if audio_info and audio_info['id'] != st.session_state.translator_last_mic_id:
        content_to_process = audio_info['bytes']
        st.session_state.translator_last_mic_id = audio_info['id']
    elif st.session_state.text_to_process:
        content_to_process = st.session_state.text_to_process
        st.session_state.text_to_process = None

    if content_to_process and content_to_process != st.session_state.translator_last_input:
        st.session_state.translator_last_input = content_to_process
        if not gemini_api_key:
            st.error("サイドバーでGemini APIキーを設定してください。")
        else:
            original, proposals_data = translate_with_gemini(content_to_process, gemini_api_key)
            
            if proposals_data and "candidates" in proposals_data: # ★★★ キーを'proposals'から'candidates'に変更 ★★★
                st.session_state.translator_usage_count += 1
                st.session_state.translator_results.insert(0, {"original": original, "candidates": proposals_data["candidates"]})
                st.rerun()
            else:
                st.session_state.translator_last_input = ""

    # ★★★ ここが、シンプルに、生まれ変わった、我々の、陳列棚です ★★★
    if st.session_state.translator_results:
        st.write("---")
        for i, result in enumerate(st.session_state.translator_results):
            with st.container(border=True):
                st.markdown(f"#### 履歴 No.{len(st.session_state.translator_results) - i}")
                st.markdown(f"**🇯🇵 あなたの入力:** {result['original']}")
                
                if "candidates" in result and isinstance(result["candidates"], list):
                    st.write("---")
                    # 3つの候補を、美しく、横に、並べます
                    cols = st.columns(len(result["candidates"]))
                    for col_index, candidate in enumerate(result["candidates"]):
                        with cols[col_index]:
                            nuance = candidate.get('nuance', 'N/A')
                            translation = candidate.get('translation', '翻訳を取得できませんでした')
                            st.info(f"**{nuance}**")
                            st.success(f"{translation}")

        if st.button("翻訳履歴をクリア", key="clear_translator_history"):
            st.session_state.translator_results = []
            st.session_state.translator_last_input = ""
            st.rerun()
