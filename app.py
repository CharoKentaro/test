import streamlit as st
from streamlit_local_storage import LocalStorage
import time

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★【英雄の、再召喚】本物の、第六の英雄を、正式に、帝国へ、召喚します ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
from tools import translator_tool, okozukai_recorder_tool, calendar_tool, gijiroku_tool, kensha_no_kioku_tool, ai_memory_partner_tool

st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()

    # ★★★【王位継承法】 - この、完璧な、統治法は、そのままです ★★★
    st.radio(
        "利用するツールを選択してください:",
        ("🤝 翻訳ツール", "💰 お小遣い管理", "📅 AI秘書", "📝 議事録作成", "🧠 賢者の記憶", "❤️ 認知予防ツール"),
        key="tool_selection",
        index=0
    )
    
    # （...以降の、サイドバーのコードは、完璧なので、変更ありません...）
    localS = LocalStorage()
    # ...
    pass

# ★★★★★ 『偉大なる、仕分け人』は、今度こそ、本物の、英雄に、出会う ★★★★★
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
# ★★★【亡霊の、完全祓除】 - 王宮は、浄化され、英雄を、ただ、信じる ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
elif st.session_state.tool_selection == "❤️ 認知予防ツール":
    # 王宮の中には、もはや、英雄の、機能は、一切、ありません。
    # ただ、兵舎にいる、英雄を、呼び出し、仕事に、必要な、道具を、渡すだけです。
    ai_memory_partner_tool.show_tool(
        gemini_api_key=st.session_state.get('gemini_api_key', ''),
        localS_object=localS
    )
