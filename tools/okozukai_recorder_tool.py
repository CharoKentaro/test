# ===============================================================
# ★★★ okozukai_recorder_tool.py ＜アーキテクチャ刷新・最終版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
from streamlit_local_storage import LocalStorage 
import json
from PIL import Image
import pandas as pd
from datetime import datetime, timedelta, timezone
import time

# --- プロンプトや補助関数 ---
GEMINI_PROMPT = """あなたはレシート解析のプロです。アップロードされたレシートの画像から、以下の情報を正確に抽出し、指定されたJSON形式で出力してください。

# 命令
- レシートに記載されている「合計金額」を抽出してください。
- レシートに記載されている「品目リスト」を抽出してください。リストには各品物の「品物名(name)」と「金額(price)」を含めてください。
- 「軽減税率対象」や「※」などの記号は品物名に含めないでください。
- 小計や割引、ポイント利用額などは無視し、最終的な支払総額を「合計金額」としてください。

# 出力形式 (JSON)
{
  "total_amount": (ここに合計金額の数値を入力),
  "items": [
    {"name": "(品物名1)", "price": (金額1)},
    {"name": "(品物名2)", "price": (金額2)},
    ...
  ]
}
"""
def calculate_remaining_balance(monthly_allowance, total_spent):
    return monthly_allowance - total_spent
def format_balance_display(balance):
    if balance >= 0:
        return f"🟢 **{balance:,.0f} 円**"
    else:
        return f"🔴 **{abs(balance):,.0f} 円 (予算オーバー)**"

