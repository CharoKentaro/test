# ===============================================================
# ★★★ app.py ＜プロンプト復活・最終完成版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import json
from pathlib import Path
from PIL import Image
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
from tools import translator_tool, calendar_tool, gijiroku_tool, kensha_no_kioku_tool, ai_memory_partner_tool

# ---------------------------------------------------------------
# Section 1: 永続化のためのコア機能
# ---------------------------------------------------------------
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

# ---------------------------------------------------------------
# Section 2: お小遣い管理ツールのための補助関数
# ---------------------------------------------------------------
def calculate_remaining_balance(monthly_allowance, total_spent):
    return monthly_allowance - total_spent

def format_balance_display(balance):
    if balance >= 0:
        return f"🟢 **{balance:,.0f} 円**"
    else:
        return f"🔴 **{abs(balance):,.0f} 円 (予算オーバー)**"

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★ ここが、復活させた「AIへの指示書」です ★★★
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
OKOZUKAI_PROMPT = """あなたは、レシートの画像を直接解析する、超優秀な経理アシスタントAIです。
# 指示
レシートの画像の中から、以下の情報を注意深く、正確に抽出してください。
1.  **合計金額 (total_amount)**: 支払いの総額。
2.  **購入品リスト (items)**: 購入した「品物名(name)」と「その単価(price)」のリスト。
# 出力形式
*   抽出した結果を、必ず以下のJSON形式で出力してください。
*   数値は、数字のみを抽出してください（円やカンマは不要）。
*   値が見つからない場合は、数値項目は "0"、リスト項目は空のリスト `[]` としてください。
*   「小計」「お預り」「お釣り」「店名」「合計」といった単語そのものは、購入品リストに含めないでください。
*   JSON以外の、前置きや説明は、絶対に出力しないでください。
{
  "total_amount": "ここに合計金額の数値",
  "items": [
    { "name": "ここに品物名1", "price": "ここに単価1" },
    { "name": "ここに品物名2", "price": "ここに単価2" }
  ]
}
"""

# ---------------------------------------------------------------
# Section 3: Streamlit アプリケーション本体
# ---------------------------------------------------------------
st.set_page_config(page_title="Multi-Tool Portal", page_icon="🚀", layout="wide")

# --- アプリ全体のデータ管理 ---
if 'app_state' not in st.session_state:
    st.session_state.app_state = read_app_state()

# --- サイドバー ---
with st.sidebar:
    st.title("🚀 Multi-Tool Portal")
    st.divider()
    
    # APIキー管理
    app_s_sidebar = st.session_state.app_state
    if 'gemini_api_key' not in app_s_sidebar: app_s_sidebar['gemini_api_key'] = ''
    with st.expander("⚙️ APIキーの設定", expanded=(not app_s_sidebar.get('gemini_api_key', ''))):
        with st.form("api_key_form"):
            api_key_input = st.text_input("Gemini APIキー", type="password", value=app_s_sidebar.get('gemini_api_key', ''))
            col1, col2 = st.columns(2)
            with col1: save_button = st.form_submit_button("💾 保存", use_container_width=True)
            with col2: reset_button = st.form_submit_button("🔄 クリア", use_container_width=True)
    if save_button:
        app_s_sidebar['gemini_api_key'] = api_key_input; write_app_state(app_s_sidebar)
        st.success("キーを保存しました！"); time.sleep(1); st.rerun()
    if reset_button:
        app_s_sidebar['gemini_api_key'] = ''; write_app_state(app_s_sidebar)
        st.success("キーをクリアしました。"); time.sleep(1); st.rerun()
    
    st.divider()
    tool_selection = st.radio("利用するツールを選択してください:", ("💰 お小遣い管理", "🤝 翻訳ツール", "📅 カレンダー登録", "📝 議事録作成", "🧠 賢者の記憶", "❤️ 認知予防ツール"), key="tool_selection")
    st.divider()
    st.markdown("""<div style="font-size: 0.9em;"><a href="https://aistudio.google.com/app/apikey" target="_blank">Gemini APIキーの取得はこちら</a></div>""", unsafe_allow_html=True)

# --- メインコンテンツの分岐 ---
api_key = st.session_state.app_state.get('gemini_api_key', '')

