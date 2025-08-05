# ===============================================================
# ★★★ gijiroku_tool.py ＜デイリーパスワード版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime, timedelta, timezone # ★ 日付を扱う達人を召喚

# ===============================================================
# 専門家のメインの仕事 (新しいシステムに換装)
# ===============================================================
def show_tool(gemini_api_key):
    st.header("📝 議事録を作成", divider='rainbow')

    # --- セッションステートの初期化 ---
    prefix = "gijiroku_"
    if f"{prefix}transcript_text" not in st.session_state:
        st.session_state[f"{prefix}transcript_text"] = None
    if f"{prefix}usage_count" not in st.session_state:
        st.session_state[f"{prefix}usage_count"] = 0

    # ★★★ リミット回数を、ここで定義 ★★★
    usage_limit = 1 # ←←← ちゃろさんが、いつでも、ここの数字を変えられます！

    # --- 運命の分岐 ---
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit

    if is_limit_reached:
        # ★★★ 聖域（アンロック・モード）の表示 ★★★
        st.success("🎉 たくさんのご利用、ありがとうございます！")
        st.info("このツールが、あなたの業務効率化の一助となれば幸いです。")
        st.warning("議事録の作成を続けるには、応援ページで「今日の合言葉（4桁の数字）」を確認し、入力してください。")
        
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        st.markdown(f'<a href="{portal_url}" target="_blank">応援ページで「今日の合言葉」を確認する →</a>', unsafe_allow_html=True)
        st.divider()

        password_input = st.text_input("ここに「今日の合言葉」を入力してください:", type="password", key=f"{prefix}password_input")
        if st.button("議事録の作成回数をリセットする", key=f"{prefix}unlock_button"):
            # ★★★ 今日の正しい「4桁の数字」を自動生成 ★★★
            JST = timezone(timedelta(hours=+9))
            today_int = int(datetime.now(JST).strftime('%Y%m%d'))
            seed_str = st.secrets.get("unlock_seed", "0")
            seed_int = int(seed_str) if seed_str.isdigit() else 0
            correct_password = str((today_int + seed_int) % 10000).zfill(4)
            
            if password_input == correct_password:
                st.session_state[f"{prefix}usage_count"] = 0
                st.balloons()
                st.success("ありがとうございます！議事録の作成回数がリセットされました。")
                time.sleep(2)
                st.rerun()
            else:
                st.error("合言葉が違うようです。応援ページで、もう一度ご確認ください。")

    else:
        # --- 通常モード (上限に達していない場合) ---
        st.info("会議などを録音した音声ファイルをアップロードすると、AIが文字起こしを行い、テキストファイルとしてダウンロードできます。")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、議事録を作成できます。")

        uploaded_file = st.file_uploader("議事録を作成したい音声ファイルをアップロードしてください:", type=['wav', 'mp3', 'm4a', 'flac'], key=f"{prefix}uploader")
        
        # ★★★ 処理の開始を、ボタンクリックから、ファイルのアップロード完了時に変更 ★★★
        if uploaded_file is not None:
            if not gemini_api_key:
                st.error("サイドバーでGemini APIキーを設定してください。")
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
                            st.session_state[f"{prefix}usage_count"] += 1
                            st.session_state[f"{prefix}transcript_text"] = response.text
                            # 最後の検索でrerunを呼ぶと、結果表示後に即座に利用制限画面に切り替わる
                            st.success("文字起こしが完了しました！")
                            if st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit:
                                time.sleep(1) # 完了メッセージを少しだけ表示
                                st.rerun()
                        else:
                            st.error("AIからの応答が空でした。音声が認識できなかった可能性があります。")

                    except Exception as e:
                        st.error(f"文字起こし中にエラーが発生しました: {e}")
            # ★★★ 処理が終わったら、アップロードされたファイルをクリアする ★★★
            # これにより、同じファイルを再アップロードして、再度処理をかけることが可能になる
            st.session_state[f"{prefix}uploader"] = None


    # --- 結果表示部分は、常に、最新の結果を表示 (成功部分は、完全に保護) ---
    if st.session_state[f"{prefix}transcript_text"]:
        st.text_area("文字起こし結果", st.session_state[f"{prefix}transcript_text"], height=300, key=f"{prefix}textarea")
        st.download_button(
            label="議事録をテキストファイルでダウンロード (.txt)",
            data=st.session_state[f"{prefix}transcript_text"].encode('utf-8-sig'),
            file_name="transcript.txt",
            mime="text/plain",
            key=f"{prefix}download_button"
        )
