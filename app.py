import streamlit as st
import re
from PIL import Image
import pytesseract

# セッションステートの初期化
if "budget" not in st.session_state:
    st.session_state.budget = 1000  # 初期予算
if "spent" not in st.session_state:
    st.session_state.spent = 0

st.title("📸 レシート家計簿")

# レシート画像のアップロード
uploaded_file = st.file_uploader("🧾 レシート画像をアップロード", type=["jpg", "jpeg", "png"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされたレシート", use_column_width=True)

    # OCR処理
    text = pytesseract.image_to_string(image, lang='jpn')
    st.text_area("🔍 抽出されたテキスト", text, height=200)

    # 金額の抽出（全角・半角の「円」や￥対応）
    amounts = re.findall(r"[¥￥]?\s?(\d{1,5})(?:円)?", text)
    if amounts:
        extracted_amounts = list(map(int, amounts))
        total_amount = sum(extracted_amounts)

        if st.button("✅ この金額を支出として記録"):
            st.session_state.spent += total_amount
            st.success(f"{total_amount} 円を支出として記録しました！")

# 現在の状態を表示
remaining = st.session_state.budget - st.session_state.spent
usage_rate = st.session_state.spent / st.session_state.budget * 100 if st.session_state.budget else 0

st.markdown("## 📊 現在の状況")
st.metric("💰 今月の予算", f"{st.session_state.budget} 円")
st.metric("📉 使った金額", f"{st.session_state.spent} 円")
st.metric("💸 残り予算", f"{remaining} 円")
st.metric("🎯 今使える自由なお金", f"🟢 {remaining} 円")
st.metric("📈 予算使用率", f"{usage_rate:.1f}%")
