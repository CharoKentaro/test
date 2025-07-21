import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import datetime
from typing import Dict, Optional, List

# --- ① アプリの基本設定 ---
st.set_page_config(
    page_title="💰 お小遣いレコーダー",
    page_icon="💰",
    layout="wide"
)

# --- ② セッションステートの初期化 ---
def initialize_session_state():
    """セッションステートの初期化"""
    if 'monthly_allowance' not in st.session_state:
        st.session_state.monthly_allowance = 0.0
    if 'total_spent' not in st.session_state:
        st.session_state.total_spent = 0.0
    if 'expense_history' not in st.session_state:
        st.session_state.expense_history = []
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = ""
    if 'current_month' not in st.session_state:
        st.session_state.current_month = datetime.datetime.now().strftime("%Y-%m")

# --- ③ 月が変わった場合の処理 ---
def check_month_change():
    """月が変わったかチェックし、必要に応じてリセット"""
    current_month = datetime.datetime.now().strftime("%Y-%m")
    if st.session_state.current_month != current_month:
        # 新しい月になった場合、支出履歴をリセット
        if st.session_state.expense_history:
            st.info(f"🗓️ 新しい月になりました！({current_month}) 支出履歴をリセットします。")
            st.session_state.total_spent = 0.0
            st.session_state.expense_history = []
            st.session_state.current_month = current_month

# --- ④ 改善されたGeminiプロンプト ---
GEMINI_PROMPT = """
あなたは高精度なレシート解析AIです。画像からレシートの情報を正確に読み取ってください。

# 解析対象
- 合計金額（税込み総額）
- お預かり金額（顧客が支払った金額）
- お釣り金額

# 重要な指示
1. 数字は正確に読み取ってください
2. カンマや円マークは除去し、数値のみを抽出
3. 見つからない項目は "0" を設定
4. 必ずJSON形式で応答し、他のテキストは含めない

# 出力形式（この形式を厳守）
{
  "total_amount": "合計金額の数値のみ",
  "tendered_amount": "お預り金額の数値のみ", 
  "change_amount": "お釣り金額の数値のみ",
  "confidence": "読み取り精度（high/medium/low）"
}
"""

