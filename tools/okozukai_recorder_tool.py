# ===============================================================
# ★★★ okozukai_recorder_tool.py ＜ハイブリッド記憶・修正版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
from streamlit_local_storage import LocalStorage
import json
from PIL import Image
import pandas as pd
from datetime import datetime, timedelta, timezone
import time

# --- プロンプトや補助関数（省略） ---
GEMINI_PROMPT = """..."""
def calculate_remaining_balance(monthly_allowance, total_spent):
    return monthly_allowance - total_spent
def format_balance_display(balance):
    if balance >= 0:
        return f"🟢 **{balance:,.0f} 円**"
    else:
        return f"🔴 **{abs(balance):,.0f} 円 (予算オーバー)**"

# ===============================================================
# LocalStorageから安全にデータを取得する関数
# ===============================================================
def safe_get_from_storage(local_storage, key, default_value, data_type=float):
    """LocalStorageから安全にデータを取得する"""
    try:
        value = local_storage.getItem(key)
        if value is None or value == "":
            return default_value
        
        if data_type == float:
            return float(value)
        elif data_type == int:
            return int(value)
        elif data_type == list:
            if isinstance(value, str):
                return json.loads(value)
            return value if isinstance(value, list) else default_value
        else:
            return value
    except Exception as e:
        st.warning(f"データの読み込みでエラーが発生しました（{key}）: {e}")
        return default_value

# ===============================================================
# LocalStorageに安全にデータを保存する関数
# ===============================================================
def safe_set_to_storage(local_storage, key, value):
    """LocalStorageに安全にデータを保存する"""
    try:
        if isinstance(value, (list, dict)):
            local_storage.setItem(key, json.dumps(value, ensure_ascii=False))
        else:
            local_storage.setItem(key, value)
        return True
    except Exception as e:
        st.error(f"データの保存でエラーが発生しました（{key}）: {e}")
        return False

