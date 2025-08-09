# =====================================================================
# ★★★ job_search_tool.py ＜app.pyから認証情報を受け取る最終版＞ ★★★
# =====================================================================
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timezone, timedelta

# ★ 認証関連のライブラリ ★
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText

# --- Webスクレイピング関数 ---
def search_jobs_on_kyujinbox(keywords):
    search_url = f"https://xn--pckua2a7gp15o89zb.com/kw-{'+'.join(keywords.split())}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        with st.spinner(f"「{keywords}」の案件を求人ボックスで検索中..."):
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            job_cards = soup.find_all("div", class_=lambda c: c and ("result_card_" in c or "p-job_list-item" in c))
            results = []
            if not job_cards:
                return []
            for card in job_cards:
                title_tag = card.find("h3", class_=lambda c: c and "heading_title" in c)
                company_tag = card.find("span", class_=lambda c: c and "text_company" in c)
                link_tag = card.find("a", href=True)
                title = title_tag.text.strip() if title_tag else "タイトル不明"
                company = company_tag.text.strip() if company_tag else "会社名不明"
                url = "https://xn--pckua2a7gp15o89zb.com" + link_tag['href'] if link_tag and link_tag['href'].startswith('/') else link_tag['href'] if link_tag else "URL不明"
                results.append({"案件タイトル": title, "会社名": company, "詳細URL": url})
        return results
    except Exception as e:
        st.error(f"情報の取得中にエラーが発生しました: {e}")
        return None

# --- メール送信関数 ---
def send_gmail_with_oauth(credentials, keywords, results_df):
    try:
        service = build('gmail', 'v1', credentials=credentials)
        user_info = service.users().getProfile(userId='me').execute()
        recipient_address = user_info['emailAddress']

        with st.spinner(f"{recipient_address} 宛にメールを送信しています..."):
            subject = f"【新着案件ウォッチャー】「{keywords}」の検索結果"
            body = f"{user_info.get('name', 'ユーザー')}さん、こんにちは！\n\n"
            body += f"ご指定のキーワード「{keywords}」での検索結果をお知らせします。\n\n"
            body += "--- 検索結果 ---\n"
            body += results_df.to_string(index=False)
            body += "\n\n"
            body += "------------------\n\n"
            body += "このメールは、Multi-Tool Portalから自動送信されました。\n"

            message = MIMEText(body, 'plain', 'utf-8')
            message['to'] = recipient_address
            message['from'] = f"Multi-Tool Portal <{recipient_address}>"
            message['subject'] = subject

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'raw': encoded_message}
            service.users().messages().send(userId='me', body=create_message).execute()
        
        st.success(f"{recipient_address} に検索結果を送信しました！")
    except Exception as e:
        st.error(f"メール送信中にエラーが発生しました: {e}")
        st.code(traceback.format_exc())

# --- ツール本体のメイン関数 ---
def show_tool(credentials):
    st.header("💼 新着案件ウォッチャー", divider='rainbow')
    
    if not credentials:
        st.warning("認証情報がありません。アプリを再読み込みしてください。")
        return

    prefix = "job_search_"
    if f"{prefix}results" not in st.session_state:
        st.session_state[f"{prefix}results"] = None

    with st.form("job_search_form"):
        keywords = st.text_input("検索キーワード", placeholder="例: Python 業務委託")
        submitted = st.form_submit_button("🔍 このキーワードで検索する", type="primary", use_container_width=True)
    
    if submitted:
        if not keywords:
            st.warning("キーワードを入力してください。")
        else:
            search_results = search_jobs_on_kyujinbox(keywords)
            st.session_state[f"{prefix}results"] = search_results
            st.session_state[f"{prefix}keywords"] = keywords
            if search_results:
                 st.success(f"{len(search_results)} 件の案件が見つかりました！")
            else:
                 st.info("該当する案件は見つかりませんでした。")
            time.sleep(1); st.rerun()

    if st.session_state.get(f"{prefix}results") is not None:
        st.divider()
        results = st.session_state[f"{prefix}results"]
        if results:
            st.subheader(f"「{st.session_state[f'{prefix}keywords']}」の検索結果")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            if st.button("📧 この結果を自分のGmailに送信する", type="primary", use_container_width=True):
                send_gmail_with_oauth(credentials, st.session_state[f'{prefix}keywords'], df)

        if st.button("検索結果をクリア", key=f"{prefix}clear_results"):
            st.session_state[f"{prefix}results"] = None
            st.rerun()
