import streamlit as st
from google.api_core.client_options import ClientOptions
from google.cloud import vision
from streamlit_local_storage import LocalStorage

# --- ① アプリの基本設定 ---
st.set_page_config(
    page_title="レシート画像 de 簡単データ化くん (PoC Ver.2)",
    page_icon="🧾"
)

# --- ② ローカルストレージの準備 ---
try:
    localS = LocalStorage()
except Exception as e:
    st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。ブラウザのシークレットモードなどが原因である可能性があります。エラー詳細: {e}")
    st.stop()

# --- ③ メインの処理を実行する関数 ---
def run_receipt_ocr_app(api_key_str):
    st.title("🧾 レシート画像 de 簡単データ化くん (PoC Ver.2)")
    st.info("【改善版】シンプルなAPIキーで、レシート画像から文字を読み取る機能の技術検証です。")

    uploaded_file = st.file_uploader(
        "処理したいレシート画像を、ここにアップロードしてください。",
        type=['png', 'jpg', 'jpeg']
    )

    if st.button("⬆️ アップロードした画像の文字を読み取る"):
        if uploaded_file is None:
            st.warning("画像がアップロードされていません。")
            st.stop()
        
        if not api_key_str:
            st.warning("サイドバーでVision APIの「APIキー」を入力し、保存してください。")
            st.stop()

        try:
            # --- ここがVision APIを呼び出す心臓部（APIキー方式） ---
            with st.spinner("🧠 AIがレシートの文字を解析中..."):
                
                # APIキーを使ってクライアントを初期化
                client_options = ClientOptions(api_key=api_key_str)
                client = vision.ImageAnnotatorClient(client_options=client_options)
                
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
            st.error("🚨 入力されたAPIキーが正しいか、再度ご確認ください。")

# --- ④ サイドバーと、APIキー入力（シンプル版） ---
with st.sidebar:
    st.header("⚙️ API設定")
    
    saved_key = localS.getItem("vision_api_key")
    # キーが存在し、それが文字列であることを確認
    default_value = saved_key if isinstance(saved_key, str) else ""
    
    api_key_input = st.text_input(
        "Vision APIキー", 
        type="password",  # 念のためパスワード形式にして見えなくします
        value=default_value,
        help="Google Cloudで作成したAPIキーを、ここに貼り付けてください。"
    )
    
    if st.button("このAPIキーをブラウザに記憶させる"):
        localS.setItem("vision_api_key", api_key_input)
        st.success("APIキーを記憶しました！")

# --- ⑤ メイン処理の、実行 ---
run_receipt_ocr_app(api_key_input)
