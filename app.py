# ===================================================================
# ★★★ app.py ＜ハイブリッドモデル・ポータル最終版＞ ★★★
# ===================================================================
import streamlit as st
import time

# ★★★ 新しいツール名をインポート ★★★
from tools import career_analyzer_tool, translator_tool # 他のツールも必要に応じてインポート

# ===============================================================
# Section 1: アプリの基本設定
# ===============================================================
st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

# ===============================================================
# Section 2: UI描画とツール起動
# ===============================================================
with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()
    
    # ★ ツール選択 ★
    st.radio(
        "利用するツールを選択してください:",
        ("👔 AIキャリアアナリスト", "🤝 翻訳ツール"), # 他のツールもここに追加
        key="tool_selection_sidebar"
    )
    st.divider()
    
    # ★ APIキー管理フォーム ★
    # (セッションステートで、各キーを管理)
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
    if 'serpapi_api_key' not in st.session_state:
        st.session_state.serpapi_api_key = "" # ユーザーキーは最初は空

    with st.expander("⚙️ APIキーの設定", expanded=False):
        with st.form("api_key_form"):
            st.session_state.gemini_api_key = st.text_input(
                "Gemini APIキー (翻訳ツールなどで使用)", 
                type="password", 
                value=st.session_state.gemini_api_key
            )
            st.session_state.serpapi_api_key = st.text_input(
                "【任意】SerpApiキー (アナリストの利用回数無制限化)", 
                type="password", 
                value=st.session_state.serpapi_api_key,
                help="通常は不要です。共有アクセスが混み合った場合に設定すると、ご自身の無料枠(月100回)で安定して利用できます。"
            )
            
            submitted = st.form_submit_button("💾 保存", use_container_width=True)
            if submitted:
                st.success("キーを保存しました！"); time.sleep(1); st.rerun()
        
    st.markdown("""
    <div style="font-size: 0.9em;">
    <a href="https://aistudio.google.com/app/apikey" target="_blank">Gemini APIキーの取得</a><br>
    <a href="https://serpapi.com/manage-api-key" target="_blank">SerpApiキーの取得</a>
    </div>
    """, unsafe_allow_html=True)

# --- メインコンテンツ ---
tool_choice = st.session_state.get("tool_selection_sidebar")

if tool_choice == "👔 AIキャリアアナリスト":
    # ★★★ ハイブリッドモデルの心臓部 ★★★
    # ユーザーキーが設定されていればそれを使い、なければ開発者の共有キーを使う
    user_serpapi_key = st.session_state.get("serpapi_api_key", "")
    developer_serpapi_key = st.secrets.get("SERPAPI_API_KEY", "")
    final_serpapi_key = user_serpapi_key if user_serpapi_key else developer_serpapi_key
    
    career_analyzer_tool.show_tool(
        gemini_api_key=st.session_state.get("gemini_api_key", ""),
        serpapi_api_key=final_serpapi_key
    )
elif tool_choice == "🤝 翻訳ツール":
    translator_tool.show_tool(gemini_api_key=st.session_state.get("gemini_api_key", ""))
else:
    st.info(f"「{tool_choice}」ツールは現在準備中です。")