# ===============================================================
# メインの仕事 - 最後の答え
# ===============================================================
def show_tool(gemini_api_key):
    st.header("💰 お小遣い管理", divider='rainbow')

    try:
        localS = LocalStorage()
    except Exception as e:
        st.error(f"🚨 重大なエラー：ローカルストレージの初期化に失敗しました。エラー詳細: {e}")
        st.stop()
        
    prefix = "okozukai_"
    
    # --- LocalStorageで使う、聖なるキーを定義 ---
    key_allowance = f"{prefix}monthly_allowance"
    key_total_spent = f"{prefix}total_spent"
    key_all_receipts = f"{prefix}all_receipt_data"

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★ 『聖別と、信頼の儀式』（改良版初期化） ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    
    # セッション状態の初期化を毎回確実に行う
    initialization_key = f"{prefix}initialized_v2"
    
    # デバッグ情報の表示（必要に応じてコメントアウト）
    with st.expander("🔧 デバッグ情報", expanded=False):
        st.write("LocalStorageの生データ:")
        try:
            raw_allowance = localS.getItem(key_allowance)
            raw_spent = localS.getItem(key_total_spent)
            raw_receipts = localS.getItem(key_all_receipts)
            st.write(f"- {key_allowance}: {raw_allowance} (型: {type(raw_allowance)})")
            st.write(f"- {key_total_spent}: {raw_spent} (型: {type(raw_spent)})")
            st.write(f"- {key_all_receipts}: {raw_receipts} (型: {type(raw_receipts)})")
        except Exception as e:
            st.write(f"デバッグ情報取得エラー: {e}")
    
    # LocalStorageからデータを安全に取得
    allowance = safe_get_from_storage(localS, key_allowance, 0.0, float)
    total_spent = safe_get_from_storage(localS, key_total_spent, 0.0, float)
    all_receipts = safe_get_from_storage(localS, key_all_receipts, [], list)
    
    # セッション状態に設定（初期化フラグに関係なく毎回実行）
    st.session_state[f"{prefix}monthly_allowance"] = allowance
    st.session_state[f"{prefix}total_spent"] = total_spent
    st.session_state[f"{prefix}all_receipts"] = all_receipts
    
    # その他のセッション状態を初期化（初回のみ）
    if initialization_key not in st.session_state:
        st.session_state[f"{prefix}receipt_preview"] = None
        st.session_state[f"{prefix}usage_count"] = 0
        st.session_state[initialization_key] = True

    usage_limit = 1
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit

    # --- これ以降のコードは、すべて、聖別された session_state のみを信頼する ---
    
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★ 『ハイブリッド記憶システム』の神殿 ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    with st.expander("🗂️ データ管理：データの保存と復元"):
        st.info("データは通常ブラウザに自動保存されますが、万が一に備え、手動で保存・復元ができます。")
        
        # --- 『記憶の結晶』のダウンロード ---
        all_data = {
            "monthly_allowance": st.session_state[f"{prefix}monthly_allowance"],
            "total_spent": st.session_state[f"{prefix}total_spent"],
            "all_receipts": st.session_state[f"{prefix}all_receipts"],
        }
        json_data = json.dumps(all_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="✅ 全データをファイルに保存する",
            data=json_data.encode('utf-8-sig'),
            file_name="okozukai_data.json",
            mime="application/json",
            help="現在の予算設定や支出履歴を、一つのファイルとしてお使いのPCに保存します。"
        )

        # --- 『記憶の継承』のアップロード ---
        uploaded_data_file = st.file_uploader("📂 保存したファイルからデータを復元する", type=['json'], key=f"{prefix}data_uploader")
        if uploaded_data_file is not None:
            try:
                restored_data = json.load(uploaded_data_file)
                st.session_state[f"{prefix}monthly_allowance"] = float(restored_data.get("monthly_allowance", 0.0))
                st.session_state[f"{prefix}total_spent"] = float(restored_data.get("total_spent", 0.0))
                st.session_state[f"{prefix}all_receipts"] = restored_data.get("all_receipts", [])
                
                # ★★★ 復元したデータを、LocalStorageにも安全に保存 ★★★
                safe_set_to_storage(localS, key_allowance, st.session_state[f"{prefix}monthly_allowance"])
                safe_set_to_storage(localS, key_total_spent, st.session_state[f"{prefix}total_spent"])
                safe_set_to_storage(localS, key_all_receipts, st.session_state[f"{prefix}all_receipts"])

                st.success("データの復元に成功しました！")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"データの復元に失敗しました。ファイルが破損している可能性があります。エラー: {e}")

        st.divider()
        # --- 全データリセットボタン ---
        if st.button("⚠️ 全てのデータをリセットする", use_container_width=True, type="secondary", help="現在の予算設定や支出履歴を、すべて消去します。"):
            st.session_state[f"{prefix}monthly_allowance"] = 0.0
            st.session_state[f"{prefix}total_spent"] = 0.0
            st.session_state[f"{prefix}all_receipts"] = []
            st.session_state[f"{prefix}receipt_preview"] = None
            st.session_state[f"{prefix}usage_count"] = 0
            
            # ★★★ LocalStorageをリセット ★★★
            safe_set_to_storage(localS, key_allowance, 0.0)
            safe_set_to_storage(localS, key_total_spent, 0.0)
            safe_set_to_storage(localS, key_all_receipts, [])
            
            st.success("全データをリセットしました！"); time.sleep(1); st.rerun()

    st.divider()

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
        current_allowance = st.session_state[f"{prefix}monthly_allowance"]
        current_spent = st.session_state[f"{prefix}total_spent"]
        projected_spent = current_spent + corrected_amount
        projected_balance = calculate_remaining_balance(current_allowance, projected_spent)
        col1, col2, col3 = st.columns(3)
        col1.metric("今月の予算", f"{current_allowance:,.0f} 円")
        col2.metric("使った金額", f"{projected_spent:,.0f} 円", delta=f"+{corrected_amount:,.0f} 円", delta_color="inverse")
        col3.metric("残り予算", f"{projected_balance:,.0f} 円", delta=f"-{corrected_amount:,.0f} 円", delta_color="inverse")
        st.divider()
        confirm_col, cancel_col = st.columns(2)
        if confirm_col.button("💰 この金額で支出を確定する", type="primary", use_container_width=True):
            st.session_state[f"{prefix}total_spent"] += corrected_amount
            new_receipt_record = {"date": datetime.now().strftime('%Y-%m-%d %H:%M'), "total_amount": corrected_amount, "items": edited_df.to_dict('records')}
            st.session_state[f"{prefix}all_receipts"].append(new_receipt_record)
            st.session_state[f"{prefix}receipt_preview"] = None
            
            # LocalStorageに安全に保存
            safe_set_to_storage(localS, key_total_spent, st.session_state[f"{prefix}total_spent"])
            safe_set_to_storage(localS, key_all_receipts, st.session_state[f"{prefix}all_receipts"])
            
            st.success(f"🎉 {corrected_amount:,.0f} 円の支出を記録しました！")
            st.balloons()
            time.sleep(2)
            st.rerun()
        if cancel_col.button("❌ キャンセル", use_container_width=True):
            st.session_state[f"{prefix}receipt_preview"] = None
            st.rerun()
    else:
        # 通常モード
        st.info("レシートを登録して、今月使えるお金を管理しよう！")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、レシートを読み込めます。")

        with st.expander("💳 今月のお小遣い設定", expanded=(st.session_state[f"{prefix}monthly_allowance"] == 0)):
             with st.form(key=f"{prefix}allowance_form"):
                new_allowance = st.number_input("今月のお小遣いを入力してください", value=st.session_state[f"{prefix}monthly_allowance"], step=1000.0, min_value=0.0)
                if st.form_submit_button("この金額で設定する", use_container_width=True):
                    st.session_state[f"{prefix}monthly_allowance"] = new_allowance
                    # LocalStorageに安全に保存
                    safe_set_to_storage(localS, key_allowance, new_allowance)
                    st.success(f"今月のお小遣いを {new_allowance:,.0f} 円に設定しました！")
                    st.rerun()
        
        st.divider()
        st.subheader("📊 現在の状況")
        current_allowance = st.session_state[f"{prefix}monthly_allowance"]
        current_spent = st.session_state[f"{prefix}total_spent"]
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
                if not gemini_api_key: st.warning("サイドバーからGemini APIキーを設定してください。")
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
        if st.session_state[f"{prefix}all_receipts"]:
            display_list = []
            for receipt in reversed(st.session_state[f'{prefix}all_receipts']):
                date = receipt.get('date', 'N/A')
                total = receipt.get('total_amount', 0)
                items = receipt.get('items', [])
                item_names = ", ".join([item.get('name', 'N/A') for item in items]) if items else "品目なし"
                display_list.append({"日付": date, "合計金額": f"{total:,.0f} 円", "主な品目": item_names})
            if display_list:
                st.dataframe(display_list, use_container_width=True)
