import streamlit as st
from streamlit_local_storage import LocalStorage
import time

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★【摂政の、解任】 - 傲慢な、摂政の、コードは、完全に、削除します ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# if "tool_selection" not in st.session_state: ... のブロックを、完全に、消し去ります。

from tools import translator_tool, okozukai_recorder_tool, calendar_tool, gijiroku_tool, kensha_no_kioku_tool

st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★【王位継承法の、制定】 - これが、最も、正統で、美しい、後継者指名です ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    st.radio(
        "利用するツールを選択してください:",
        ("🤝 翻訳ツール", "💰 お小遣い管理", "📅 AI秘書", "📝 議事録作成", "🧠 賢者の記憶", "❤️ 認知予防ツール"),
        key="tool_selection",
        index=0  # <-- この、一行こそが、帝国の、平和を、永遠に、保つ、魔法です。
    )
    
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

# ★★★★★ 『偉大なる、仕分け人』は、正統な、王の、声だけを、聞く ★★★★★
if st.session_state.tool_selection == "🤝 翻訳ツール":
    translator_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "💰 お小遣い管理":
    okozukai_recorder_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "📅 AI秘書":
    calendar_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "📝 議事録作成":
    gijiroku_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
elif st.session_state.tool_selection == "🧠 賢者の記憶":
    kensha_no_kioku_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
    
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★ 第六の英雄は、正しく、統治された、帝国で、その、使命を、果たす ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
elif st.session_state.tool_selection == "❤️ 認知予防ツール":
    
    import google.generativeai as genai
    from streamlit_mic_recorder import mic_recorder

    # ( ... 認知予防ツールの、内部コードは、以前の、安定版から、一切、変更ありません ... )
    SYSTEM_PROMPT_TRUE_FINAL = """..."""
    def dialogue_with_gemini(content_to_process, api_key):
        # ...
        return original_input_display, ai_response_text

    prefix = "cc_"
    storage_key_results = f"{prefix}results"

    if f"{prefix}initialized" not in st.session_state:
        retrieved_results = localS.getItem(storage_key_results)
        st.session_state[storage_key_results] = retrieved_results if retrieved_results else []
        st.session_state[f"{prefix}initialized"] = True
        
        if st.query_params.get("unlocked") == "true":
            st.session_state[f"{prefix}usage_count"] = 0
            st.query_params.clear()
            st.toast("おかえりなさい！応援、ありがとうございました！")
            st.balloons()
            # 危険なrerunは、ここには、ありません。

    st.header("❤️ 認知予防ツール", divider='rainbow')

    # （...以降の、全てのコードも、以前の、安定版から、一切、変更ありません...）
    if f"{prefix}last_mic_id" not in st.session_state: st.session_state[f"{prefix}last_mic_id"] = None
    # ...
    # ...
    if st.session_state.get(storage_key_results):
        # ...
        if st.button("会話の履歴をクリア", key=f"{prefix}clear_history"):
            st.session_state[storage_key_results] = []
            st.session_state[f"{prefix}last_input"] = ""
            localS.setItem(storage_key_results, [])
            if f"{prefix}initialized" in st.session_state:
                 del st.session_state[f"{prefix}initialized"]
            st.rerun()