# --- メイン関数 ---
def show_tool(gemini_api_key, localS: LocalStorage):
    st.header("💰 お小遣い管理", divider='rainbow')
    
    prefix = "okozukai_"
    key_allowance = f"{prefix}monthly_allowance"
    key_total_spent = f"{prefix}total_spent"
    key_all_receipts = f"{prefix}all_receipt_data"

    # --- Step 1: 初期化 ---
    # 初回実行時のみ、LocalStorageから値を読み込んでst.session_stateを初期化する
    if f"{prefix}initialized" not in st.session_state:
        # 常にfloatとして扱うことで、データ型の不整合を防ぐ
        st.session_state[key_allowance] = float(localS.getItem(key_allowance) or 0.0)
        st.session_state[key_total_spent] = float(localS.getItem(key_total_spent) or 0.0)
        st.session_state[key_all_receipts] = localS.getItem(key_all_receipts) or []
        st.session_state[f"{prefix}receipt_preview"] = None
        st.session_state[f"{prefix}usage_count"] = 0
        st.session_state[f"{prefix}initialized"] = True

    # --- 新アーキテクチャの核心部 ---
    # --- Step 2: 状態の同期 ---
    # 「st.session_state（正義）」と「LocalStorage（バックアップ）」を比較し、
    # 値が異なっていれば、「正義」の値を「バックアップ」に反映（＝保存）する
    try:
        session_val = float(st.session_state.get(key_allowance, 0.0))
        storage_val = float(localS.getItem(key_allowance) or 0.0)

        if session_val != storage_val:
            localS.setItem(key_allowance, session_val, key="okozukai_allowance_storage_sync")
            st.toast(f"✅ 設定をブラウザに保存しました！", icon="💾")
    except (ValueError, TypeError):
        pass

    usage_limit = 1
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit

    if is_limit_reached:
        # アンロック・モード
        st.success("🎉 たくさんのご利用、ありがとうございます！")
        st.info("このツールが、あなたの家計管理の一助となれば幸いです。")
        st.warning("レシートの読み込みを続けるには、応援ページで「今日の合言葉（4桁の数字）」を確認し、入力してください。")
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue2.html"
        st.markdown(f'<a href="{portal_url}" target="_blank">応援ページで「今日の合言葉」を確認する →</a>', unsafe_allow_html=True)
        st.divider()
        password_input = st.text_input("ここに「今日の合言葉」を入力してください:", type="password", key=f"{prefix}password_input")
        if st.button("レシートの読み込み回数をリセットする", key=f"{prefix}unlock_button"):
            JST = timezone(timedelta(hours=+9))
            today_int = int(datetime.now(JST).strftime('%Y%m%d'))
            seed_str = st.secrets.get("unlock_seed", "0")
            seed_int = int(seed_str) if seed_str.isdigit() else 0
            correct_password = str((today_int + seed_int) % 10000).zfill(4)
            if password_input == correct_password:
                st.session_state[f"{prefix}usage_count"] = 0
                st.balloons()
                st.success("ありがとうございます！レシートの読み込み回数がリセットされました。")
                time.sleep(2)
                st.rerun()
            else:
                st.error("合言葉が違うようです。応援ページで、もう一度ご確認ください。")

    elif st.session_state[f"{prefix}receipt_preview"]:
        # 確認モード
        st.subheader("📝 支出の確認")
        st.info("AIが読み取った内容を確認・修正し、問題なければ「確定」してください。")
        preview_data = st.session_state[f"{prefix}receipt_preview"]
        corrected_amount = st.number_input("AIが読み取った合計金額はこちらです。必要なら修正してください。", value=preview_data['total_amount'], min_value=0.0, step=1.0, key=f"{prefix}correction_input")
        st.write("📋 **品目リスト（直接編集できます）**")
        if preview_data['items']:
            df_items = pd.DataFrame(preview_data['items'])
            df_items['price'] = pd.to_numeric(df_items['price'], errors='coerce').fillna(0)
        else:
            df_items = pd.DataFrame([{"name": "", "price": 0}])
            st.info("AIは品目を検出できませんでした。手動で追加・修正してください。")
        edited_df = st.data_editor(df_items, num_rows="dynamic", column_config={"name": st.column_config.TextColumn("品物名", required=True, width="large"), "price": st.column_config.NumberColumn("金額（円）", format="%d円", required=True)}, key=f"{prefix}data_editor", use_container_width=True)
        st.divider()
        st.write("📊 **支出後の残高プレビュー**")
        current_allowance = st.session_state[key_allowance]
        current_spent = st.session_state[key_total_spent]
        projected_spent = current_spent + corrected_amount
        projected_balance = calculate_remaining_balance(current_allowance, projected_spent)
        col1, col2, col3 = st.columns(3)
        col1.metric("今月の予算", f"{current_allowance:,.0f} 円")
        col2.metric("使った金額", f"{projected_spent:,.0f} 円", delta=f"+{corrected_amount:,.0f} 円", delta_color="inverse")
        col3.metric("残り予算", f"{projected_balance:,.0f} 円", delta=f"-{corrected_amount:,.0f} 円", delta_color="inverse")
        st.divider()
        confirm_col, cancel_col = st.columns(2)
        if confirm_col.button("💰 この金額で支出を確定する", type="primary", use_container_width=True):
            st.session_state[key_total_spent] += corrected_amount
            new_receipt_record = {"date": datetime.now().strftime('%Y-%m-%d %H:%M'), "total_amount": corrected_amount, "items": edited_df.to_dict('records')}
            st.session_state[key_all_receipts].append(new_receipt_record)
            localS.setItem(key_total_spent, st.session_state[key_total_spent], key="okozukai_total_spent_storage")
            localS.setItem(key_all_receipts, st.session_state[key_all_receipts], key="okozukai_receipts_storage")
            st.session_state[f"{prefix}receipt_preview"] = None
            st.success(f"🎉 {corrected_amount:,.0f} 円の支出を記録しました！")
            st.balloons()
            time.sleep(2)
            st.rerun()
        if cancel_col.button("❌ キャンセル", use_container_width=True):
            st.session_state[f"{prefix}receipt_preview"] = None
            st.rerun()

    else:
        # --- Step 3: UIの描画と操作 ---
        # UIは常に「正義」である st.session_state を参照して描画される
        st.info("レシートを登録して、今月使えるお金を管理しよう！")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、レシートを読み込めます。")

        with st.expander("💳 今月のお小遣い設定", expanded=(st.session_state[key_allowance] == 0)):
            st.warning("⚠️ **ご注意**: ブラウザの「プライベートモード」や「シークレットモード」では、設定した金額が保存されません。通常のモードでご利用ください。")
            
            def update_session_state():
                input_val = st.session_state[f"{prefix}allowance_input_key"]
                st.session_state[key_allowance] = float(input_val)

            st.number_input(
                "今月のお小遣いを入力してください", 
                value=float(st.session_state[key_allowance]), 
                step=1000.0, 
                min_value=0.0,
                key=f"{prefix}allowance_input_key",
                on_change=update_session_state
            )
            
        st.divider()
        st.subheader("📊 現在の状況")
        current_allowance = st.session_state[key_allowance]
        current_spent = st.session_state[key_total_spent]
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
        st.subheader("📸 レシートを登録する")
        uploaded_file = st.file_uploader("📁 レシート画像をアップロード", type=['png', 'jpg', 'jpeg'], key=f"{prefix}uploader")
        if uploaded_file:
            st.image(uploaded_file, caption="解析対象のレシート", width=300)
            if st.button("⬆️ このレシートを解析する", use_container_width=True, type="primary"):
                if not gemini_api_key: 
                    st.warning("サイドバーからGemini APIキーを設定してください。")
                else:
                    try:
                        with st.spinner("🧠 AIがレシートを解析中..."):
                            genai.configure(api_key=gemini_api_key)
                            model = genai.GenerativeModel('gemini-1.5-flash-latest')
                            image = Image.open(uploaded_file)
                            gemini_response = model.generate_content([GEMINI_PROMPT, image])
                            cleaned_text = gemini_response.text.strip().replace("```json", "```").replace("```", "")
                            extracted_data = json.loads(cleaned_text)
                        
                        st.session_state[f"{prefix}usage_count"] += 1
                        st.session_state[f"{prefix}receipt_preview"] = {"total_amount": float(extracted_data.get("total_amount", 0)), "items": extracted_data.get("items", [])}
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 解析エラー: {e}")
                        if 'gemini_response' in locals(): st.code(gemini_response.text, language="text")
        
        st.divider()
        st.subheader("📜 支出履歴")
        if st.session_state[key_all_receipts]:
            display_list = []
            for receipt in reversed(st.session_state[key_all_receipts]):
                date = receipt.get('date', 'N/A')
                total = receipt.get('total_amount', 0)
                items = receipt.get('items', [])
                item_names = ", ".join([item.get('name', 'N/A') for item in items]) if items else "品目なし"
                display_list.append({"日付": date, "合計金額": f"{total:,.0f} 円", "主な品目": item_names})
            if display_list:
                st.dataframe(display_list, use_container_width=True)
