# --- 衝突回避のための接頭辞 ---
prefix = "translator_"

# --- セッションステートの初期化 ---
if f"{prefix}usage_count" not in st.session_state: st.session_state[f"{prefix}usage_count"] = 0
if f"{prefix}results" not in st.session_state: st.session_state[f"{prefix}results"] = []
if f"{prefix}last_mic_id" not in st.session_state: st.session_state[f"{prefix}last_mic_id"] = None
if f"{prefix}text_to_process" not in st.session_state: st.session_state[f"{prefix}text_to_process"] = None
if f"{prefix}last_input" not in st.session_state: st.session_state[f"{prefix}last_input"] = ""

# --- 応援機能のロジック ---
usage_limit = 1
is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit

# 応援ページから戻ってきたかをURLクエリパラメータで判定
if st.query_params.get("unlocked") == "true" and st.query_params.get("from") == "translator":
    st.session_state[f"{prefix}usage_count"] = 0
    st.query_params.clear() 
    st.toast("おかえりなさい！利用回数がリセットされました。")
    st.balloons(); time.sleep(1); st.rerun()

# --- UIロジックの分岐 ---
if is_limit_reached:
    # --- アンロック・モード ---
    st.success("🎉 たくさんのご利用、ありがとうございます！")
    st.info("このツールが、あなたの世界を広げる一助となれば幸いです。\n\n下のボタンから応援ページに移動することで、翻訳を続けることができます。")
    portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html?from=translator&unlocked=true"
    st.link_button("応援ページに移動して、翻訳を続ける", portal_url, type="primary", use_container_width=True)

else:
    # --- 通常モード ---
    st.info("マイクで日本語を話すか、テキストボックスに入力してください。ニュアンスの異なる3つの翻訳候補を提案します。")
    st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、提案を受けられます。")
    
    def handle_text_input():
        st.session_state[f"{prefix}text_to_process"] = st.session_state[f"{prefix}text_input_key"]
    
    col1, col2 = st.columns([1, 2])
    with col1: audio_info = mic_recorder(start_prompt="🎤 話し始める", stop_prompt="⏹️ 提案を受ける", key=f'{prefix}mic', format="webm")
    with col2: st.text_input("または、ここに日本語を入力してEnter...", key=f"{prefix}text_input_key", on_change=handle_text_input)

    content_to_process = None
    if audio_info and audio_info['id'] != st.session_state[f"{prefix}last_mic_id"]:
        content_to_process = audio_info['bytes']
        st.session_state[f"{prefix}last_mic_id"] = audio_info['id']
    elif st.session_state[f"{prefix}text_to_process"]:
        content_to_process = st.session_state[f"{prefix}text_to_process"]
        st.session_state[f"{prefix}text_to_process"] = None

    if content_to_process and content_to_process != st.session_state[f"{prefix}last_input"]:
        st.session_state[f"{prefix}last_input"] = content_to_process
        if not gemini_api_key:
            st.error("サイドバーでGemini APIキーを設定してください。")
        else:
            original, proposals_data = translate_with_gemini(content_to_process, gemini_api_key)
            if proposals_data and "candidates" in proposals_data:
                st.session_state[f"{prefix}usage_count"] += 1
                st.session_state[f"{prefix}results"].insert(0, {"original": original, "candidates": proposals_data["candidates"]})
                st.rerun()
            else:
                st.session_state[f"{prefix}last_input"] = ""

    if st.session_state[f"{prefix}results"]:
        st.divider()
        st.subheader("📜 翻訳履歴")
        for i, result in enumerate(st.session_state[f"{prefix}results"]):
            with st.container(border=True):
                st.markdown(f"**🇯🇵 あなたの入力:** {result['original']}")
                if "candidates" in result and isinstance(result["candidates"], list):
                    st.write("---")
                    cols = st.columns(len(result["candidates"]))
                    for col_index, candidate in enumerate(result["candidates"]):
                        with cols[col_index]:
                            nuance = candidate.get('nuance', 'N/A')
                            translation = candidate.get('translation', '翻訳エラー')
                            st.info(f"**{nuance}**")
                            st.success(translation)
        
        if st.button("翻訳履歴をクリア", key=f"{prefix}clear_history"):
            st.session_state[f"{prefix}results"] = []
            st.session_state[f"{prefix}last_input"] = ""
            st.rerun()
