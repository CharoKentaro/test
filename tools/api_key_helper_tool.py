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
    (通常、Google Maps APIには毎月$200の無料利用枠があります)
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
            st.success("キーを削除しました。")
            time.sleep(1)
            st.rerun()
        st.caption("新しいキーを設定したい場合は、一度削除してください。")
        return # キーが設定済みなら、ここで処理を終了

    # --- ステップ1: プロジェクトIDの入力 ---
    st.subheader("ステップ1: プロジェクトIDを取得する")
    st.markdown("""
    まず、APIキーを保管するための「プロジェクト」という箱を用意します。
    1. **下のリンクをクリックして、Google Cloudでプロジェクトを新規作成してください。**
       - プロジェクト名は「My-Map-Tool」など、ご自身で分かりやすい名前でOKです。
    2. **作成が完了したら、画面上部に表示される「プロジェクトID」をコピーします。**
       - （例: `my-map-tool-123456` のような形式です）
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
        
        # --- A: Maps JavaScript API ---
        with col_a:
            st.markdown("**A. 地図表示 API**")
            st.caption("ウェブページに地図を表示するための基本APIです。")
            maps_js_url = f"https://console.cloud.google.com/apis/library/maps-backend.googleapis.com?project={project_id}"
            st.markdown(f'<a href="{maps_js_url}" target="_blank" style="display: block; margin-top: 10px; padding: 12px; background-color: #4285F4; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">🅰️ 地図表示APIを有効化</a>', unsafe_allow_html=True)

        # --- B: Geocoding API ---
        with col_b:
            st.markdown("**B. 住所検索 API**")
            st.caption("「東京都庁」などの住所を、緯度経度に変換するAPIです。")
            geocoding_url = f"https://console.cloud.google.com/apis/library/geocoding-backend.googleapis.com?project={project_id}"
            st.markdown(f'<a href="{geocoding_url}" target="_blank" style="display: block; margin-top: 10px; padding: 12px; background-color: #34A853; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">🅱️ 住所検索APIを有効化</a>', unsafe_allow_html=True)

        # --- C: Places API ---
        with col_c:
            st.markdown("**C. 場所検索 API**")
            st.caption("近くのカフェやレストランなどを検索するAPIです。")
            places_url = f"https://console.cloud.google.com/apis/library/places-backend.googleapis.com?project={project_id}"
            st.markdown(f'<a href="{places_url}" target="_blank" style="display: block; margin-top: 10px; padding: 12px; background-color: #FBBC05; color: black; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">🆎 場所検索APIを有効化</a>', unsafe_allow_html=True)

        st.divider()
        st.subheader("ステップ3: APIキーを作成して完了！")
        st.markdown("""
        上記のAPIをすべて有効にできたら、最後にAPIキーを作成します。
        1. **下のリンクを開き、移動したページで**
        2. **画面上部の「+ 認証情報を作成」をクリックし、**
        3. **「APIキー」を選択してください。**
        
        表示されたAPIキーをコピーして、下のボックスに貼り付ければ完了です！
        """)
        credentials_url = f"https://console.cloud.google.com/apis/credentials?project={project_id}"
        st.markdown(f'<a href="{credentials_url}" target="_blank" style="display: inline-block; padding: 12px 20px; background-color: #EA4335; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">🔑 APIキー作成ページを開く</a>', unsafe_allow_html=True)

        with st.form("maps_api_key_form"):
            maps_api_key_input = st.text_input("ここにGoogle Maps APIキーを貼り付け →", type="password")
            submitted = st.form_submit_button("💾 このキーを保存する", type="primary", use_container_width=True)

            if submitted:
                # 簡単な形式チェック（Google APIキーは通常"AIza"で始まる）
                if maps_api_key_input.startswith("AIza"):
                    app_s = read_app_state()
                    app_s['google_maps_api_key'] = maps_api_key_input
                    write_app_state(app_s)
                    st.success("✅ Google Maps APIキーを保存しました！")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ キーの形式が正しくないようです。もう一度確認してください。（通常「AIza...」から始まります）")
