import streamlit as st
from google.cloud import vision
from streamlit_local_storage import LocalStorage

# --- ① アプリの基本設定 ---
st.set_page_config(
    page_title="レシート画像 de 簡単データ化くん (PoC)",
    page_icon="🧾"
)

# --- ② ローカルストレージの準備 ---
try:
    localS = LocalStorage()
except Exception as e:
    st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。ブラウザのシークレットモードなどが原因である可能性があります。エラー詳細: {e}")
    st.stop()

# --- ③ メインの処理を実行する関数 ---
def run_receipt_ocr_app(api_key_json_str):
    st.title("🧾 レシート画像 de 簡単データ化くん (PoC)")
    st.info("このアプリは、レシート画像から文字を読み取る機能の技術検証（PoC）です。")

    uploaded_file = st.file_uploader(
        "処理したいレシート画像を、ここにアップロードしてください。",
        type=['png', 'jpg', 'jpeg']
    )

    if st.button("⬆️ アップロードした画像の文字を読み取る"):
        if uploaded_file is None:
            st.warning("画像がアップロードされていません。")
            st.stop()
        
        if not api_key_json_str:
            st.warning("サイドバーでVision APIの認証情報（JSON）を入力し、保存してください。")
            st.stop()

        try:
            # --- ここがVision APIを呼び出す心臓部 ---
            with st.spinner("🧠 AIがレシートの文字を解析中..."):
                # 文字列形式のJSONを辞書に変換
                import json
                credentials_dict = json.loads(api_key_json_str)
                
                # 認証情報を使ってクライアントを初期化
                credentials = vision.Credentials.from_service_account_info(credentials_dict)
                client = vision.ImageAnnotatorClient(credentials=credentials)
                
                # アップロードされた画像データを読み込む
                content = uploaded_file.getvalue()
                image = vision.Image(content=content)
                
                # Vision APIのテキスト検出（OCR）を実行
                response = client.text_detection(image=image)
                texts = response.text_annotations

            st.success("🎉 文字の読み取りが完了しました！")
            
            # --- 抽出した結果を表示 ---
            st.divider()
            st.subheader("🤖 AIが読み取った全テキスト情報")

            if texts:
                # 抽出されたテキスト全体をそのまま表示
                st.text_area("抽出結果", texts[0].description, height=300)
            else:
                st.warning("この画像からは文字を検出できませんでした。")

            if response.error.message:
                st.error(f"APIからエラーが返されました: {response.error.message}")

        except Exception as e:
            st.error(f"❌ 処理中に予期せぬエラーが発生しました: {e}")
            st.error("🚨 APIキーのJSONが正しい形式か、再度ご確認ください。コピー＆ペーストが不完全な可能性があります。")

# --- ④ サイドバーと、APIキー入力 ---
with st.sidebar:
    st.header("⚙️ API設定")
    
    # Vision APIはサービスアカウントのJSONキーを使用するため、入力欄をtext_areaに変更
    saved_key_json = localS.getItem("vision_api_key_json")
    default_value = saved_key_json if isinstance(saved_key_json, str) else ""
    
    api_key_input = st.text_area(
        "Vision API サービスアカウントキー (JSON)", 
        value=default_value,
        height=250,
        help="Google Cloudからダウンロードした、サービスアカウントのJSONキーの中身を、ここに全て貼り付けてください。"
    )
    
    if st.button("このAPIキーをブラウザに記憶させる"):
        localS.setItem("vision_api_key_json", api_key_input)
        st.success("APIキーを記憶しました！")

# --- ⑤ メイン処理の、実行 ---
run_receipt_ocr_app(api_key_input)
