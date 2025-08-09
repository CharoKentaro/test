# ===============================================================
# ★★★ job_search_tool.py ＜新着案件ウォッチャー・基本版＞ ★★★
# ===============================================================
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# --- Webスクレイピング関数 (求人ボックス特化版) ---
def search_jobs_on_kyujinbox(keywords):
    """
    求人ボックスでキーワード検索を行い、結果をリストで返す。
    """
    # キーワードをURLエンコードされた形式に変換
    search_url = f"https://xn--pckua2a7gp15o89zb.com/kw-{'+'.join(keywords.split())}"
    headers = {
        # スクレイピング対策を回避するためのユーザーエージェント
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        with st.spinner(f"「{keywords}」の案件を求人ボックスで検索中..."):
            # サイトにアクセス
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status() # HTTPエラーがあれば例外を発生させる
            
            # HTMLを解析
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 求人情報が書かれているカード要素をすべて取得
            # ※サイトの構造が変わると、ここのクラス名が変わる可能性がある
            job_cards = soup.find_all("div", class_=lambda c: c and ("result_card_" in c or "p-job_list-item" in c))

            results = []
            if not job_cards:
                st.warning("求人情報を見つけられませんでした。サイトの構造が変更されたか、キーワードに合う求人がない可能性があります。")
                return []

            # 各カードから情報を抽出
            for card in job_cards:
                title_tag = card.find("h3", class_=lambda c: c and "heading_title" in c)
                company_tag = card.find("span", class_=lambda c: c and "text_company" in c)
                link_tag = card.find("a", href=True)

                title = title_tag.text.strip() if title_tag else "タイトル不明"
                company = company_tag.text.strip() if company_tag else "会社名不明"
                
                # URLが相対パス（/から始まる）の場合、ドメイン名を補完して絶対パスにする
                url = "https://xn--pckua2a7gp15o89zb.com" + link_tag['href'] if link_tag and link_tag['href'].startswith('/') else link_tag['href'] if link_tag else "URL不明"

                results.append({
                    "案件タイトル": title,
                    "会社名": company,
                    "詳細URL": url,
                })
        
        return results

    except requests.exceptions.RequestException as e:
        st.error(f"ネットワークエラーが発生しました: {e}")
        return None
    except Exception as e:
        st.error(f"情報の取得中に予期せぬエラーが発生しました: {e}")
        return None


# --- メイン関数 ---
def show_tool(gemini_api_key): # APIキーは将来の拡張用に引数は残します
    st.header("💼 新着案件ウォッチャー", divider='rainbow')
    st.info("キーワードを入力して、「求人ボックス」から新しい仕事の機会を見つけましょう。")

    prefix = "job_search_"
    
    # セッションステートの初期化
    if f"{prefix}results" not in st.session_state:
        st.session_state[f"{prefix}results"] = None

    # --- 入力フォーム ---
    with st.form("job_search_form"):
        keywords = st.text_input(
            "検索キーワード",
            placeholder="例: Python 業務効率化 業務委託",
            help="複数のキーワードはスペースで区切ってください。"
        )
        submitted = st.form_submit_button("🔍 このキーワードで検索する", type="primary", use_container_width=True)

    if submitted:
        if not keywords:
            st.warning("キーワードを入力してください。")
        else:
            search_results = search_jobs_on_kyujinbox(keywords)
            # 検索結果をセッションステートに保存
            st.session_state[f"{prefix}results"] = search_results
            if search_results:
                 st.success(f"{len(search_results)} 件の案件が見つかりました！")
            time.sleep(1)
            st.rerun()

    # --- 結果表示 ---
    if st.session_state[f"{prefix}results"] is not None:
        st.divider()
        st.subheader("📊 検索結果")
        
        results = st.session_state[f"{prefix}results"]
        if not results:
            st.info("該当する案件は見つかりませんでした。キーワードを変えて試してみてください。")
        else:
            # Pandas DataFrameで見やすく表示
            df = pd.DataFrame(results)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                # URLをクリック可能にする設定（将来的な改善案）
                # column_config={"詳細URL": st.column_config.LinkColumn("詳細URL")}
            )

        if st.button("検索結果をクリア", key=f"{prefix}clear_results"):
            st.session_state[f"{prefix}results"] = None
            st.rerun()
