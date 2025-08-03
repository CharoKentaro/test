import streamlit as st
from streamlit_local_storage import LocalStorage
import time

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★【作戦①：摂政の、設置】帝国の、崩壊を、永遠に、防ぐ、絶対の、法 ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# 全ての、仕事の、始まりに、国王（tool_selection）の、存在を、確認する。
# もし、万が一、ご不在の、場合には、摂政（"🤝 翻訳ツール"）が、代行する。
if "tool_selection" not in st.session_state:
    st.session_state.tool_selection = "🤝 翻訳ツール"

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
from tools import translator_tool, okozukai_recorder_tool, calendar_tool, gijiroku_tool, kensha_no_kioku_tool

st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()
    # 国王陛下は、摂政が、準備した、玉座に、お座りになります。
    st.radio(
        "利用するツールを選択してください:",
        ("🤝 翻訳ツール", "💰 お小遣い管理", "📅 AI秘書", "📝 議事録作成", "🧠 賢者の記憶", "❤️ 認知予防ツール"),
        key="tool_selection"
    )
    # （...以降のサイドバーのコードは変更なし...）
    localS = LocalStorage()
    # ...
    pass

# ★★★★★ 『偉大なる、仕分け人』は、もはや、国王不在に、悩まされることはない ★★★★★
if st.session_state.tool_selection == "🤝 翻訳ツール":
    translator_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
# （...）
elif st.session_state.tool_selection == "🧠 賢者の記憶":
    kensha_no_kioku_tool.show_tool(gemini_api_key=st.session_state.get('gemini_api_key', ''))
    
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★【究極最終形態】第六の英雄は、安定した、帝国で、その、使命を、果たす ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
elif st.session_state.tool_selection == "❤️ 認知予防ツール":
    
    import google.generativeai as genai
    from streamlit_mic_recorder import mic_recorder

    SYSTEM_PROMPT_TRUE_FINAL = """...""" # （変更なし）
    def dialogue_with_gemini(content_to_process, api_key): # （変更なし）
        # ...
        return original_input_display, ai_response_text

    prefix = "cc_"
    storage_key_results = f"{prefix}results"

    # ★★★【究極の、創生の儀式】 - この世界の、始まりに、一度だけ、実行される ★★★
    if f"{prefix}initialized" not in st.session_state:
        retrieved_results = localS.getItem(storage_key_results)
        st.session_state[storage_key_results] = retrieved_results if retrieved_results else []
        st.session_state[f"{prefix}initialized"] = True
        
        # ★★★【作戦②：爆薬の、解体】 - 帰還者の祝福は、平和的に、行われる ★★★
        if st.query_params.get("unlocked") == "true":
            st.session_state[f"{prefix}usage_count"] = 0
            st.query_params.clear()
            st.toast("おかえりなさい！応援、ありがとうございました！")
            st.balloons()
            # 帝国を、再起動する、危険な、st.rerun() は、完全に、撤去されました。

    # --- これより先は、完全に、安定した、世界 ---
    st.header("❤️ 認知予防ツール", divider='rainbow')

    # （...セッション管理、UI、入力ハンドリング等の、全てのコードは、以前の、安定版と、同じです...）
    if f"{prefix}last_mic_id" not in st.session_state: st.session_state[f"{prefix}last_mic_id"] = None
    if f"{prefix}text_to_process" not in st.session_state: st.session_state[f"{prefix}text_to_process"] = None
    if f"{prefix}last_input" not in st.session_state: st.session_state[f"{prefix}last_input"] = ""
    if f"{prefix}usage_count" not in st.session_state: st.session_state[f"{prefix}usage_count"] = 0
    
    usage_limit = 3
    # ...
    # ...
    if st.session_state.get(storage_key_results):
        # ...
        if st.button("会話の履歴をクリア", key=f"{prefix}clear_history"):
            st.session_state[storage_key_results] = []
            st.session_state[f"{prefix}last_input"] = ""
            localS.setItem(storage_key_results, [])
            # 創生の、記憶も、リセットします
            if f"{prefix}initialized" in st.session_state:
                 del st.session_state[f"{prefix}initialized"]
            st.rerun()
