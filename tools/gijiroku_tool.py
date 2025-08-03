import streamlit as st
import google.generativeai as genai
import time

# ===============================================================
# 専門家のメインの仕事 (応援システムを戴冠)
# ===============================================================
def show_tool(gemini_api_key):
    st.header("📝 議事録を作成", divider='rainbow')

    # --- ★★★【帰還者の祝福】★★★ ---
    if st.query_params.get("unlocked") == "true":
        st.session_state["gijiroku_usage_count"] = 0
        st.query_params.clear()
        st.toast("おかえりなさい！議事録の作成回数がリセットされました。")
        st.balloons()
        time.sleep(1)
        st.rerun()

    # --- セッションステートの初期化 ---
    prefix = "gijiroku_"
    if f"{prefix}transcript_text" not in st.session_state:
        st.session_state[f"{prefix}transcript_text"] = None
    
    # --- ★★★【門番の存在保証】★★★ ---
    if f"{prefix}usage_count" not in st.session_state:
        st.session_state[f"{prefix}usage_count"] = 0

    # --- ★★★【運命の分岐路】★★★ ---
    usage_limit = 5 # デフォルトで5回に設定
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit

    if is_limit_reached:
        st.success("🎉 たくさんのご利用、ありがとうございます！")
        st.info("このツールが、あなたの、業務効率化の、一助となれば幸いです。\n\n下のボタンから応援ページに移動することで、議事録の作成を続けることができます。")
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        st.link_button("応援ページに移動して、議事録作成を続ける", portal_url, type="primary")

    else:
        # --- 通常モード (上限に達していない場合) ---
        st.info("会議などを録音した音声ファイルをアップロードすると、AIが文字起こしを行い、テキストファイルとしてダウンロードできます。")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、議事録を作成できます。応援後、リセットされます。")

        uploaded_file = st.file_uploader("議事録を作成したい音声ファイルをアップロードしてください:", type=['wav', 'mp3', 'm4a', 'flac'], key=f"{prefix}uploader")
        
        if st.button("この音声ファイルから議事録を作成する", key=f"{prefix}submit_button"):
            if not gemini_api_key:
                st.error("サイドバーでGemini APIキーを設定してください。")
            elif uploaded_file is None:
                st.warning("音声ファイルをアップロードしてください。")
            else:
                with st.spinner("AIが音声を文字に変換しています。長い音声の場合、数分かかることがあります..."):
                    try:
                        genai.configure(api_key=gemini_api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        
                        audio_bytes = uploaded_file.getvalue()
                        audio_part = {"mime_type": uploaded_file.type, "data": audio_bytes}
                        prompt = "この日本語の音声を、話者分離（例：「スピーカーA:」「スピーカーB:」）を、意識しながら、できる限り正確に、文字に書き起こしてください。書き起こした日本語テキストのみを回答してください。"
                        
                        response = model.generate_content([prompt, audio_part])
                        
                        if response.text:
                            # ★★★【通行料の徴収】★★★
                            st.session_state[f"{prefix}usage_count"] += 1
                            st.session_state[f"{prefix}transcript_text"] = response.text
                            # 最後の検索でrerunを呼ぶと、結果表示後に即座に利用制限画面に切り替わる
                            if st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit:
                                st.rerun()
                        else:
                            st.error("AIからの応答が空でした。音声が認識できなかった可能性があります。")

                    except Exception as e:
                        st.error(f"文字起こし中にエラーが発生しました: {e}")

    # --- 結果表示部分は、分岐の外に出すことで、常に、最新の結果を表示します ---
    if st.session_state[f"{prefix}transcript_text"]:
        st.success("文字起こしが完了しました！")
        st.text_area("文字起こし結果", st.session_state[f"{prefix}transcript_text"], height=300, key=f"{prefix}textarea")
        st.download_button(
            label="議事録をテキストファイルでダウンロード (.txt)",
            data=st.session_state[f"{prefix}transcript_text"].encode('utf-8-sig'),
            file_name="transcript.txt",
            mime="text/plain",
            key=f"{prefix}download_button"
        )
