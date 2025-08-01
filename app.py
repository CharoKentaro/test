import streamlit as st
from streamlit_local_storage import LocalStorage
import time

# ★★★ 七人の、英雄たちが、ここに、集結します ★★★
from tools import translator_tool, okozukai_recorder_tool, calendar_tool, gijiroku_tool, kensha_no_kioku_tool
from tools import AI_Memory_Partner # ★ 変更点：英雄の、正式名称での、召喚

# --- アプリの基本設定 (変更なし) ---
st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

# --- サイドバー (最終形態) ---
with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()

    # ★★★ 選択肢は、七つに ★★★
    tool_selection = st.radio(
        "利用するツールを選択してください:",
        ("❤️ 認知予防ツール", "🤝 翻訳ツール", "💰 お小遣い管理", "📅 カレンダーAI秘書", "📝 議事録作成", "🧠 賢者の記憶"), # ★ 変更点：表示名を変更
        key="tool_selection"
    )
    st.divider()

    # --- APIキー管理 (変更なし) ---
    localS = LocalStorage()
    saved_key = localS.getItem("gemini_api_key")
    gemini_default = saved_key if isinstance(saved_key, str) else ""
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = gemini_default
    with st.expander("⚙️ APIキーの設定", expanded=not st.session_state.gemini_api_key):
        with st.form("api_key_form", clear_on_submit=False):
            st.session_state.gemini_api_key = st.text_input("Gemini APIキー", type="password", value=st.session_state.gemini_api_key)
            col1, col2 = st.columns(2)
            with col1: save_button = st.form_submit_button("💾 保存", use_container_width=True)
            with col2: reset_button = st.form_submit_button("🔄 クリア", use_container_width=True)
    if save_button:
        localS.setItem("gemini_api_key", st.session_state.gemini_api_key, key="storage_api_key_save")
        st.success("キーをブラウザに保存しました！"); time.sleep(1); st.rerun()
    if reset_button:
        localS.setItem("gemini_api_key", None, key="storage_api_key_clear");
        st.session_state.gemini_api_key = ""
        st.success("キーをクリアしました。"); time.sleep(1); st.rerun()
    st.divider()
    st.markdown("""<div style="font-size: 0.9em;"><a href="https://aistudio.google.com/app/apikey" target="_blank">Gemini APIキーの取得はこちら</a></div>""", unsafe_allow_html=True)

# ★★★★★ 『偉大なる、仕分け人』の、最終契約書 ★★★★★
if st.session_state.tool_selection == "❤️ 認知予防ツール": # ★ 変更点：契約書を、正式な表示名に合わせる
    AI_Memory_Partner.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "🤝 翻訳ツール":
    translator_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "💰 お小遣い管理":
    okozukai_recorder_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "📅 カレンダーAI秘書":
    calendar_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "📝 議事録作成":
    gijiroku_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "🧠 賢者の記憶":
    kensha_no_kioku_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
