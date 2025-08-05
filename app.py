# ===============================================================
# ★★★ app.py ＜最終完成版＞ ★★★
# ===============================================================
import streamlit as st
from streamlit_local_storage import LocalStorage # ★ 復活させる
import time
from tools import translator_tool, okozukai_recorder_tool, calendar_tool, gijiroku_tool, kensha_no_kioku_tool, ai_memory_partner_tool

st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()
    tool_selection = st.radio(
        "利用するツールを選択してください:",
        ("🤝 翻訳ツール", "💰 お小遣い管理", "📅 カレンダー登録", "📝 議事録作成", "🧠 賢者の記憶", "❤️ 認知予防ツール"),
        key="tool_selection"
    )
    st.divider()
    
    # ★★★ LocalStorageを、APIキーのためだけに、正しく使う ★★★
    localS = LocalStorage()
    saved_key = localS.getItem("gemini_api_key")
    gemini_default = saved_key if isinstance(saved_key, str) else ""
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = gemini_default
        
    with st.expander("⚙️ APIキーの設定", expanded=not st.session_state.gemini_api_key):
        with st.form("api_key_form", clear_on_submit=False):
            api_key_input = st.text_input("Gemini APIキー", type="password", value=st.session_state.gemini_api_key)
            col1, col2 = st.columns(2)
            with col1: save_button = st.form_submit_button("💾 保存", use_container_width=True)
            with col2: reset_button = st.form_submit_button("🔄 クリア", use_container_width=True)

    if save_button:
        st.session_state.gemini_api_key = api_key_input
        localS.setItem("gemini_api_key", st.session_state.gemini_api_key)
        st.success("キーをブラウザに保存しました！"); time.sleep(1); st.rerun()
    if reset_button:
        localS.setItem("gemini_api_key", None)
        st.session_state.gemini_api_key = ""
        st.success("キーをクリアしました。"); time.sleep(1); st.rerun()

    st.divider()
    st.markdown("""<div style="font-size: 0.9em;"><a href="https://aistudio.google.com/app/apikey" target="_blank">Gemini APIキーの取得はこちら</a></div>""", unsafe_allow_html=True)


if st.session_state.tool_selection == "🤝 翻訳ツール":
    translator_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "💰 お小遣い管理":
    # ★★★ お小遣いツールには、もう、LocalStorageを渡さない ★★★
    okozukai_recorder_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "📅 カレンダー登録":
    calendar_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "📝 議事録作成":
    gijiroku_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "🧠 賢者の記憶":
    kensha_no_kioku_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "❤️ 認知予防ツール":
    ai_memory_partner_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
