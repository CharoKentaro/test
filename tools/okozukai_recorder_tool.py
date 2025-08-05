# ===============================================================
# ★★★ okozukai_recorder_tool.py ＜最終確認・URLパラメータ版＞ ★★★
# ===============================================================
import streamlit as st
# LocalStorage と、関連するライブラリはもう使いません
import time

# --- このツール専用の関数 ---
def calculate_remaining_balance(monthly_allowance, total_spent):
    return monthly_allowance - total_spent

def format_balance_display(balance):
    if balance >= 0:
        return f"🟢 **{balance:,.0f} 円**"
    else:
        return f"🔴 **{abs(balance):,.0f} 円 (予算オーバー)**"

# --- ポータルから呼び出されるメイン関数 ---
def show_tool(gemini_api_key):
    st.header("💰 お小遣い管理", divider='rainbow')

    st.error("【最終実験モード】LocalStorageを使わず、URLだけでデータを保存するテストです。")

    prefix = "okozukai_"
    key_allowance = f"{prefix}monthly_allowance"

    # --- Step 1: 初期化 ---
    # URLのクエリパラメータから直接データを読み込む
    # st.query_params は Streamlit 1.33.0 以降で利用可能です
    try:
        # URLに値があればそれを使い、なければ0.0とする
        current_allowance_from_url = float(st.query_params.get(key_allowance, 0.0))
    except (AttributeError, ValueError):
        # 古いStreamlitバージョンや予期せぬ値の場合のフォールバック
        current_allowance_from_url = 0.0
        st.warning("st.query_paramsが利用できない、またはURLの値が不正です。")


    # --- Step 2: UIの描画と操作 ---
    with st.expander("💳 今月のお小遣い設定", expanded=(current_allowance_from_url == 0)):
        
        # コールバック関数：入力されたらURLを書き換える
        def update_url():
            new_val = st.session_state[f"{prefix}allowance_input"]
            # st.query_params を使ってURLを操作
            st.query_params[key_allowance] = str(float(new_val))
            st.toast(f"✅ 設定をURLに保存しました！リロードして確認してください。")

        st.number_input(
            "今月のお小遣いを入力してください",
            value=current_allowance_from_url, # 表示する値はURLから取得したもの
            step=1000.0,
            min_value=0.0,
            key=f"{prefix}allowance_input",
            on_change=update_url,
            help="入力後、Enterキーを押すか、他の場所をクリックするとURLに保存されます。"
        )

    # --- Step 3: 現在の状況表示 ---
    st.divider()
    st.subheader("📊 現在の状況")
    
    # 表示するデータはすべてURLから直接読み取った値を使う
    current_allowance = current_allowance_from_url
    # (他のデータは一時的に0として表示を簡略化)
    current_spent = 0.0 
    remaining_balance = calculate_remaining_balance(current_allowance, current_spent)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("今月の予算", f"{current_allowance:,.0f} 円")
    col2.metric("使った金額", f"{current_spent:,.0f} 円")
    col3.metric("残り予算", f"{remaining_balance:,.0f} 円")
    
    st.markdown(f"#### 🎯 今使えるお金は…")
    st.markdown(f"<p style='text-align: center; font-size: 2.5em; font-weight: bold;'>{format_balance_display(remaining_balance)}</p>", unsafe_allow_html=True)
    
    if current_allowance > 0:
        progress_ratio = min(current_spent / current_allowance, 1.0)
        st.progress(progress_ratio)
        st.caption(f"予算使用率: {progress_ratio * 100:.1f}%")
        
    st.divider()
    st.info("この実験では、レシート登録機能は無効化されています。")
