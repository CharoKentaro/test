import streamlit as st
from PIL import Image
import pytesseract
import re
import io

# （ローカル環境の方は以下のようにパスを設定）
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.title("🧾 レシートOCR：使った金額を自動で読み取る")

# --- 画像アップロード ---
uploaded_file = st.file_uploader("📷 レシート画像をアップロードしてください", type=["jpg", "jpeg", "png"])

# --- 金額手入力（OCRの失敗に備えて） ---
manual_amount = st.number_input("💰 手入力で金額を追加したい場合はこちらに入力", min_value=0, step=1)

# --- OCR処理と金額抽出 ---
if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        st.image(image, caption="アップロードされたレシート", use_column_width=True)

        # OCRでテキスト抽出（日本語指定）
        text = pytesseract.image_to_string(image, lang='jpn')
        st.text_area("📝 認識されたテキスト", text, height=200)

        # 金額の抽出（例：123円、1,234など）
        prices = re.findall(r'\d{1,3}(?:,\d{3})*|\d+', text)
        prices = [int(p.replace(',', '')) for p in prices if int(p.replace(',', '')) < 100000]

        if prices:
            detected_total = max(prices)
            total_spent = detected_total + manual_amount
            st.success(f"✅ OCRで検出された最大の金額: {detected_total:,} 円")
            st.info(f"💵 合計（手入力含む）: {total_spent:,} 円")
        else:
            st.warning("❗金額が検出されませんでした。手入力欄をご利用ください。")

    except Exception as e:
        st.error(f"⚠️ エラーが発生しました：{e}")

else:
    st.write("👆 レシート画像をアップロードしてください。")