# --- ⑤ Gemini APIでレシート解析 ---
def analyze_receipt_with_gemini(image: Image.Image, api_key: str) -> Dict:
    """Gemini APIを使用してレシートを解析"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        # 画像のサイズを最適化
        if image.size[0] > 1024 or image.size[1] > 1024:
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        
        response = model.generate_content([GEMINI_PROMPT, image])
        
        # レスポンスのクリーニング
        response_text = response.text.strip()
        # コードブロックマーカーを除去
        response_text = response_text.replace("```json", "").replace("```", "")
        # 余分な空白や改行を除去
        response_text = response_text.strip()
        
        # JSONパース
        parsed_data = json.loads(response_text)
        
        # データ検証
        required_keys = ["total_amount", "tendered_amount", "change_amount"]
        for key in required_keys:
            if key not in parsed_data:
                parsed_data[key] = "0"
        
        return {
            "success": True,
            "data": parsed_data,
            "error": None
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "data": None,
            "error": f"AI応答のJSON解析に失敗: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"レシート解析エラー: {str(e)}"
        }

# --- ⑥ 残高計算とフォーマット ---
def calculate_remaining_balance(allowance: float, spent: float) -> float:
    """残高計算"""
    return allowance - spent

def format_balance_display(balance: float) -> str:
    """残高の表示フォーマット"""
    if balance >= 0:
        return f"🟢 **{balance:,.0f} 円**"
    else:
        return f"🔴 **{abs(balance):,.0f} 円 オーバー**"

def get_balance_color(balance: float) -> str:
    """残高に応じた色を返す"""
    if balance >= 0:
        return "normal"
    else:
        return "inverse"

# --- ⑦ 支出記録の追加 ---
def add_expense(amount: float, description: str = "レシートからの支出"):
    """支出を記録"""
    expense = {
        "amount": amount,
        "description": description,
        "timestamp": datetime.datetime.now().isoformat(),
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    st.session_state.expense_history.append(expense)
    st.session_state.total_spent += amount

# --- ⑧ メインアプリケーション ---
def run_allowance_recorder_app():
    # 初期化
    initialize_session_state()
    check_month_change()
    
    # ヘッダー
    st.title("💰 お小遣いレコーダー")
    st.markdown("### 📱 レシートをAIで解析して、賢くお金を管理しよう！")
    
    # 現在の状況を大きく表示
    current_balance = calculate_remaining_balance(
        st.session_state.monthly_allowance, 
        st.session_state.total_spent
    )
    
    # メインダッシュボード
    with st.container():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "💳 今月の予算", 
                f"{st.session_state.monthly_allowance:,.0f} 円"
            )
        
        with col2:
            spent_delta = f"+{st.session_state.total_spent:,.0f}" if st.session_state.total_spent > 0 else None
            st.metric(
                "💸 使った金額", 
                f"{st.session_state.total_spent:,.0f} 円",
                delta=spent_delta,
                delta_color="inverse"
            )
        
        with col3:
            balance_delta = f"-{st.session_state.total_spent:,.0f}" if st.session_state.total_spent > 0 else None
            st.metric(
                "💰 残り予算", 
                f"{current_balance:,.0f} 円",
                delta=balance_delta,
                delta_color=get_balance_color(current_balance)
            )
    
    # 大きな残高表示
    st.markdown("---")
    st.markdown("### 🎯 今使える自由なお金")
    st.markdown(f"## {format_balance_display(current_balance)}")
    
    # プログレスバー
    if st.session_state.monthly_allowance > 0:
        progress = min(st.session_state.total_spent / st.session_state.monthly_allowance, 1.0)
        st.progress(progress)
        percentage = progress * 100
        
        if percentage >= 100:
            st.error(f"⚠️ 予算を超過しています！ ({percentage:.1f}%)")
        elif percentage >= 80:
            st.warning(f"⚠️ 予算の80%以上を使用しています ({percentage:.1f}%)")
        else:
            st.success(f"✅ 予算使用率: {percentage:.1f}%")
    
    st.markdown("---")
    
    # タブで機能を分離
    tab1, tab2, tab3, tab4 = st.tabs(["📸 レシート解析", "💳 予算設定", "📊 支出履歴", "⚙️ 設定"])
    
    with tab1:
        st.header("📸 レシートを解析して支出を記録")
        
        # APIキーチェック
        if not st.session_state.gemini_api_key:
            st.warning("🔑 Gemini APIキーが設定されていません。設定タブで入力してください。")
            return
        
        uploaded_file = st.file_uploader(
            "レシート画像をアップロードしてください", 
            type=['png', 'jpg', 'jpeg'],
            help="PNG、JPG、JPEG形式の画像をサポートしています"
        )
        
        if uploaded_file:
            # 画像プレビュー
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(uploaded_file, caption="アップロードされたレシート", width=250)
            
            with col2:
                if st.button("🧠 AIでレシートを解析", type="primary", use_container_width=True):
                    with st.spinner("🔍 AIがレシートを解析中..."):
                        image = Image.open(uploaded_file)
                        result = analyze_receipt_with_gemini(image, st.session_state.gemini_api_key)
                    
                    if result["success"]:
                        data = result["data"]
                        st.success("✅ 解析完了！")
                        
                        # 解析結果の表示
                        st.subheader("📋 解析結果")
                        with st.expander("詳細結果を表示", expanded=True):
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("合計金額", f"{float(data.get('total_amount', 0)):,.0f} 円")
                            with col_b:
                                st.metric("お預り", f"{float(data.get('tendered_amount', 0)):,.0f} 円")
                            with col_c:
                                st.metric("お釣り", f"{float(data.get('change_amount', 0)):,.0f} 円")
                        
                        # 金額確認・修正
                        total_amount = st.number_input(
                            "💰 記録する支出金額（必要に応じて修正してください）",
                            value=float(data.get("total_amount", 0)),
                            min_value=0.0,
                            step=10.0
                        )
                        
                        description = st.text_input("📝 支出の説明（任意）", placeholder="例：昼食代、日用品など")
                        
                        # 予想残高表示
                        projected_balance = calculate_remaining_balance(
                            st.session_state.monthly_allowance,
                            st.session_state.total_spent + total_amount
                        )
                        
                        if projected_balance < 0:
                            st.warning(f"⚠️ この支出を記録すると、予算を **{abs(projected_balance):,.0f} 円** オーバーします")
                        else:
                            st.info(f"💡 この支出後の残り予算: **{projected_balance:,.0f} 円**")
                        
                        # 支出確定ボタン
                        if st.button("💾 支出を記録する", type="primary", use_container_width=True):
                            if total_amount > 0:
                                desc = description if description else "レシートからの支出"
                                add_expense(total_amount, desc)
                                st.success(f"🎉 {total_amount:,.0f} 円の支出を記録しました！")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("支出金額は0円より大きい値を入力してください")
                    
                    else:
                        st.error(f"❌ 解析に失敗しました: {result['error']}")
                        st.info("💡 手動入力をお試しください")
                        
                        # 手動入力フォールバック
                        with st.expander("手動で支出を入力", expanded=True):
                            manual_amount = st.number_input("支出金額", min_value=0.0, step=10.0)
                            manual_desc = st.text_input("説明", placeholder="例：昼食代")
                            
                            if st.button("手動で記録", use_container_width=True):
                                if manual_amount > 0:
                                    desc = manual_desc if manual_desc else "手動入力"
                                    add_expense(manual_amount, desc)
                                    st.success(f"🎉 {manual_amount:,.0f} 円を記録しました！")
                                    st.rerun()
    
    with tab2:
        st.header("💳 今月のお小遣い予算設定")
        
        current_month_display = datetime.datetime.now().strftime("%Y年%m月")
        st.info(f"📅 現在設定中: {current_month_display}の予算")
        
        new_allowance = st.number_input(
            "今月のお小遣い予算を設定してください",
            value=st.session_state.monthly_allowance,
            min_value=0.0,
            step=1000.0,
            help="月初に設定することをおすすめします"
        )
        
        if st.button("💾 予算を更新", type="primary"):
            st.session_state.monthly_allowance = new_allowance
            st.success(f"✅ 今月の予算を {new_allowance:,.0f} 円に設定しました！")
            st.rerun()
        
        # 予算提案機能
        st.subheader("💡 予算設定のヒント")
        suggested_amounts = [10000, 20000, 30000, 50000]
        cols = st.columns(len(suggested_amounts))
        
        for i, amount in enumerate(suggested_amounts):
            with cols[i]:
                if st.button(f"{amount:,}円", key=f"suggest_{amount}"):
                    st.session_state.monthly_allowance = amount
                    st.rerun()
    
    with tab3:
        st.header("📊 今月の支出履歴")
        
        if st.session_state.expense_history:
            # 支出履歴の表示
            st.subheader(f"📝 記録された支出 ({len(st.session_state.expense_history)}件)")
            
            for i, expense in enumerate(reversed(st.session_state.expense_history)):
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**{expense['description']}**")
                        st.caption(expense['date'])
                    with col2:
                        st.write(f"💸 {expense['amount']:,.0f}円")
                    with col3:
                        if st.button("🗑️", key=f"delete_{i}", help="この支出を削除"):
                            st.session_state.expense_history.remove(expense)
                            st.session_state.total_spent -= expense['amount']
                            st.rerun()
                    st.divider()
            
            # 統計情報
            st.subheader("📈 支出統計")
            avg_expense = st.session_state.total_spent / len(st.session_state.expense_history)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("平均支出額", f"{avg_expense:,.0f} 円")
            with col2:
                st.metric("支出回数", f"{len(st.session_state.expense_history)} 回")
        
        else:
            st.info("📋 まだ支出が記録されていません。レシート解析タブから支出を記録してみましょう！")
    
    with tab4:
        st.header("⚙️ 設定")
        
        # APIキー設定
        st.subheader("🔑 Gemini API設定")
        api_key_input = st.text_input(
            "Gemini APIキー",
            value=st.session_state.gemini_api_key,
            type="password",
            help="Google AI StudioでAPIキーを取得してください"
        )
        
        if st.button("💾 APIキーを保存"):
            st.session_state.gemini_api_key = api_key_input
            st.success("✅ APIキーを保存しました！")
        
        st.markdown("---")
        
        # データ管理
        st.subheader("🗂️ データ管理")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 支出履歴のみリセット", type="secondary"):
                if st.session_state.expense_history:
                    st.session_state.total_spent = 0.0
                    st.session_state.expense_history = []
                    st.success("支出履歴をリセットしました！")
                    st.rerun()
                else:
                    st.info("リセットする支出履歴がありません")
        
        with col2:
            if st.button("🗑️ 全データリセット", type="secondary"):
                st.session_state.monthly_allowance = 0.0
                st.session_state.total_spent = 0.0
                st.session_state.expense_history = []
                st.success("全データをリセットしました！")
                st.rerun()
        
        # アプリ情報
        st.markdown("---")
        st.subheader("ℹ️ アプリについて")
        st.info("""
        **お小遣いレコーダー v2.0**
        
        📱 主な機能:
        - AI powered レシート自動解析
        - リアルタイム残高表示
        - 月次自動リセット
        - 支出履歴管理
        - 予算オーバー警告
        
        💡 使い方:
        1. 月初に予算を設定
        2. Gemini APIキーを設定
        3. レシートを撮影してアップロード
        4. AI解析結果を確認して記録
        5. 残り予算をリアルタイムで確認
        """)

# --- ⑨ サイドバー ---
with st.sidebar:
    st.markdown("### 🎯 クイックステータス")
    
    # 現在の状況をサイドバーにも表示
    if st.session_state.monthly_allowance > 0:
        progress = min(st.session_state.total_spent / st.session_state.monthly_allowance, 1.0)
        st.progress(progress)
        st.caption(f"予算使用率: {progress * 100:.1f}%")
    
    remaining = calculate_remaining_balance(st.session_state.monthly_allowance, st.session_state.total_spent)
    if remaining >= 0:
        st.success(f"残り: {remaining:,.0f}円")
    else:
        st.error(f"オーバー: {abs(remaining):,.0f}円")
    
    st.markdown("---")
    st.markdown("### 📖 使い方ガイド")
    st.markdown("""
    1. **予算設定タブ**で月の予算を設定
    2. **設定タブ**でGemini APIキーを入力
    3. **レシート解析タブ**で写真をアップロード
    4. AI解析結果を確認して支出を記録
    5. 残り予算をリアルタイムで確認
    """)
    
    st.markdown("---")
    current_date = datetime.datetime.now().strftime("%Y年%m月%d日")
    st.caption(f"📅 {current_date}")

# --- ⑩ メイン処理の実行 ---
if __name__ == "__main__":
    run_allowance_recorder_app()
