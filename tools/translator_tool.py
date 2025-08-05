# ===============================================================
# ★★★ translator_tool.py （復元版） ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import time

# --- このツール専用のプロンプト作成関数 ---
def create_translator_prompt(target_language, source_text):
    return f"""
# 命令
あなたは、世界最高の翻訳家です。
以下のテキストを、寸分の狂いもなく、自然で流暢な「{target_language}」に翻訳してください。

# 翻訳対象のテキスト
{source_text}

# 翻訳結果
"""

# --- ポータルから呼び出されるメイン関数 ---
def show_tool(gemini_api_key):
    st.header("🤝 翻訳ツール", divider='rainbow')

    # --- セッションステートの初期化 ---
    # このツール専用のキーを接頭辞として使用する
    prefix = "translator_"
    if f"{prefix}source_text" not in st.session_state:
        st.session_state[f"{prefix}source_text"] = "ここに翻訳したい文章を入力してください。"
        st.session_state[f"{prefix}target_language"] = "英語"
        st.session_state[f"{prefix}translated_text"] = ""

    # --- UIのレイアウト ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("原文")
        # st.session_stateから値を取得して表示
        source_text = st.text_area(
            "翻訳したい文章を入力", 
            value=st.session_state[f"{prefix}source_text"], 
            height=300, 
            key=f"{prefix}source_text_input"
        )
        
        # ユーザーの入力をセッションステートに即時反映
        st.session_state[f"{prefix}source_text"] = source_text

        target_language = st.selectbox(
            "何語に翻訳しますか？",
            ("英語", "日本語", "中国語", "韓国語", "スペイン語", "フランス語"),
            key=f"{prefix}target_language_select"
        )
        st.session_state[f"{prefix}target_language"] = target_language
        
        if st.button("この内容で翻訳する", type="primary", use_container_width=True):
            if not gemini_api_key:
                st.warning("サイドバーからGemini APIキーを設定してください。")
            elif not source_text or source_text == "ここに翻訳したい文章を入力してください。":
                st.warning("翻訳したい文章を入力してください。")
            else:
                try:
                    with st.spinner(f"🧠 AIが{target_language}へ翻訳中..."):
                        genai.configure(api_key=gemini_api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        prompt = create_translator_prompt(target_language, source_text)
                        response = model.generate_content(prompt)
                        # 翻訳結果をセッションステートに保存
                        st.session_state[f"{prefix}translated_text"] = response.text
                        st.toast("翻訳が完了しました！", icon="🎉")
                except Exception as e:
                    st.error(f"翻訳中にエラーが発生しました: {e}")

    with col2:
        st.subheader("翻訳結果")
        # st.session_stateから翻訳結果を取得して表示
        translated_text = st.text_area(
            "翻訳結果がここに表示されます", 
            value=st.session_state[f"{prefix}translated_text"], 
            height=300, 
            key=f"{prefix}translated_text_output",
            disabled=True # 編集不可にする
        )
