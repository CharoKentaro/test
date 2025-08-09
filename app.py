# ===============================================================
# ★★★ app.py ＜ちゃろさんの認証ロジック統合・最終版＞ ★★★
# ===============================================================
import streamlit as st
import json
from pathlib import Path
import time
import pandas as pd

# ★★★ 認証に必要なライブラリをインポート ★★★
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import requests
import traceback

# ★★★ ツールをインポート ★★★
from tools import translator_tool, calendar_tool, gijiroku_tool, kensha_no_kioku_tool, ai_memory_partner_tool, job_search_tool

# ===============================================================
# Section 1: アプリの基本設定と永続化機能
# ===============================================================
st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

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

# ===============================================================
# Section 2: Google認証機能
# ===============================================================

# --- 認証情報の準備 ---
try:
    CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
    REDIRECT_URI = st.secrets["REDIRECT_URI"] 
    SCOPE = [
        "openid", "https://www.googleapis.com/auth/userinfo.email", 
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/gmail.send"
    ]
except KeyError as e:
    st.error(f"重大なエラー: StreamlitのSecretsに {e} が設定されていません。")
    st.stop()

# --- 認証フローとログアウト関数 ---
def get_google_auth_flow():
    return Flow.from_client_config(
        client_config={ "web": { "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
                                 "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token",
                                 "redirect_uris": [REDIRECT_URI], }},
        scopes=SCOPE, redirect_uri=REDIRECT_URI)

def google_logout():
    st.session_state.pop("google_credentials", None)
    st.session_state.pop("google_user_info", None)
    st.success("ログアウトしました。"); time.sleep(1); st.rerun()

# --- 認証コールバック処理 ---
if "code" in st.query_params and "google_credentials" not in st.session_state:
    try:
        with st.spinner("Google認証処理中..."):
            flow = get_google_auth_flow()
            flow.fetch_token(code=st.query_params["code"])
            
            creds_dict = {
                'token': flow.credentials.token,
                'refresh_token': flow.credentials.refresh_token,
                'token_uri': flow.credentials.token_uri,
                'client_id': flow.credentials.client_id,
                'client_secret': flow.credentials.client_secret,
                'scopes': flow.credentials.scopes
            }
            st.session_state["google_credentials"] = creds_dict
            
            creds = Credentials(**creds_dict)
            user_info_response = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {creds.token}"})
            user_info_response.raise_for_status()
            st.session_state["google_user_info"] = user_info_response.json()

            st.query_params.clear(); st.success("✅ Google認証が完了しました！"); time.sleep(1); st.rerun()
    except Exception as e:
        st.error(f"Google認証中にエラーが発生しました: {e}"); st.query_params.clear()

# ===============================================================
# Section 3: UI描画とツール起動
# ===============================================================

# --- サイドバー ---
with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()

    if "google_user_info" not in st.session_state:
        st.info("各ツールを利用するには、Googleアカウントでのログインが必要です。")
        flow = get_google_auth_flow()
        authorization_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
        st.link_button("🗝️ Googleアカウントでログイン", authorization_url, use_container_width=True)
    else:
        user_info = st.session_state.get("google_user_info", {})
        st.success("✅ ログイン中")
        st.write(f"**ユーザー:** {user_info.get('name', 'N/A')}")
        st.write(f"**メール:** {user_info.get('email', 'N/A')}")
        if st.button("🔑 ログアウト", use_container_width=True):
            google_logout()
        
        st.divider()
        st.radio(
            "利用するツールを選択してください:",
            ("💼 新着案件ウォッチャー", "💰 お小遣い管理", "🤝 翻訳ツール", "📅 カレンダー登録", "📝 議事録作成", "🧠 賢者の記憶", "❤️ 認知予防ツール"),
            key="tool_selection_sidebar"
        )
    st.divider()
    st.markdown("""<div style="font-size: 0.9em;"><a href="https://aistudio.google.com/app/apikey" target="_blank">Gemini APIキーの取得はこちら</a></div>""", unsafe_allow_html=True)

# --- メインコンテンツ ---
if "google_user_info" not in st.session_state:
    st.header("ようこそ、Multi-Tool Portal へ！")
    st.info("👆 サイドバーにある「🗝️ Googleアカウントでログイン」ボタンを押して、始めてください。")
else:
    tool_choice = st.session_state.get("tool_selection_sidebar")
    credentials_dict = st.session_state.get("google_credentials")
    
    # ログイン情報を元に、ツールで使える形式の認証オブジェクトを作成
    creds = Credentials(**credentials_dict) if credentials_dict else None
    
    if tool_choice == "💼 新着案件ウォッチャー":
        job_search_tool.show_tool(credentials=creds)
    elif tool_choice == "💰 お小遣い管理":
        # このツールは認証を使わないので、そのまま呼び出す
        # okozukai_tool.show_tool() のような形
        st.warning("「お小遣い管理」ツールは現在準備中です。")
    elif tool_choice == "🤝 翻訳ツール":
        # このツールにAPIキーが必要なら、別途フォームを設けるか、
        # Secretsから読み込むなどして渡す必要があります。
        translator_tool.show_tool(gemini_api_key=st.secrets.get("GEMINI_API_KEY")) #例
    else:
        st.info(f"「{tool_choice}」ツールは現在準備中です。")