if tool_selection == "💰 お小遣い管理":
    st.header("💰 お小遣い管理", divider='rainbow')

    # 状態管理キーの定義
    okozukai_prefix = "okozukai_"
    key_allowance = f"{okozukai_prefix}monthly_allowance"
    key_total_spent = f"{okozukai_prefix}total_spent"
    key_all_receipts = f"{okozukai_prefix}all_receipts"
    key_usage_count = f"{okozukai_prefix}usage_count"
    
    # 状態の初期化
    app_s = st.session_state.app_state
    if key_allowance not in app_s: app_s[key_allowance] = 0.0
    if key_total_spent not in app_s: app_s[key_total_spent] = 0.0
    if key_all_receipts not in app_s: app_s[key_all_receipts] = []
    if key_usage_count not in app_s: app_s[key_usage_count] = 0
    if 'receipt_preview' not in st.session_state: st.session_state.receipt_preview = None

    usage_limit = 1
    is_limit_reached = app_s.get(key_usage_count, 0) >= usage_limit

    # UIの分岐ロジック
    if is_limit_reached:
        st.success("🎉 たくさんのご利用、ありがとうございます！")
        st.info("このツールが、あなたの家計管理の一助となれば幸いです。")
        st.warning("レシートの読み込みを続けるには、応援ページで「今日の合言葉（4桁の数字）」を確認し、入力してください。")
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue2.html"
        st.markdown(f'<a href="{portal_url}" target="_blank">応援ページで「今日の合言葉」を確認する →</a>', unsafe_allow_html=True)
        st.divider()
        with st.form("password_form"):
            password_input = st.text_input("ここに「今日の合言葉」を入力してください:", type="password")
            if st.form_submit_button("レシートの読み込み回数をリセットする"):
                JST = timezone(timedelta(hours=+9)); today_int = int(datetime.now(JST).strftime('%Y%m%d'))
                seed_str = st.secrets.get("unlock_seed", "0"); seed_int = int(seed_str) if seed_str.isdigit() else 0
                correct_password = str((today_int + seed_int) % 10000).zfill(4)
                if password_input == correct_password:
                    app_s[key_usage_count] = 0; write_app_state(app_s)
                    st.balloons(); st.success("ありがとうございます！読み込み回数がリセットされました。")
                    time.sleep(2); st.rerun()
                else: st.error("合言葉が違うようです。応援ページで、もう一度ご確認ください。")

    elif st.session_state.receipt_preview:
        st.subheader("📝 支出の確認")
        st.info("AIが読み取った内容を確認・修正し、問題なければ「確定」してください。")
        preview_data = st.session_state.receipt_preview
        corrected_amount = st.number_input("合計金額", value=float(preview_data.get('total_amount', 0.0)), min_value=0.0, step=1.0)
        items_data = preview_data.get('items', [])
        df_items = pd.DataFrame(items_data) if items_data else pd.DataFrame([{"name": "", "price": 0.0}])
        edited_df = st.data_editor(df_items, num_rows="dynamic", column_config={"name": st.column_config.TextColumn("品物名", required=True), "price": st.column_config.NumberColumn("金額", format="%.0f円")}, use_container_width=True)
        col_confirm, col_cancel = st.columns(2)
        if col_confirm.button("💰 この金額で支出を確定する", type="primary", use_container_width=True):
            app_s[key_total_spent] += corrected_amount
            app_s[key_all_receipts].append({"date": datetime.now().strftime('%Y-%m-%d %H:%M'), "total_amount": corrected_amount, "items": edited_df.to_dict('records')})
            write_app_state(app_s)
            st.session_state.receipt_preview = None
            st.success("支出を記録しました！"); st.balloons(); time.sleep(1); st.rerun()
        if col_cancel.button("❌ キャンセル", use_container_width=True):
            st.session_state.receipt_preview = None; st.rerun()
            
    else:
        st.info("レシートを登録して、今月使えるお金を管理しよう！")
        st.caption(f"🚀 あと {usage_limit - app_s.get(key_usage_count, 0)} 回、レシートを読み込めます。")
        with st.expander("💳 今月のお小遣い設定", expanded=(app_s.get(key_allowance, 0) == 0)):
            with st.form(key="allowance_form"):
                new_allowance = st.number_input("今月のお小遣い", value=float(app_s.get(key_allowance, 0)), step=1000.0)
                if st.form_submit_button("この金額で設定する", type="primary", use_container_width=True):
                    app_s[key_allowance] = new_allowance; write_app_state(app_s)
                    st.success(f"お小遣いを {new_allowance:,.0f} 円に設定しました！"); time.sleep(1); st.rerun()
        
        st.divider()
        st.subheader("📊 現在の状況")
        current_allowance = app_s.get(key_allowance, 0.0)
        current_spent = app_s.get(key_total_spent, 0.0)
        remaining_balance = calculate_remaining_balance(current_allowance, current_spent)
        col1, col2 = st.columns(2)
        col1.metric("今月の予算", f"{current_allowance:,.0f} 円"); col2.metric("使った金額", f"{current_spent:,.0f} 円")
        st.markdown(f"<p style='text-align: center; font-size: 2.0em; font-weight: bold;'>残り予算: {format_balance_display(remaining_balance)}</p>", unsafe_allow_html=True)
        if current_allowance > 0: st.progress(min(current_spent / current_allowance, 1.0))

        st.divider()
        st.subheader("📸 レシートを登録する")
        uploaded_file = st.file_uploader("📁 画像をアップロード", type=['png', 'jpg', 'jpeg'])
        if uploaded_file:
            st.image(uploaded_file, caption="解析対象のレシート", width=300)
            if st.button("⬆️ このレシートを解析する", type="primary", use_container_width=True):
                if not api_key: st.warning("サイドバーからGemini APIキーを設定してください。")
                else:
                    try:
                        app_s[key_usage_count] += 1; write_app_state(app_s)
                        with st.spinner("🧠 AIがレシートを解析中..."):
                            genai.configure(api_key=api_key); model = genai.GenerativeModel('gemini-1.5-flash-latest')
                            image = Image.open(uploaded_file); response = model.generate_content([OKOZUKAI_PROMPT, image])
                            extracted_data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
                        st.session_state.receipt_preview = extracted_data; st.rerun()
                    except Exception as e:
                        app_s[key_usage_count] -= 1; write_app_state(app_s)
                        st.error(f"❌ 解析エラー: {e}")
        
        st.divider()
        st.subheader("📜 支出履歴とデータ管理")
        if app_s[key_all_receipts]:
            st.info(f"現在、{len(app_s[key_all_receipts])} 件のレシートデータが記録されています。")
            with st.expander("クリックして詳細な支出履歴を表示"):
                for receipt in reversed(app_s[key_all_receipts]):
                    with st.container(border=True):
                        st.write(f"**日時:** {receipt.get('date', 'N/A')} / **合計:** {float(receipt.get('total_amount', 0)):,.0f} 円")
                        items_df = pd.DataFrame(receipt.get('items', []))
                        if not items_df.empty: st.dataframe(items_df, hide_index=True, use_container_width=True)
                        else: st.write("品目情報なし")
            flat_list_for_csv = []
            for receipt in app_s[key_all_receipts]:
                receipt_date = receipt.get('date', 'N/A'); receipt_total = receipt.get('total_amount', 0)
                items = receipt.get('items', [])
                if not items: flat_list_for_csv.append({"日付": receipt_date, "品物名": "品目なし", "金額": 0, "レシート合計": receipt_total})
                else:
                    for item in items: flat_list_for_csv.append({"日付": receipt_date, "品物名": item.get('name', 'N/A'), "金額": item.get('price', 0), "レシート合計": receipt_total})
            if flat_list_for_csv:
                df_for_csv = pd.DataFrame(flat_list_for_csv)
                csv_data = df_for_csv.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(label="✅ 全支出履歴をCSVでダウンロード", data=csv_data, file_name=f"okozukai_history_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
        c1, c2 = st.columns(2)
        if c1.button("支出履歴のみリセット", use_container_width=True, help="使った金額とレシート履歴だけを0にします。"):
            app_s[key_total_spent] = 0.0; app_s[key_all_receipts] = []; write_app_state(app_s)
            st.success("支出履歴をリセットしました！"); time.sleep(1); st.rerun()
        if c2.button("⚠️ 全データ完全初期化", use_container_width=True, help="予算設定も含め、このツールの全データを消去します。", type="secondary"):
            app_s[key_allowance] = 0.0; app_s[key_total_spent] = 0.0; app_s[key_all_receipts] = []; app_s[key_usage_count] = 0
            write_app_state(app_s); st.success("全データをリセットしました！"); time.sleep(1); st.rerun()

# --- 他のツールの呼び出し ---
elif tool_selection == "🤝 翻訳ツール": translator_tool.show_tool(gemini_api_key=api_key)
elif tool_selection == "📅 カレンダー登録": calendar_tool.show_tool(gemini_api_key=api_key)
elif tool_selection == "📝 議事録作成": gijiroku_tool.show_tool(gemini_api_key=api_key)
elif tool_selection == "🧠 賢者の記憶": kensha_no_kioku_tool.show_tool(gemini_api_key=api_key)
elif tool_selection == "❤️ 認知予防ツール": ai_memory_partner_tool.show_tool(gemini_api_key=api_key)
