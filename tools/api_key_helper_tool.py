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
    """Google Maps APIキーをユーザーが自分で簡単に取得するための支援ツール"""
    st.header("🔑 Google Maps APIキー 簡単設定ツール", divider='rainbow')
    st.info("""
    このツールは、あなたのGoogleアカウントでGoogle Maps APIキーを簡単に取得するためのお手伝いをします。
    **ここで作成されるAPIキーやプロジェクトの情報は、あなたのGoogleアカウントに紐付きます。**
    利用料金や管理責任はご自身にあることをご理解の上、ご利用ください。
    """)
    st.divider()

    # --- 現在保存されているキーの確認と削除 ---
    app_state = read_app_state()
    saved_key = app_state.get('google_maps_api_key', '')

    if saved_key:
        st.success("✅ Google Maps APIキーは既に設定されています。")
        col1, col2 = st.columns([3, 1])
        col1.text_input("設定済みのキー", value=saved_key, type="password", disabled=True)
        if col2.button("🗑️ キーを削除", use_container_width=True):
            del app_state['google_maps_api_key']
            write_app_state(app_state)
            st.success("キーを削除しました。"); time.sleep(1); st.rerun()
        st.caption("新しいキーを設定したい場合は、一度削除してください。")
        return

    # --- ステップ0: 準備（初回のみ） ---
    st.subheader("ステップ0: 準備（初回のみ）")
    st.warning("GoogleのAPIを利用するには、最初に「請求先アカウント」の設定が必要です。")
    st.markdown("""
    - **なぜ必要？**: Googleが本人確認と不正利用防止のために必須としています。
    - **料金は？**: クレジットカードの登録が求められますが、Google Mapsには**毎月$200の無料利用枠**があるため、通常の個人利用で料金が発生することはほとんどありません。
    
    下のリンクから設定ページを開き、画面の指示に従って設定を完了してください。
    （既に設定済みの方は、このステップは不要です）
    """)
    st.markdown('<a href="https://console.cloud.google.com/billing/create" target="_blank" style="display: inline-block; padding: 12px 20px; background-color: #F4B400; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">💳 請求先アカウント設定ページを開く</a>', unsafe_allow_html=True)
    st.divider()

    # --- ステップ1: プロジェクトIDの入力 ---
    st.subheader("ステップ1: プロジェクトを作成し、IDを取得する")
    st.markdown("""
    次に、APIキーを保管する「プロジェクト」という箱を用意します。
    1. **下のリンクをクリックして、プロジェクトを新規作成してください。**
       - プロジェクト名はご自身で分かりやすい名前でOKです。
       - 作成時に「請求先アカウント」の選択を求められたら、ステップ0で作成したものを選択します。
    2. **作成後、画面上部に表示される「プロジェクトID」をコピーしてください。**
    3. **コピーしたIDを、下のボックスに貼り付けてください。**
    """)
    st.markdown('<a href="https://console.cloud.google.com/projectcreate" target="_blank" style="display: inline-block; padding: 12px 20px; background-color: #4285F4; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">🚀 プロジェクト作成ページを開く</a>', unsafe_allow_html=True)

    project_id = st.text_input("ここにプロジェクトIDを貼り付け →", placeholder="例: my-map-tool-123456", help="プロジェクト作成後に表示されるIDです。プロジェクト名ではありません。")

    # --- ステップ2 & 3: 魔法のリンクとキー入力 ---
    if project_id:
        st.divider()
        st.subheader("ステップ2: 3つのAPIを有効にする")
        st.warning("A→B→Cの順番で、リンクを一つずつクリックしてAPIを有効にしてください。")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**A. 地図表示 API**"); st.caption("ウェブに地図を表示する基本API")
            maps_js_url = f"https://console.cloud.google.com/apis/library/maps-backend.googleapis.com?project={project_id}"
            st.markdown(f'<a href="{maps_js_url}" target="_blank" style="display: block; margin-top: 10px; padding: 12px; background-color: #4285F4; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">🅰️ 地図表示APIを有効化</a>', unsafe_allow_html=True)
        with col_b:
            st.markdown("**B. 住所検索 API**"); st.caption("住所を緯度経度に変換するAPI")
            geocoding_url = f"https://console.cloud.google.com/apis/library/geocoding-backend.googleapis.com?project={project_id}"
            st.markdown(f'<a href="{geocoding_url}" target="_blank" style="display: block; margin-top: 10px; padding: 12px; background-color: #34A853; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">🅱️ 住所検索APIを有効化</a>', unsafe_allow_html=True)
        with col_c:
            st.markdown("**C. 場所検索 API**"); st.caption("近くの店などを検索するAPI")
            places_url = f"https://console.cloud.google.com/apis/library/places-backend.googleapis.com?project={project_id}"
            st.markdown(f'<a href="{places_url}" target="_blank" style="display: block; margin-top: 10px; padding: 12px; background-color: #FBBC05; color: black; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">🆎 場所検索APIを有効化</a>', unsafe_allow_html=True)

        st.divider()
        st.subheader("ステップ3: APIキーを作成して完了！")
        
        st.markdown("""
        上記のAPIをすべて有効にできたら、いよいよ最後のステップです！<br>
        下の**「🔑 APIキー作成ページを開く」**ボタンを押してください。

        移動先のページ上部に**「+ 認証情報を作成」**が表示されています。そちらを選択すると、次に**「APIキー」**という項目が表示されますので、クリックしてください。
        
        自動でキーが作成されますので、表示された文字列をコピーして、下のボックスに貼り付ければ完了です！
        """, unsafe_allow_html=True)
        
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        # ★★★ ここが、ちゃろさんの最後のアイデアを反映した究極の改善箇所です！ ★★★
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        st.info("""
        💡 **ヒント：２回目以降の方へ**
        
        もし以前にキーを作成し、ブラウザのキャッシュクリア等でここの設定が消えてしまった場合は、**新しくキーを作り直す必要はありません。**

        下の「APIキー作成ページ」を開くと、以前作成したキーの一覧（例: `API キー 1`）が表示されているはずです。そのキーの名前の部分をクリックすれば、キーの文字列を再度コピーできます。
        """, icon="ℹ️")

        credentials_url = f"https://console.cloud.google.com/apis/credentials?project={project_id}"
        st.markdown(f'<a href="{credentials_url}" target="_blank" style="display: inline-block; padding: 12px 20px; background-color: #EA4335; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">🔑 APIキー作成ページを開く</a>', unsafe_allow_html=True)

        with st.form("maps_api_key_form"):
            maps_api_key_input = st.text_input("ここにGoogle Maps APIキーを貼り付け →", type="password")
            submitted = st.form_submit_button("💾 このキーを保存する", type="primary", use_container_width=True)
            if submitted:
                if maps_api_key_input.startswith("AIza"):
                    app_s = read_app_state(); app_s['google_maps_api_key'] = maps_api_key_input
                    write_app_state(app_s)
                    st.success("✅ Google Maps APIキーを保存しました！"); st.balloons(); time.sleep(2); st.rerun()
                else:
                    st.error("❌ キーの形式が正しくないようです。もう一度確認してください。（通常「AIza...」から始まります）")
