import streamlit as st
import json
from pathlib import Path
import time

# app.pyと共通の永続化機能をここでも利用します
STATE_FILE = Path("multitool_state.json")

def read_app_state():
    if STATE_FILE.exists():
        with STATE_FILE.open("r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def write_app_state(data):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def show_tool():
    """Gemini APIキーをユーザーが自分で簡単に取得するための支援ツール"""
    st.header("💎 Gemini APIキー 簡単設定ツール", divider='rainbow')
    st.info("""
    このアプリのAI機能（お小遣い管理の自動解析など）を利用するには、Googleの「Gemini APIキー」が必要です。
    幸い、キーの取得はとても簡単です！ 下のガイドに従って設定してみましょう。
    """)
    st.divider()

    # --- 現在保存されているキーの確認と削除 ---
    app_state = read_app_state()
    saved_key = app_state.get('gemini_api_key', '')

    if saved_key:
        st.success("✅ Gemini APIキーは既に設定されています。")
        col1, col2 = st.columns([3, 1])
        col1.text_input("設定済みのキー", value=saved_key, type="password", disabled=True)
        if col2.button("🗑️ キーを削除", use_container_width=True, key="gemini_key_delete"):
            del app_state['gemini_api_key']
            write_app_state(app_state)
            st.success("キーを削除しました。"); time.sleep(1); st.rerun()
        st.caption("新しいキーを設定したい場合は、一度削除してください。")
        return

    # --- キーが未設定の場合のガイド ---
    st.subheader("簡単1ステップでAPIキーを取得！")
    st.markdown("""
    1. **下の「💎 APIキー取得ページを開く」ボタンをクリックしてください。**
       - Googleアカウントへのログインが求められる場合があります。
    2. **移動したページで、「Create API key in new project」ボタンを押すと、すぐにキーが作成されます。**
    3. **表示された長い文字列（これがAPIキーです）をコピーしてください。**
    4. **コピーしたキーを、下のボックスに貼り付けて保存すれば完了です！**
    """)

    # これがGemini APIキー取得のための究極の「魔法のリンク」です！
    ai_studio_url = "https://aistudio.google.com/app/apikey"
    
    st.markdown(f'<a href="{ai_studio_url}" target="_blank" style="display: inline-block; margin-top: 10px; margin-bottom: 20px; padding: 12px 20px; background-color: #1a73e8; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">💎 APIキー取得ページを開く</a>', unsafe_allow_html=True)

    with st.form("gemini_api_key_form"):
        gemini_api_key_input = st.text_input("ここにGemini APIキーを貼り付け →", type="password")
        submitted = st.form_submit_button("💾 このキーを保存する", type="primary", use_container_width=True)

        if submitted:
            # Geminiキーも"AIza"で始まることが多い
            if gemini_api_key_input.startswith("AIza"):
                app_s = read_app_state()
                app_s['gemini_api_key'] = gemini_api_key_input
                write_app_state(app_s)
                st.success("✅ Gemini APIキーを保存しました！")
                st.balloons()
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ キーの形式が正しくないようです。もう一度確認してください。")
