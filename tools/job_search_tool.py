# =====================================================================
# ★★★ job_search_tool.py ＜ターゲットをIndeedに変更した最終版＞ ★★★
# =====================================================================
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import traceback
import urllib.parse 

# ★ 認証関連のライブラリ ★
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText

# ★★★ 新しい関数：Indeedから情報を取得 ★★★
def search_jobs_on_indeed(keywords):
    try:
        # IndeedのURL構造に合わせてキーワードをエンコード
        encoded_keywords = urllib.parse.quote_plus(keywords)
        search_url = f"https://jp.indeed.com/jobs?q={encoded_keywords}"
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        
        with st.spinner(f"「{keywords}」の案件をIndeedで検索中..."):
            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status() 
            soup = BeautifulSoup(response.content, "html.parser")

            # Indeedの求人カードは 'job_seen_beacon' という属性を持つことが多い
            job_cards = soup.find_all("div", class_="job_seen_beacon")

            results = []
            if not job_cards:
                st.info("Indeedで求人情報が見つかりませんでした。サイトの構造が変更されたか、ガードされている可能性があります。")
                return []

            for card in job_cards:
                # タイトルとURLを取得
                title_element = card.select_one('h2.jobTitle > a')
                if not title_element:
                    continue # タイトルがなければスキップ
                
                title = title_element.get_text(strip=True)
                url = "https://jp.indeed.com" + title_element['href']

                # 会社名を取得
                company_element = card.select_one('span.companyName')
                company = company_element.get_text(strip=True) if company_element else "会社名不明"

                results.append({"案件タイトル": title, "会社名": company, "詳細URL": url})
        return results
    except requests.exceptions.HTTPError as e:
        st.error(f"Indeedへのアクセス中にエラーが発生しました: {e}")
        st.warning("Indeedのガードが固いか、IPアドレスが一時的にブロックされている可能性があります。")
        return None
    except Exception as e:
        st.error(f"情報の取得中に予期せぬエラーが発生しました: {e}")
        return None

# --- メール送信関数 (変更なし) ---
def send_gmail_with_oauth(credentials, keywords, results_df):
    try:
        service = build('gmail', 'v1', credentials=credentials)
        user_info = service.users().getProfile(userId='me').execute()
        recipient_address = user_info['emailAddress']
        with st.spinner(f"{recipient_address} 宛にメールを送信しています..."):
            subject = f"【新着案件ウォッチャー】「{keywords}」の検索結果 (Indeed)"
            body = f"{user_info.get('name', 'ユーザー')}さん、こんにちは！\n\nご指定のキーワード「{keywords}」での検索結果をお知らせします。\n\n--- 検索結果 ---\n{results_df.to_string(index=False)}\n\n------------------\n\nこのメールは、Multi-Tool Portalから自動送信されました。\n"
            message = MIMEText(body, 'plain', 'utf-8')
            message['to'] = recipient_address
            message['from'] = f"Multi-Tool Portal <{recipient_address}>"; message['subject'] = subject
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().messages().send(userId='me', body={'raw': encoded_message}).execute()
        st.success(f"{recipient_address} に検索結果を送信しました！")
    except Exception as e:
        st.error(f"メール送信中にエラーが発生しました: {e}"); st.code(traceback.format_exc())

# --- ツール本体のメイン関数 ---
def show_tool(credentials):
    st.header("💼 新着案件ウォッチャー", divider='rainbow')
    st.info("検索対象を「Indeed」に変更しました。") # ユーザーにお知らせ
    if not credentials: st.warning("認証情報がありません。アプリを再読み込みしてください。"); return
    
    prefix = "job_search_";
    if f"{prefix}results" not in st.session_state: st.session_state[f"{prefix}results"] = None
    
    with st.form("job_search_form"):
        keywords = st.text_input("検索キーワード", placeholder="例: Python エンジニア リモート")
        submitted = st.form_submit_button("🔍 このキーワードで検索する", type="primary", use_container_width=True)
    
    if submitted:
        if not keywords: st.warning("キーワードを入力してください。")
        else:
            # ★★★ 呼び出す関数をIndeed用に変更 ★★★
            search_results = search_jobs_on_indeed(keywords)
            
            st.session_state[f"{prefix}results"] = search_results
            st.session_state[f"{prefix}keywords"] = keywords
            if search_results is None: pass
            elif not search_results: st.info("該当する案件は見つかりませんでした。")
            else: st.success(f"{len(search_results)} 件の案件が見つかりました！")
            time.sleep(1); st.rerun()
            
    if st.session_state.get(f"{prefix}results") is not None:
        st.divider(); results = st.session_state[f"{prefix}results"]
        if results:
            st.subheader(f"「{st.session_state[f'{prefix}keywords']}」の検索結果"); df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True, hide_index=True)
            if st.button("📧 この結果を自分のGmailに送信する", type="primary", use_container_width=True):
                send_gmail_with_oauth(credentials, st.session_state[f'{prefix}keywords'], df)
        if st.button("検索結果をクリア", key=f"{prefix}clear_results"):
            st.session_state[f"{prefix}results"] = None; st.rerun()
