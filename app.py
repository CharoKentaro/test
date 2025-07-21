import streamlit as st
import json
import os
from datetime import datetime

# JSONファイルの保存先
DATA_FILE = "budget_data.json"

# =======================================
# 1. データの読み込み・初期化
# =======================================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {
            "budget": 1000,  # 初期予算
            "expenses": [],  # 支出リスト
        }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =======================================
# 2. 残り予算の計算
# =======================================
def calculate_summary(data):
    total_spent = sum(item["amount"] for item in data["expenses"])
    remaining = data["budget"] - total_spent
    usage_rate = (total_spent / data["budget"]) * 100 if data["budget"] else 0
    return total_spent, remaining, usage_rate

# =======================================
# 3. UI構成
# =======================================
st.set_page_config("かんたん家計簿💰", layout="centered")

st.title("かんたん家計簿 💰")
st.markdown("今月の支出を記録して、予算内での生活をサポートします。")

# データ読み込み
data = load_data()

# =======================================
# 4. 支出の入力フォーム
# =======================================
with st.form("expense_form"):
    st.subheader("📥 支出を記録する")
    description = st.text_input("支出の内容", placeholder="例：ランチ")
    amount = st.number_input("金額（円）", min_value=0, step=100)
    submitted = st.form_submit_button("記録する")

    if submitted:
        if description and amount > 0:
            data["expenses"].append({
                "description": description,
                "amount": amount,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            save_data(data)
            st.success(f"この支出を記録すると、残り予算は {calculate_summary(data)[1]} 円 になります。")
            st.rerun()
        else:
            st.warning("支出内容と金額を正しく入力してください。")

# =======================================
# 5. 現在の状況表示
# =======================================
st.markdown("---")
st.subheader("📊 現在の状況")

total_spent, remaining, usage_rate = calculate_summary(data)

col1, col2, col3 = st.columns(3)
col1.metric("今月の予算", f"{data['budget']} 円")
col2.metric("使った金額", f"{total_spent} 円")
col3.metric("残り予算", f"{remaining} 円")

# 使用率バー
st.markdown(f"""
🎯 **今使える自由なお金**  
🟢 {remaining} 円  
予算使用率: {usage_rate:.1f}% ({total_spent} 円 / {data['budget']} 円)
""")

# =======================================
# 6. 支出の一覧表示（任意）
# =======================================
with st.expander("📜 支出の履歴を表示する"):
    if data["expenses"]:
        for item in reversed(data["expenses"]):
            st.write(f"- {item['date']} | {item['description']}：{item['amount']} 円")
    else:
        st.info("まだ支出は記録されていません。")

# =======================================
# 7. データ管理オプション
# =======================================
st.markdown("---")
st.subheader("🔄 データ管理")

col4, col5 = st.columns(2)

with col4:
    if st.button("💣 支出をリセット"):
        data["expenses"] = []
        save_data(data)
        st.success("支出履歴をリセットしました。")
        st.rerun()

with col5:
    if st.button("🔧 予算を初期化（1,000円に戻す）"):
        data["budget"] = 1000
        save_data(data)
        st.success("予算を1,000円に設定しました。")
        st.rerun()
