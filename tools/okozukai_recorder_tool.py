# ===============================================================
# ★★★ okozukai_recorder_tool.py ＜多重永続化対応版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
import os
import tempfile
from pathlib import Path

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
# 永続化システム
# ===============================================================
def get_data_file_path():
    """データファイルのパスを取得"""
    # Streamlitの一時ディレクトリを使用
    temp_dir = Path(tempfile.gettempdir()) / "streamlit_okozukai"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir / "okozukai_data.json"

def save_data_to_file(data):
    """データをファイルに保存"""
    try:
        file_path = get_data_file_path()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"ファイル保存エラー: {e}")
        return False

def load_data_from_file():
    """ファイルからデータを読み込み"""
    try:
        file_path = get_data_file_path()
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"ファイル読み込み注意: {e}")
    return None

def get_url_params():
    """URLパラメータからデータを取得"""
    try:
        # Streamlit 1.28.0以降のクエリパラメータ取得方法
        query_params = st.experimental_get_query_params() if hasattr(st, 'experimental_get_query_params') else {}
        
        data = {}
        if 'allowance' in query_params:
            data['monthly_allowance'] = float(query_params['allowance'][0])
        if 'spent' in query_params:
            data['total_spent'] = float(query_params['spent'][0])
        if 'receipts' in query_params:
            data['all_receipts'] = json.loads(query_params['receipts'][0])
        
        return data if data else None
    except Exception as e:
        st.warning(f"URL パラメータ読み込み注意: {e}")
        return None

def set_url_params(data):
    """URLパラメータにデータを設定"""
    try:
        query_params = {
            'allowance': [str(data.get('monthly_allowance', 0))],
            'spent': [str(data.get('total_spent', 0))],
            'receipts': [json.dumps(data.get('all_receipts', []), ensure_ascii=False)]
        }
        if hasattr(st, 'experimental_set_query_params'):
            st.experimental_set_query_params(**query_params)
    except Exception as e:
        st.warning(f"URL パラメータ設定注意: {e}")

# ===============================================================
# ブラウザ永続化（Cookieスタイル）
# ===============================================================
def create_persistent_storage():
    """永続化ストレージを作成"""
    storage_js = """
    <div id="persistent_storage" style="display:none;"></div>
    <script>
    // データを複数の方法で保存
    function savePersistentData(key, value) {
        const dataStr = JSON.stringify(value);
        
        // 1. LocalStorage
        try {
            localStorage.setItem('okozukai_' + key, dataStr);
        } catch(e) { console.log('LocalStorage失敗:', e); }
        
        // 2. SessionStorage
        try {
            sessionStorage.setItem('okozukai_' + key, dataStr);
        } catch(e) { console.log('SessionStorage失敗:', e); }
        
        // 3. Cookie (有効期限30日)
        try {
            const expires = new Date();
            expires.setTime(expires.getTime() + (30*24*60*60*1000));
            document.cookie = 'okozukai_' + key + '=' + encodeURIComponent(dataStr) + ';expires=' + expires.toUTCString() + ';path=/';
        } catch(e) { console.log('Cookie失敗:', e); }
        
        // 4. IndexedDB (簡易版)
        try {
            if ('indexedDB' in window) {
                const request = indexedDB.open('OkozukaiDB', 1);
                request.onsuccess = function(event) {
                    const db = event.target.result;
                    if (db.objectStoreNames.contains('data')) {
                        const transaction = db.transaction(['data'], 'readwrite');
                        const objectStore = transaction.objectStore('data');
                        objectStore.put({id: key, value: dataStr});
                    }
                };
                request.onupgradeneeded = function(event) {
                    const db = event.target.result;
                    if (!db.objectStoreNames.contains('data')) {
                        db.createObjectStore('data', {keyPath: 'id'});
                    }
                };
            }
        } catch(e) { console.log('IndexedDB失敗:', e); }
    }
    
    // データを複数の方法から読み込み
    function loadPersistentData(key) {
        let data = null;
        
        // 1. LocalStorage
        try {
            data = localStorage.getItem('okozukai_' + key);
            if (data) return JSON.parse(data);
        } catch(e) {}
        
        // 2. SessionStorage
        try {
            data = sessionStorage.getItem('okozukai_' + key);
            if (data) return JSON.parse(data);
        } catch(e) {}
        
        // 3. Cookie
        try {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'okozukai_' + key) {
                    return JSON.parse(decodeURIComponent(value));
                }
            }
        } catch(e) {}
        
        return null;
    }
    
    // Streamlitとの通信
    window.addEventListener('message', function(event) {
        if (event.data.type === 'SAVE_DATA') {
            savePersistentData(event.data.key, event.data.value);
            window.parent.postMessage({type: 'DATA_SAVED', key: event.data.key}, '*');
        } else if (event.data.type === 'LOAD_DATA') {
            const value = loadPersistentData(event.data.key);
            window.parent.postMessage({type: 'DATA_LOADED', key: event.data.key, value: value}, '*');
        }
    });
    
    // 初期データ読み込み
    window.onload = function() {
        const allowance = loadPersistentData('monthly_allowance');
        const spent = loadPersistentData('total_spent');
        const receipts = loadPersistentData('all_receipts');
        
        window.parent.postMessage({
            type: 'INITIAL_DATA_LOADED',
            data: {
                monthly_allowance: allowance,
                total_spent: spent,
                all_receipts: receipts
            }
        }, '*');
    };
    </script>
    """
    return storage_js

