import streamlit as st
import google.generativeai as genai
from streamlit_local_storage import LocalStorage
import json
from PIL import Image
import io

# --- ① アプリの基本設定 ---
st.set_page_config(
    page_title="お小遣いレコーダー",
    page_icon="💰"
)

# --- ② ローカルストレージの準備 ---
try:
    localS = LocalStorage()
except Exception as e:
    st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。エラー詳細: {e}")
    st.stop()

# --- ③ Geminiに渡す、魂のプロンプト（シンプル版）---
GEMINI_PROMPT = """
あなたは、レシートの画像を直接解析する、経理アシスタントAIです。
# 指示
レシートの画像の中から、「合計金額」「お預り金額」「お釣り」の3つの、支出に関わる重要な数字だけを、注意深く、抽出してください。
# 出力形式
*   抽出した結果を、必ず以下のJSON形式で出力してください。
*   数値は、数字のみを抽出してください（円やカンマは不要）。
*   値が見つからない場合は、"0" と記載してください。
*   JSON以外の、前置きや説明は、絶対に出力しないでください。

{
  "total_amount": "ここに合計金額の数値",
  "tendered_amount": "ここにお預り金額の数値",
  "change_amount": "ここにお釣り金額の数値"
}
"""

# --- ④ 残高計算関数 ---
def calculate_remaining_balance(monthly_allowance, total_spent):
    return monthly_allowance - total_spent

def format_balance_display(balance):
    if balance >= 0:
        return f"🟢 **{balance:,.0f} 円**"
    else:
        return f"🔴 **{abs(balance):,.0f} 円 (予算オーバー)**"

