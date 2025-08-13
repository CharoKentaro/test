import streamlit as st

def show_tool():
    """Gemini APIキーの取得方法を案内するための、純粋なヘルパーツール"""
    st.header("💎 Gemini APIキー 簡単設定ガイド", divider='rainbow')
    st.info("""
    このアプリのAI機能（お小遣い管理の自動解析など）を利用するには、Googleの「Gemini APIキー」が必要です。
    幸い、キーの取得はとても簡単です！ 下のガイドに従って設定してみましょう。
    """)
    st.divider()

    st.subheader("APIキーの取得と設定手順")

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★ ここが、ちゃろさんのご指示を反映した案内文です ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    st.markdown("""
    下の**「💎 APIキー取得ページを開く」**ボタンをクリックしてください。

    Googleアカウントへのログインが求められる場合があります。
    そうすると、画面の上のほうに**「Get API key」**という項目があるので、クリックしてください。
    （スマホからの場合は、ブラウザのメニューから「PC版で表示」などのチェックボックスにチェックをいれると、表示されると思います）
    
    移動したページで、**「Create API key in new project（APIキーを作成する）」**ボタンを押すと、すぐにキーが作成されます。
    
    表示された長い文字列（これがAPIキーです）をコピーしてください。
    
    > **【重要】** このAPIキーも、他人に知られないように厳重に管理してください。
    
    最後に、コピーしたAPIキーを、**このページの左側にあるサイドバーの「⚙️ APIキーの設定」の中に入力**し、「💾 保存」ボタンをクリックしてください。
    
    あなた以外にキーが知られることはなく、あなただけのローカルブラウザに安全に保存されます。
    """)

    ai_studio_url = "https://aistudio.google.com/app/apikey"
    st.markdown(f'<a href="{ai_studio_url}" target="_blank" style="display: inline-block; margin-top: 20px; padding: 12px 20px; background-color: #1a73e8; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">💎 APIキー取得ページを開く</a>', unsafe_allow_html=True)
    
    st.divider()
    st.success("キーをサイドバーに設定したら、他のツールを使ってみましょう！")