# ===============================================================
# メインの仕事 - 最後の答え
# ===============================================================
def show_tool(gemini_api_key):
    st.header("💰 お小遣い管理", divider='rainbow')
    
    prefix = "okozukai_"
    
    # 永続化ストレージを初期化
    st.components.v1.html(create_persistent_storage(), height=0, key="persistent_storage")
    
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★ 多重データソースからの読み込み ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    
    if f"{prefix}data_initialized" not in st.session_state:
        # デフォルト値
        default_data = {
            "monthly_allowance": 0.0,
            "total_spent": 0.0,
            "all_receipts": []
        }
        
        loaded_data = default_data.copy()
        data_source = "デフォルト"
        
        # 1. ファイルから読み込み
        file_data = load_data_from_file()
        if file_data:
            loaded_data.update(file_data)
            data_source = "ファイル"
        
        # 2. URLパラメータから読み込み
        url_data = get_url_params()
        if url_data:
            loaded_data.update(url_data)
            data_source = "URL"
        
        # セッション状態に設定
        st.session_state[f"{prefix}monthly_allowance"] = float(loaded_data.get("monthly_allowance", 0))
        st.session_state[f"{prefix}total_spent"] = float(loaded_data.get("total_spent", 0))
        st.session_state[f"{prefix}all_receipts"] = loaded_data.get("all_receipts", [])
        st.session_state[f"{prefix}receipt_preview"] = None
        st.session_state[f"{prefix}usage_count"] = 0
        st.session_state[f"{prefix}data_initialized"] = True
        st.session_state[f"{prefix}data_source"] = data_source
        
        if loaded_data['monthly_allowance'] > 0:
            st.success(f"💾 データを復元しました（ソース: {data_source}） - 予算: {loaded_data['monthly_allowance']:,.0f}円")

    # データ保存関数
    def save_all_data():
        """全てのストレージにデータを保存"""
        current_data = {
            "monthly_allowance": st.session_state[f"{prefix}monthly_allowance"],
            "total_spent": st.session_state[f"{prefix}total_spent"],
            "all_receipts": st.session_state[f"{prefix}all_receipts"]
        }
        
        # 1. ファイルに保存
        save_data_to_file(current_data)
        
        # 2. URLパラメータに保存
        set_url_params(current_data)
        
        # 3. JavaScript永続化ストレージに保存
        for key, value in current_data.items():
            save_js = f"""
            <script>
            window.postMessage({{type: 'SAVE_DATA', key: '{key}', value: {json.dumps(value)}}}, '*');
            </script>
            """
            st.components.v1.html(save_js, height=0, key=f"save_{key}_{hash(str(value)) % 1000}")

    usage_limit = 1
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit

    # デバッグ情報
    with st.expander("🔧 デバッグ情報", expanded=False):
        st.write("現在のデータ:")
        st.write(f"- データソース: {st.session_state.get(f'{prefix}data_source', '不明')}")
        st.write(f"- 予算: {st.session_state.get(f'{prefix}monthly_allowance', 0):,.0f}円")
        st.write(f"- 使用済み: {st.session_state.get(f'{prefix}total_spent', 0):,.0f}円")
        st.write(f"- レシート数: {len(st.session_state.get(f'{prefix}all_receipts', []))}")
        
        st.write("ファイル情報:")
        file_path = get_data_file_path()
        st.write(f"- パス: {file_path}")
        st.write(f"- 存在: {file_path.exists()}")
        if file_path.exists():
            st.write(f"- サイズ: {file_path.stat().st_size} bytes")
        
        col1, col2 = st.columns(2)
        if col1.button("🔄 データを再読み込み"):
            st.session_state[f"{prefix}data_initialized"] = False
            st.rerun()
        
        if col2.button("💾 今すぐ保存"):
            save_all_data()
            st.success("保存完了！")

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★ データ管理セクション ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    with st.expander("🗂️ データ管理"):
        st.info("データは自動的に複数の場所に保存されます（ファイル、URL、ブラウザ）")
        
        # データダウンロード
        all_data = {
            "monthly_allowance": st.session_state[f"{prefix}monthly_allowance"],
            "total_spent": st.session_state[f"{prefix}total_spent"],
            "all_receipts": st.session_state[f"{prefix}all_receipts"],
        }
        json_data = json.dumps(all_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="✅ バックアップファイルをダウンロード",
            data=json_data.encode('utf-8-sig'),
            file_name=f"okozukai_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

        # データ復元
        uploaded_file = st.file_uploader("📂 バックアップから復元", type=['json'])
        if uploaded_file:
            try:
                restored_data = json.load(uploaded_file)
                st.session_state[f"{prefix}monthly_allowance"] = float(restored_data.get("monthly_allowance", 0))
                st.session_state[f"{prefix}total_spent"] = float(restored_data.get("total_spent", 0))
                st.session_state[f"{prefix}all_receipts"] = restored_data.get("all_receipts", [])
                save_all_data()
                st.success("データ復元完了！")
                st.rerun()
            except Exception as e:
                st.error(f"復元エラー: {e}")

        # リセット
        if st.button("⚠️ 全データリセット", type="secondary"):
            st.session_state[f"{prefix}monthly_allowance"] = 0.0
            st.session_state[f"{prefix}total_spent"] = 0.0
            st.session_state[f"{prefix}all_receipts"] = []
            st.session_state[f"{prefix}receipt_preview"] = None
            st.session_state[f"{prefix}usage_count"] = 0
            save_all_data()
            st.success("リセット完了！")
            st.rerun()

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
        # 確認モード（変更なし）
        st.subheader("📝 支出の確認")
        st.info("AIが読み取った内容を確認・修正し、問題なければ「確定」してください。")
        preview_data = st.session_state[f"{prefix}receipt_preview"]
        corrected_amount = st.number_input("AIが読み取った合計金額はこちらです。必要なら修正してください。", 
                                         value=preview_data['total_amount'], min_value=0.0, step=1.0, 
                                         key=f"{prefix}correction_input")
        st.write("📋 **品目リスト（直接編集できます）**")
        if preview_data['items']:
            df_items = pd.DataFrame(preview_data['items'])
            df_items['price'] = pd.to_numeric(df_items['price'], errors='coerce').fillna(0)
        else:
            df_items = pd.DataFrame([{"name": "", "price": 0}])
            st.info("AIは品目を検出できませんでした。手動で追加・修正してください。")
        
        edited_df = st.data_editor(df_items, num_rows="dynamic", 
                                 column_config={
                                     "name": st.column_config.TextColumn("品物名", required=True, width="large"), 
                                     "price": st.column_config.NumberColumn("金額（円）", format="%d円", required=True)
                                 }, 
                                 key=f"{prefix}data_editor", use_container_width=True)
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
            new_receipt_record = {
                "date": datetime.now().strftime('%Y-%m-%d %H:%M'), 
                "total_amount": corrected_amount, 
                "items": edited_df.to_dict('records')
            }
            st.session_state[f"{prefix}all_receipts"].append(new_receipt_record)
            st.session_state[f"{prefix}receipt_preview"] = None
            save_all_data()  # 全データを保存
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
                new_allowance = st.number_input("今月のお小遣いを入力してください", 
                                              value=st.session_state[f"{prefix}monthly_allowance"], 
                                              step=1000.0, min_value=0.0)
                if st.form_submit_button("この金額で設定する", use_container_width=True):
                    st.session_state[f"{prefix}monthly_allowance"] = new_allowance
                    save_all_data()  # 全データを保存
                    st.success(f"今月のお小遣いを {new_allowance:,.0f} 円に設定しました！")
                    st.balloons()
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
        st.markdown(f"<p style='text-align: center; font-size: 2.5em; font-weight: bold;'>{format_balance_display(remaining_balance)}</p>", 
                   unsafe_allow_html=True)
        if current_allowance > 0:
            progress_ratio = min(current_spent / current_allowance, 1.0)
            st.progress(progress_ratio)
            st.caption(f"予算使用率: {progress_ratio * 100:.1f}%")
        
        st.divider()
        st.subheader("📸 レシートを登録する")
        uploaded_file = st.file_uploader("📁 レシート画像をアップロード", type=['png', 'jpg', 'jpeg'], 
                                       key=f"{prefix}uploader")
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
                        st.session_state[f"{prefix}receipt_preview"] = {
                            "total_amount": float(extracted_data.get("total_amount", 0)), 
                            "items": extracted_data.get("items", [])
                        }
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 解析エラー: {e}")
                        if 'gemini_response' in locals(): 
                            st.code(gemini_response.text, language="text")
        
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