# --- ⑤ メインの処理を実行する関数 ---
def run_allowance_recorder_app(gemini_api_key):
    st.title("💰 お小遣いレコーダー")
    st.info("レシートを登録して、今月使えるお金を管理しよう！")

    # --- 【修正箇所】セッションステートの初期化処理を改善 ---
    # アプリの初回実行時、またはブラウザリロード時に一度だけローカルストレージから値を読み込む
    if "initialized" not in st.session_state:
        stored_allowance = localS.getItem("monthly_allowance")
        stored_spent = localS.getItem("total_spent")
        
        st.session_state.monthly_allowance = float(stored_allowance if stored_allowance is not None else 0.0)
        st.session_state.total_spent = float(stored_spent if stored_spent is not None else 0.0)
        
        # 初期化が完了したことを示すフラグを立てる
        st.session_state.initialized = True
    
    # --- 今月のお小遣い設定 ---
    st.divider()
    st.header("💳 今月のお小遣い設定")
    
    new_allowance = st.number_input(
        "今月のお小遣いを入力してください", 
        value=st.session_state.monthly_allowance,
        step=1000.0,
        min_value=0.0
    )
    
    if st.button("この金額で設定する"):
        # 高速な内部メモリを先に更新
        st.session_state.monthly_allowance = new_allowance
        # その後、バックアップとしてローカルストレージに保存
        localS.setItem("monthly_allowance", new_allowance)
        st.success(f"今月のお小遣いを {new_allowance:,.0f} 円に設定しました！")
        st.rerun()

    # --- 現在の残高表示（常に最新の内部メモリを参照） ---
    current_allowance = st.session_state.monthly_allowance
    current_spent = st.session_state.total_spent
    remaining_balance = calculate_remaining_balance(current_allowance, current_spent)
    
    st.divider()
    st.header("📊 現在の状況")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("今月の予算", f"{current_allowance:,.0f} 円")
    with col2:
        spent_delta = f"+{current_spent:,.0f} 円" if current_spent > 0 else None
        st.metric("使った金額", f"{current_spent:,.0f} 円", delta=spent_delta, delta_color="inverse")
    with col3:
        balance_delta = f"-{current_spent:,.0f} 円" if current_spent > 0 else None
        st.metric("残り予算", f"{remaining_balance:,.0f} 円", delta=balance_delta, delta_color="inverse")
    
    st.markdown("### 🎯 今使える自由なお金")
    st.markdown(f"## {format_balance_display(remaining_balance)}")
    
    if current_allowance > 0:
        progress_ratio = min(current_spent / current_allowance, 1.0)
        st.progress(progress_ratio)
        st.caption(f"予算使用率: {progress_ratio * 100:.1f}% ({current_spent:,.0f} 円 / {current_allowance:,.0f} 円)")
    
    if current_spent > 0:
        st.info(f"💡 これまでに {current_spent:,.0f} 円使いました。残り {remaining_balance:,.0f} 円使えます！")

    st.divider()

    # --- レシート解析機能 ---
    st.header("📸 レシートを登録する")
    uploaded_file = st.file_uploader("処理したいレシート画像を、ここにアップロードしてください。", type=['png', 'jpg', 'jpeg'])

    if uploaded_file:
        st.image(uploaded_file, caption="アップロードされたレシート", width=300)

        if st.button("⬆️ このレシートを解析して支出を記録する"):
            if not gemini_api_key:
                st.warning("サイドバーからGemini APIキーが設定されているか確認してください。")
                st.stop()

            try:
                with st.spinner("🧠 AIがレシートを解析中..."):
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash-latest')
                    image = Image.open(uploaded_file)
                    gemini_response = model.generate_content([GEMINI_PROMPT, image])
                    cleaned_json_str = gemini_response.text.strip().replace("```json", "").replace("```", "")
                    extracted_data = json.loads(cleaned_json_str)
                
                st.success("🎉 AIによる解析が完了しました！")
                
                try:
                    total_amount = float(extracted_data.get("total_amount", 0))
                    
                    st.subheader("📋 解析結果")
                    st.json(extracted_data)
                    
                    corrected_total = st.number_input(
                        "AIが読み取った合計金額はこちらです。必要なら修正してください。", 
                        value=total_amount,
                        min_value=0.0,
                        key=f"corrected_total_{uploaded_file.file_id}" 
                    )
                    
                    projected_balance = calculate_remaining_balance(current_allowance, current_spent + corrected_total)
                    st.info(f"この支出を記録すると、残り予算は **{projected_balance:,.0f} 円** になります。")
                    
                    if st.button("💰 この金額で支出を確定する", key=f"confirm_button_{uploaded_file.file_id}"):
                        new_total_spent = st.session_state.total_spent + corrected_total
                        # 高速な内部メモリを先に更新
                        st.session_state.total_spent = new_total_spent
                        # その後、バックアップとしてローカルストレージに保存
                        localS.setItem("total_spent", new_total_spent)
                        
                        st.success(f"🎉 {corrected_total:,.0f} 円の支出を記録しました！")
                        st.balloons()
                        # 画面をリフレッシュして、更新された内部メモリの値を即座に表示
                        st.rerun()

                except (ValueError, TypeError) as e:
                    st.error(f"AIが金額を数値として正しく認識できませんでした。エラー: {e}")
                    st.subheader("手動入力")
                    manual_total = st.number_input("支出した合計金額を手動で入力してください。", min_value=0.0, key="manual_total")
                    
                    if st.button("手動で支出を記録する", key="manual_confirm") and manual_total > 0:
                        new_total_spent = st.session_state.total_spent + manual_total
                        st.session_state.total_spent = new_total_spent
                        localS.setItem("total_spent", new_total_spent)
                        st.success(f"🎉 {manual_total:,.0f} 円の支出を記録しました！")
                        st.rerun()

            except Exception as e:
                st.error(f"❌ 処理中に予期せぬエラーが発生しました: {e}")
                if 'gemini_response' in locals():
                    st.code(gemini_response.text, language="text")
    
    # --- データ管理機能 ---
    st.divider()
    st.header("🔄 データ管理")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("支出履歴をリセット", type="secondary"):
            st.session_state.total_spent = 0.0
            localS.setItem("total_spent", 0.0)
            st.success("支出履歴をリセットしました！")
            st.rerun()
    
    with col2:
        if st.button("全データをリセット", type="secondary"):
            st.session_state.monthly_allowance = 0.0
            st.session_state.total_spent = 0.0
            st.session_state.initialized = False # 初期化フラグもリセット
            localS.setItem("monthly_allowance", 0.0)
            localS.setItem("total_spent", 0.0)
            st.success("全データをリセットしました！")
            st.rerun()

# --- ⑥ サイドバーとAPIキー入力 ---
with st.sidebar:
    st.header("⚙️ API設定")
    saved_gemini_key = localS.getItem("gemini_api_key")
    gemini_api_key_input = st.text_input(
        "Gemini APIキー", type="password",
        value=saved_gemini_key if isinstance(saved_gemini_key, str) else ""
    )
    if st.button("Geminiキーを記憶"):
        localS.setItem("gemini_api_key", gemini_api_key_input)
        st.success("Gemini APIキーを記憶しました！")
    
    st.divider()
    st.caption("💡 使い方のヒント")
    st.caption("1. 今月の予算を設定")
    st.caption("2. レシート画像をアップロード") 
    st.caption("3. AI解析結果を確認して支出記録")
    st.caption("4. 残り予算をリアルタイムで確認")

# --- ⑦ メイン処理の実行 ---
run_allowance_recorder_app(gemini_api_key_input)
