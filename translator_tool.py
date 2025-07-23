# tools/translator_tool.py

import streamlit as st
import google.generativeai as genai
from google.cloud import speech
from google.api_core.client_options import ClientOptions
from streamlit_mic_recorder import mic_recorder

# ===============================================================
# 補助関数 (calendar_tool.pyから継承した、信頼できるコード)
# ===============================================================
def transcribe_audio(audio_bytes, api_key):
    """Speech-to-Text APIを使用して音声データを日本語テキストに変換する"""
    if not audio_bytes or not api_key:
        return None
    try:
        client_options = ClientOptions(api_key=api_key)
        client = speech.SpeechClient(client_options=client_options)
        audio = speech.RecognitionAudio(content=audio_bytes)
        # 日本語の聞き取りに特化
        config = speech.RecognitionConfig(language_code="ja-JP")
        response = client.recognize(config=config, audio=audio)
        if response.results:
            return response.results[0].alternatives[0].transcript
    except Exception as e:
        st.error(f"音声認識エラー: {e}")
    return None

# ===============================================================
# 新しい専門家の仕事：翻訳
# ===============================================================
def translate_text_with_gemini(text_to_translate, api_key):
    """Geminiを使用してテキストを自然な英語に翻訳する"""
    if not text_to_translate or not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        
        # ちゃろ様との議論で洗練させた、魂のプロンプト
        system_prompt = """
        あなたは、言語の壁を乗り越える手助けをする、非常に優秀な翻訳アシスタントです。
        ユーザーから渡された日本語のテキストを、海外の親しい友人との会話で使われるような、自然で、カジュアルでありながら礼儀正しく、そしてフレンドリーな英語に翻訳してください。
        - 非常に硬い表現や、ビジネス文書のような翻訳は避けてください。
        - 翻訳後の英語テキストのみを回答してください。他の言葉は一切含めないでください。
        """
        model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=system_prompt)
        response = model.generate_content(text_to_translate)
        return response.text.strip()
    except Exception as e:
        st.error(f"翻訳エラー: {e}")
    return None

# ===============================================================
# 専門家のメインの仕事 (司令塔 app.py から呼び出される)
# ===============================================================
def show_tool(gemini_api_key, speech_api_key):
    st.header("🤝 フレンドリー翻訳ツール", divider='rainbow')

    # --- 状態管理の初期化 (私たちの叡智) ---
    if "translation_results" not in st.session_state:
        st.session_state.translation_results = []
    # 「こだま」防止用のID記憶場所
    if "translator_last_mic_id" not in st.session_state:
        st.session_state.translator_last_mic_id = None

    # --- UIウィジェットの表示 ---
    st.info("マイクで日本語を話すか、テキストボックスに入力してください。自然な英語に翻訳します。")

    # 音声入力とテキスト入力（デュアル入力方式）
    col1, col2 = st.columns([1, 2])
    with col1:
        audio_info = mic_recorder(
            start_prompt="🎤 話し始める",
            stop_prompt="⏹️ 翻訳する",
            key='translator_mic'
        )
    with col2:
        text_prompt = st.text_input("または、ここに日本語を入力...", key="translator_text")

    # --- 結果表示エリア ---
    if st.session_state.translation_results:
        st.write("---")
        for i, result in enumerate(reversed(st.session_state.translation_results)): # 新しいものが上にくるように
            with st.container(border=True):
                st.caption(f"翻訳 {len(st.session_state.translation_results) - i}")
                st.markdown(f"**🇯🇵 入力 (日本語):**\n{result['original']}")
                st.markdown(f"**🇺🇸 翻訳 (英語):**\n{result['translated']}")
        if st.button("翻訳履歴をクリア", key="clear_history"):
            st.session_state.translation_results = []
            st.rerun()


    # --- 入力があった場合の、一度きりの、処理フロー ---
    japanese_text = None
    source = None # 入力ソースを記録

    # 音声入力があった場合
    if audio_info and audio_info['id'] != st.session_state.translator_last_mic_id:
        st.session_state.translator_last_mic_id = audio_info['id']
        if not speech_api_key:
            st.error("サイドバーでSpeech-to-Text APIキーを設定してください。")
        else:
            with st.spinner("音声を日本語に変換中..."):
                japanese_text = transcribe_audio(audio_info['bytes'], speech_api_key)
                source = "mic"

    # テキスト入力があった場合
    elif text_prompt:
        japanese_text = text_prompt
        source = "text"

    # --- 翻訳処理の実行 ---
    if japanese_text:
        if not gemini_api_key:
            st.error("サイドバーでGemini APIキーを設定してください。")
        else:
            with st.spinner("AIが最適な英語を考えています..."):
                translated_text = translate_text_with_gemini(japanese_text, gemini_api_key)

            if translated_text:
                # 翻訳結果をセッション状態に保存
                st.session_state.translation_results.append({
                    "original": japanese_text,
                    "translated": translated_text
                })
                # テキスト入力欄をクリアするためにrerunを呼ぶ
                # このシンプルな使い方なら、私たちの管理下に置ける
                st.rerun()
            else:
                st.warning("翻訳に失敗しました。もう一度お試しください。")
