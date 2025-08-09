# ===================================================================
# ★★★ app.py ＜コピペ＆ペースト方式・最終完成版＞ ★★★
# ===================================================================
import streamlit as st
import time

# ★★★ ツールをインポート ★★★
from tools import career_analyzer_tool, translator_tool 

# ===============================================================
# アプリの基本設定
# ===============================================================
st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

# ===============================================================
# UI描画とツール起動
# ===============================================================
with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()
    
    st.radio("利用するツールを選択してください:", ("👔 AIキャリアアナリスト", "🤝 翻訳ツール"), key="tool_selection_sidebar")
    st.divider()
    
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")

    with st.expander("⚙️ Gemini APIキーの設定", expanded=not(st.session_state.gemini_api_key)):
        with st.form("api_key_form"):
            api_key_input = st.text_input("Gemini APIキー", type="password", value=st.session_state.gemini_api_key)
            col1, col2 = st.columns(2)
            with col1: save_button = st.form_submit_button("💾 保存", use_container_width=True)
            with col2: reset_button = st.form_submit_button("🔄 クリア", use_container_width=True)

    if save_button:
        st.session_state.gemini_api_key = api_key_input
        st.success("キーを保存しました！"); time.sleep(1); st.rerun()
    if reset_button:
        st.session_state.gemini_api_key = ""; st.success("キーをクリアしました。"); time.sleep(1); st.rerun()
        
    st.markdown("""<div style="font-size: 0.9em;"><a href="https://aistudio.google.com/app/apikey" target="_blank">Gemini APIキーの取得はこちら</a></div>""", unsafe_allow_html=True)

# --- メインコンテンツ ---
tool_choice = st.session_state.get("tool_selection_sidebar")
gemini_api_key = st.session_state.get("gemini_api_key", "")

# ★★★ 各ツールを、必要な引数だけで正しく呼び出す ★★★
if tool_choice == "👔 AIキャリアアナリスト":
    career_analyzer_tool.show_tool(gemini_api_key=gemini_api_key)
elif tool_choice == "🤝 翻訳ツール":
    translator_tool.show_tool(gemini_api_key=gemini_api_key)
