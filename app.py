# ===============================================================
# ★★★ app.py ＜最終版・完全版＞ ★★★
# ===============================================================
import streamlit as st
from streamlit_local_storage import LocalStorage
import time
from tools import translator_tool, okozukai_recorder_tool, calendar_tool, gijiroku_tool, kensha_no_kioku_tool, ai_memory_partner_tool

st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

# LocalStorageは、もはやAPIキーの保存という限定的な役割でのみ使用
with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()
    tool_selection = st.radio(
        "利用するツールを選択してください:",
        ("🤝 翻訳ツール", "💰 お小遣い管理", "📅 カレンダー登録", "📝 議事録作成", "🧠 賢者の記憶", "❤️ 認知予防ツール"),
        key="tool_selection"
    )
    st.divider()
    
    localS = LocalStorage()
    saved_key = localS.getItem("gemini_api_key")
    gemini_default = saved_key if isinstance(saved_key, str) else ""
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = gemini_default
        
    with st.expander("⚙️ APIキーの設定", expanded=not st.session_state.gemini_api_key):
        with st.form("api_key_form"):
            api_key_input = st.text_input("Gemini APIキー", type="password", value=st.session_state.gemini_api_key)
            if st.form_submit_button("💾 保存", use_container_width=True):
                st.session_state.gemini_api_key = api_key_input
                localS.setItem("gemini_api_key", api_key_input)
                st.success("キーを保存しました！"); time.sleep(1); st.rerun()

    st.divider()
    st.markdown("""<div style="font-size: 0.9em;"><a href="https://aistudio.google.com/app/apikey" target="_blank">Gemini APIキーの取得はこちら</a></div>""", unsafe_allow_html=True)


api_key = st.session_state.get('gemini_api_key', '')

# --- 各ツールの呼び出し ---
# 選択されたツールに応じて、対応するモジュールのshow_tool関数を呼び出す
if tool_selection == "🤝 翻訳ツール":
    translator_tool.show_tool(gemini_api_key=api_key)
elif tool_selection == "💰 お小遣い管理":
    okozukai_recorder_tool.show_tool(gemini_api_key=api_key)
elif tool_selection == "📅 カレンダー登録":
    calendar_tool.show_tool(gemini_api_key=api_key)
elif tool_selection == "📝 議事録作成":
    gijiroku_tool.show_tool(gemini_api_key=api_key)
elif tool_selection == "🧠 賢者の記憶":
    kensha_no_kioku_tool.show_tool(gemini_api_key=api_key)
elif tool_selection == "❤️ 認知予防ツール":
    ai_memory_partner_tool.show_tool(gemini_api_key=api_key)
