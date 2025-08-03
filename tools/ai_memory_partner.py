import streamlit as st
import google.generativeai as genai
import time
from google.api_core import exceptions
import json

# streamlit_mic_recorderのインポートをtry-catchで囲む
try:
    from streamlit_mic_recorder import mic_recorder
    MIC_RECORDER_AVAILABLE = True
except ImportError:
    MIC_RECORDER_AVAILABLE = False
    st.error("streamlit_mic_recorderがインストールされていません。pip install streamlit-mic-recorderでインストールしてください。")

# --- プロンプト ---
SYSTEM_PROMPT_TRUE_FINAL = """
# ...（プロンプトは変更なし）...
"""

# --- 補助関数 ---
def dialogue_with_gemini(content_to_process, api_key):
    """
    Gemini APIとの対話を処理する関数
    この部分は元のコードと同じと仮定
    """
    try:
        # ここに元のdialogue_with_gemini関数の処理を記述
        # 仮の戻り値（実際の実装に置き換えてください）
        original_input_display = "ユーザーの入力"
        ai_response_text = "AIの応答"
        return original_input_display, ai_response_text
    except Exception as e:
        st.error(f"Gemini APIでエラーが発生しました: {str(e)}")
        return None, None

# --- メインの仕事 ---
def show_tool(gemini_api_key, localS_object):
    """
    認知予防ツールのメイン表示関数
    """
    
    # デバッグ情報を表示（問題解決後は削除可能）
    with st.expander("🔧 デバッグ情報", expanded=False):
        st.write(f"Gemini APIキー設定済み: {bool(gemini_api_key)}")
        st.write(f"localS_object: {type(localS_object)}")
        st.write(f"マイクレコーダー利用可能: {MIC_RECORDER_AVAILABLE}")
    
    # localS_objectの安全チェック
    if localS_object is None:
        st.error("ローカルストレージオブジェクトが設定されていません。")
        return
    
    localS = localS_object
    prefix = "cc_"
    storage_key_results = f"{prefix}results"

    # URLパラメータによる制限解除
    if st.query_params.get("unlocked") == "true":
        st.session_state[f"{prefix}usage_count"] = 0
        st.query_params.clear()
        try:
            retrieved_results = localS.getItem(storage_key_results)
            if retrieved_results:
                st.session_state[storage_key_results] = retrieved_results
        except Exception as e:
            st.warning(f"履歴の復元でエラーが発生しました: {str(e)}")
            st.session_state[storage_key_results] = []
        st.toast("おかえりなさい！またお話できることを、楽しみにしておりました。")
        st.balloons()

    # メインヘッダー
    st.header("❤️ 認知予防ツール", divider='rainbow')

    # セッション状態の初期化
    try:
        if f"{prefix}initialized" not in st.session_state:
            retrieved_data = localS.getItem(storage_key_results) if localS else []
            st.session_state[storage_key_results] = retrieved_data or []
            st.session_state[f"{prefix}initialized"] = True
    except Exception as e:
        st.warning(f"データの初期化でエラーが発生しました: {str(e)}")
        st.session_state[storage_key_results] = []
        st.session_state[f"{prefix}initialized"] = True
    
    # その他のセッション状態初期化
    if f"{prefix}last_mic_id" not in st.session_state: 
        st.session_state[f"{prefix}last_mic_id"] = None
    if f"{prefix}text_to_process" not in st.session_state: 
        st.session_state[f"{prefix}text_to_process"] = None
    if f"{prefix}last_input" not in st.session_state: 
        st.session_state[f"{prefix}last_input"] = ""
    if f"{prefix}usage_count" not in st.session_state: 
        st.session_state[f"{prefix}usage_count"] = 0

    usage_limit = 3
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit
    audio_info = None

    # 使用制限チェック
    if is_limit_reached:
        st.success("🎉 たくさんお話いただき、ありがとうございます！")
        st.info("このツールが、あなたの心を温める一助となれば幸いです。\n\n応援ページへ移動することで、またお話を続けることができます。")
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        st.link_button("応援ページに移動して、お話を続ける", portal_url, type="primary", use_container_width=True)
    else:
        # メイン機能の表示
        st.info("下のボタンを押して、昔の楽しかった思い出や、頑張ったお話など、なんでも自由にお話しください。")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、お話できます。")
        
        # Gemini APIキーのチェック
        if not gemini_api_key:
            st.warning("⚠️ サイドバーでGemini APIキーを設定してください。")
            st.info("APIキーを設定すると、音声・テキスト入力機能が利用できるようになります。")
        
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        # ★★★【聖杯の、封印】危険な、武器を、折りたたみメニューに、封印します ★★★
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        with st.expander("マイクで話す、または、文章を、入力する", expanded=True):
            def handle_text_input():
                st.session_state[f"{prefix}text_to_process"] = st.session_state.cc_text
            
            # 聖杯（マイク）と、テキスト入力は、この、聖域の、中でだけ、姿を現します。
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if MIC_RECORDER_AVAILABLE:
                    try:
                        audio_info = mic_recorder(
                            start_prompt="🟢 話し始める", 
                            stop_prompt="🔴 話を聞いてもらう", 
                            key=f'{prefix}mic', 
                            format="webm"
                        )
                    except Exception as e:
                        st.error(f"マイクでエラーが発生しました: {str(e)}")
                        audio_info = None
                else:
                    st.warning("マイク機能は利用できません")
            
            with col2:
                st.text_input(
                    "または、ここに文章を入力してEnter...", 
                    key=f"{prefix}text", 
                    on_change=handle_text_input
                )

    # 入力処理
    content_to_process = None
    
    # 音声入力の処理
    if audio_info and audio_info.get('id') != st.session_state.get(f"{prefix}last_mic_id"):
        content_to_process = audio_info.get('bytes')
        st.session_state[f"{prefix}last_mic_id"] = audio_info.get('id')
    
    # テキスト入力の処理
    elif st.session_state.get(f"{prefix}text_to_process"):
        content_to_process = st.session_state.get(f"{prefix}text_to_process")
        st.session_state[f"{prefix}text_to_process"] = None

    # 新しい入力の処理
    if content_to_process and content_to_process != st.session_state.get(f"{prefix}last_input"):
        st.session_state[f"{prefix}last_input"] = content_to_process
        
        if not gemini_api_key:
            st.error("サイドバーでGemini APIキーを設定してください。")
        else:
            with st.spinner("AI が考えています..."):
                try:
                    original, ai_response = dialogue_with_gemini(content_to_process, gemini_api_key)
                    
                    if original and ai_response:
                        # 使用回数を増加
                        st.session_state[f"{prefix}usage_count"] += 1
                        
                        # 結果を保存
                        new_result = {"original": original, "response": ai_response}
                        st.session_state[storage_key_results].insert(0, new_result)
                        
                        # ローカルストレージに保存
                        try:
                            localS.setItem(storage_key_results, st.session_state[storage_key_results])
                        except Exception as e:
                            st.warning(f"データの保存でエラーが発生しました: {str(e)}")
                        
                        st.rerun()
                    else:
                        st.error("AIからの応答を取得できませんでした。")
                        st.session_state[f"{prefix}last_input"] = ""
                        
                except Exception as e:
                    st.error(f"処理中にエラーが発生しました: {str(e)}")
                    st.session_state[f"{prefix}last_input"] = ""

    # 会話履歴の表示
    if st.session_state.get(storage_key_results):
        st.write("---")
        st.subheader("💬 会話履歴")
        
        for i, result in enumerate(st.session_state[storage_key_results]):
            with st.chat_message("user"):
                st.write(result.get('original', '入力内容が見つかりません'))
            with st.chat_message("assistant"):
                st.write(result.get('response', '応答が見つかりません'))
        
        # 履歴クリアボタン
        if st.button("会話の履歴をクリア", key=f"{prefix}clear_history"):
            st.session_state[storage_key_results] = []
            st.session_state[f"{prefix}last_input"] = ""
            
            try:
                localS.setItem(storage_key_results, [])
            except Exception as e:
                st.warning(f"履歴のクリアでエラーが発生しました: {str(e)}")
            
            # 創生の記憶もリセット
            if f"{prefix}initialized" in st.session_state:
                del st.session_state[f"{prefix}initialized"]
            
            st.rerun()

# メイン実行部分（例）
if __name__ == "__main__":
    # サイドバーでの設定例
    with st.sidebar:
        st.header("設定")
        gemini_api_key = st.text_input("Gemini APIキー", type="password")
        
        # ダミーのlocalS_objectクラス（実際の実装に置き換えてください）
        class DummyLocalStorage:
            def __init__(self):
                self.storage = {}
            
            def getItem(self, key):
                return self.storage.get(key)
            
            def setItem(self, key, value):
                self.storage[key] = value
        
        # 実際のアプリではここで適切なlocalS_objectを初期化してください
        localS_object = DummyLocalStorage()
    
    # ツールの表示
    show_tool(gemini_api_key, localS_object)
