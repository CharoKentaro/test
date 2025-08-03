import streamlit as st
from streamlit_local_storage import LocalStorage
import time

# （... 冒頭の import 文は、変更ありません ...）
from tools import translator_tool, okozukai_recorder_tool, calendar_tool, gijiroku_tool, kensha_no_kioku_tool

st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

# （... サイドバーのコードも、変更ありません ...）
with st.sidebar:
    # ...
    pass

# ★★★★★ 『偉大なる、仕分け人』の、最終契約書 ★★★★★
# （... 他のツールの呼び出し部分は、変更ありません ...）
if st.session_state.tool_selection == "🤝 翻訳ツール":
    # ...
    pass
# （...）

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★【真・最終形態】新生児の世界に、記憶を、与える、『創生の儀式』 ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
elif st.session_state.tool_selection == "❤️ 認知予防ツール":
    
    import google.generativeai as genai
    from streamlit_mic_recorder import mic_recorder

    # （... SYSTEM_PROMPT と dialogue_with_gemini 関数は、変更ありません ...）
    SYSTEM_PROMPT_TRUE_FINAL = """..."""
    def dialogue_with_gemini(content_to_process, api_key):
        # ...
        return original_input_display, ai_response_text

    prefix = "cc_"
    storage_key_results = f"{prefix}results"

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★【最重要】『創生の儀式』 - 全ての、世界の、始まりに、執り行われる、絶対の、法 ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # この儀式は、この世界（タブ）が、生まれた、最初の、一瞬にしか、実行されません。
    if f"{prefix}initialized" not in st.session_state:
        # まず、聖なる石版（LocalStorage）から、帝国の、真の、歴史を、読み込みます。
        retrieved_results = localS.getItem(storage_key_results)
        # そして、この世界の、魂（session_state）に、その、歴史を、刻み込みます。
        st.session_state[storage_key_results] = retrieved_results if retrieved_results else []
        # 最後に、創生の儀式が、完了したことを、宣言し、この世界に、アイデンティティを、与えます。
        st.session_state[f"{prefix}initialized"] = True
        
        # 帰還者への、特別な、祝福も、この、聖域で、行います。
        if st.query_params.get("unlocked") == "true":
            st.session_state[f"{prefix}usage_count"] = 0
            st.query_params.clear()
            st.toast("おかえりなさい！応援、ありがとうございました！")
            st.balloons()
            # 儀式の、完了後、ページを、再描画し、安定した、世界を、表示します。
            time.sleep(1.5)
            st.rerun()

    # --- これより先は、記憶を、確立した、安定した、世界 ---
    st.header("❤️ 認知予防ツール", divider='rainbow')

    # （... 帰還者の、祝福ロジックは、『創生の儀式』に、吸収されたため、ここからは、削除します ...）
    
    # セッション管理（これらは、創生の儀式で、既に、確立されています）
    if f"{prefix}last_mic_id" not in st.session_state: st.session_state[f"{prefix}last_mic_id"] = None
    if f"{prefix}text_to_process" not in st.session_state: st.session_state[f"{prefix}text_to_process"] = None
    if f"{prefix}last_input" not in st.session_state: st.session_state[f"{prefix}last_input"] = ""
    if f"{prefix}usage_count" not in st.session_state: st.session_state[f"{prefix}usage_count"] = 0

    # （... is_limit_reached, UI表示、入力ハンドリング、履歴表示など、以下のコードは、全て、同じです ...）
    usage_limit = 3
    # ...
    # ...
    if st.session_state.get(storage_key_results):
        # ...
        if st.button("会話の履歴をクリア", key=f"{prefix}clear_history"):
            st.session_state[storage_key_results] = []
            st.session_state[f"{prefix}last_input"] = ""
            # 歴史を消す時は、もちろん、聖なる石版も、空にします。
            localS.setItem(storage_key_results, [])
            # ★★★ そして、この世界の、創生の、記憶も、リセットし、再び、まっさらな、状態から、始めます ★★★
            del st.session_state[f"{prefix}initialized"]
            st.rerun()
