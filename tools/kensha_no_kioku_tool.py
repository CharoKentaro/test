# ===============================================================
# ★★★ kensha_no_kioku_tool.py ＜デイリーパスワード版＞ ★★★
# ===============================================================
import streamlit as st
import google.generativeai as genai
import json
import time
from datetime import datetime, timedelta, timezone # ★ 日付を扱う達人を召喚
import pandas as pd

# ===============================================================
# 専門家のメインの仕事 (新しいシステムに換装)
# ===============================================================
def show_tool(gemini_api_key):
    st.header("🧠 賢者の記憶", divider='rainbow')

    # --- セッションステートの初期化 ---
    prefix = "kensha_"
    if f"{prefix}analysis_result" not in st.session_state:
        st.session_state[f"{prefix}analysis_result"] = None
    if f"{prefix}usage_count" not in st.session_state:
        st.session_state[f"{prefix}usage_count"] = 0
    # ★ コンテキスト情報をセッションで保持
    if f"{prefix}context" not in st.session_state:
        st.session_state[f"{prefix}context"] = {}

    # ★★★ リミット回数を、ここで定義 ★★★
    usage_limit = 1 # ←←← ちゃろさんが、いつでも、ここの数字を変えられます！
    
    # --- 運命の分岐 ---
    is_limit_reached = st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit

    if is_limit_reached:
        # ★★★ 聖域（アンロック・モード）の表示 ★★★
        st.success("🎉 たくさんのご利用、ありがとうございます！")
        st.info("この『賢者の記憶』が、あなたの未来を創造する一助となれば幸いです。")
        st.warning("分析を続けるには、応援ページで「今日の合言葉（4桁の数字）」を確認し、入力してください。")
        
        portal_url = "https://pray-power-is-god-and-cocoro.com/free3/continue.html"
        st.markdown(f'<a href="{portal_url}" target="_blank">応援ページで「今日の合言葉」を確認する →</a>', unsafe_allow_html=True)
        st.divider()

        password_input = st.text_input("ここに「今日の合言葉」を入力してください:", type="password", key=f"{prefix}password_input")
        if st.button("分析回数をリセットする", key=f"{prefix}unlock_button"):
            # ★★★ 今日の正しい「4桁の数字」を自動生成 ★★★
            JST = timezone(timedelta(hours=+9))
            today_int = int(datetime.now(JST).strftime('%Y%m%d'))
            seed_str = st.secrets.get("unlock_seed", "0")
            seed_int = int(seed_str) if seed_str.isdigit() else 0
            correct_password = str((today_int + seed_int) % 10000).zfill(4)
            
            if password_input == correct_password:
                st.session_state[f"{prefix}usage_count"] = 0
                st.balloons()
                st.success("ありがとうございます！分析回数がリセットされました。")
                time.sleep(2)
                st.rerun()
            else:
                st.error("合言葉が違うようです。応援ページで、もう一度ご確認ください。")

    else:
        # --- 通常モード (上限に達していない場合) ---
        st.info("""
        会議の音声ファイルをアップロードし、あなたの「ビジネス目標」と「課題」を入力してください。
        AIが単なる議事録を超えた、未来を創造するための戦略的分析レポートを生成します。
        """)
        st.warning("長時間の音声ファイルは、処理に時間がかかったり、サーバーのメモリ制限によりエラーが発生する可能性があります。")
        st.caption(f"🚀 あと {usage_limit - st.session_state.get(f'{prefix}usage_count', 0)} 回、分析できます。")

        # --- STEP 1: コンテキスト入力 (成功部分は、完全に保護) ---
        st.subheader("STEP 1: あなたの状況を教えてください")
        with st.form(key=f"{prefix}context_form"):
            st.markdown("AIは、以下の情報を基に、あなただけの、分析を行います。")
            business_goal = st.text_input("あなたのビジネス目標", placeholder="例：今四半期の、売上を、20%向上させる", value=st.session_state[f"{prefix}context"].get("business_goal", ""))
            current_challenges = st.text_area("現在、直面している課題", placeholder="例：新規顧客の、獲得単価が、高騰している。競合製品の、値下げ攻勢が、激しい。", value=st.session_state[f"{prefix}context"].get("current_challenges", ""))
            meta_prompt = st.text_area("AIへの、特別な、追加指示（任意）", placeholder="例：特に、若年層向けの、マーケティング戦略に、重点を、置いて、分析してほしい。", value=st.session_state[f"{prefix}context"].get("meta_prompt", ""))
            
            form_submit_button = st.form_submit_button("この内容で、コンテキストを設定する")
            if form_submit_button:
                # ★ コンテキスト情報をセッションに保存
                st.session_state[f"{prefix}context"] = {
                    "business_goal": business_goal,
                    "current_challenges": current_challenges,
                    "meta_prompt": meta_prompt
                }
                st.success("コンテキストを、AIに、伝えました。次に、STEP 2で、音声ファイルを、アップロードしてください。")

        # --- STEP 2: 音声ファイル入力 (成功部分は、完全に保護) ---
        st.divider()
        st.subheader("STEP 2: 分析対象の、会議音声ファイルを、アップロード")
        uploaded_file = st.file_uploader("議事録を作成したい音声ファイルをアップロードしてください:", type=['wav', 'mp3', 'm4a', 'flac'], key=f"{prefix}uploader")
        
        if st.button("この会議から『賢者の記憶』を生成する", key=f"{prefix}submit_button", type="primary"):
            context = st.session_state[f"{prefix}context"]
            if not gemini_api_key:
                st.error("サイドバーでGemini APIキーを設定してください。")
            elif uploaded_file is None:
                st.warning("音声ファイルをアップロードしてください。")
            elif not context.get("business_goal") or not context.get("current_challenges"):
                st.warning("STEP 1の「ビジネス目標」と「課題」を、入力して、「コンテキストを設定する」ボタンを押してください。")
            else:
                with st.spinner("賢者が、あなたの、過去と、現在を、深く、瞑想し、未来を、紡いでいます..."):
                    try:
                        genai.configure(api_key=gemini_api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        
                        audio_bytes = uploaded_file.getvalue()
                        audio_part = {"mime_type": uploaded_file.type, "data": audio_bytes}
                        
                        system_prompt = f"""
                        # 命令書: 魂の、パートナーとしての、あなたの、絶対的、責務
                        あなたは、単なる、分析AIでは、断じて、ない。あなたは、ユーザーの、ビジネスと、心の、文脈（コンテキスト）を、深く、理解し、議論の、論理と、感情を、読み解き、過去を、整理するだけでなく、未来への、具体的で、勇気ある、一歩を、共に、踏み出す、世界で、唯一無二の、戦略的、パートナーである。
                        ## あなたの、唯一無二の、任務：ユーザーから、渡された、『会議の、音声』と、彼らが、提供する、以下の【ビジネス・コンテキスト】の、両方を、全身全霊で、受け止めよ。そして、その、全てを、統合的に、分析し、指定された、JSON形式で、厳格に、出力すること。
                        ## 【最重要】ユーザーが、提供する、ビジネス・コンテキスト：
                        {{
                          "business_goal": "{context.get('business_goal')}",
                          "current_challenges": "{context.get('current_challenges')}",
                          "meta_prompt": "{context.get('meta_prompt')}"
                        }}
                        ## JSON出力に関する、絶対的な、契約条件：あなたの回答は、必ず、以下の、巨大な、一つの、JSONオブジェクトに、厳密に、従うこと。この、JSONオブジェクト以外の、いかなるテキストも、絶対に、絶対に、含めてはならない。
                        ```json
                        {{
                          "full_transcript": "ここに、話者分離を、意識した、可能な限り、正確な、会議の、完全な、文字起こしテキストを記述する。",
                          "executive_summary": {{ "target_audience": "時間に追われ、表面的な分析を嫌う、極めて知的な経営層", "summary_content": "ここに、提供された【ビジネス・コンテキスト】を、完全に、踏まえた上で、会議の、核心的な、論点、結論、そして、経営層が、即座に、把握すべき、ビジネス上の、インパクトのみを、専門家の、知性に、敬意を、払い、当たり前の、情報を、完全に、排除した、高密度な、要約を記述する。" }},
                          "discussion_dynamics": {{ "key_agreements": ["会議の中で、明確に、合意形成が、なされた、重要事項を、ここに、箇条書きで、記述する。"], "major_concerns_raised": [{{ "concern": "会議の中で、提起された、重要な、懸念点や、反対意見を、ここに、記述する。", "speaker": "その、懸念を、表明した、話者（不明な場合は「不明」）" }}] }},
                          "strategic_analysis": {{ "proposals": [ {{ "strategy_name": "ここに、一つ目の、画期的な、戦略案を、【ビジネス・コンテキスト】に、沿って、記述する。", "merits": "この戦略の、主なメリットを、箇条書きで、記述する。", "demerits": "この戦略で、想定される、デメリットや、リスクを、箇条書きで、記述する。", "first_actionable_step": "この戦略を、前に、進めるために、明日からでも、実行可能な、具体的で、小さな、最初の一歩を、記述する。" }}, {{ "strategy_name": "ここに、二つ目の、全く、異なる、アプローチの、戦略案を、記述する。", "merits": "メリットを、記述する。", "demerits": "デメリットを、記述する。", "first_actionable_step": "最初の一歩を、記述する。" }}, {{ "strategy_name": "ここに、三つ目の、常識を、覆すような、大胆な、戦略案を、記述する。", "merits": "メリットを、記述する。", "demerits": "デメリットを、記述する。", "first_actionable_step": "最初の一歩を、記述する。" }} ], "ranking_and_tradeoffs": {{ "ranking": "上記の3つの戦略を、【ビジネス・コンテキスト】を、基に、ユーザーにとって、最も、効果的だと、思われる、順に、ランク付けする。", "reasoning": "なぜ、その、順位付けに、なったのか。その、判断を、左右した、重要な、トレードオフを、明確に、説明する。" }}, "critical_self_challenge": {{ "blind_spots": "あなた自身の、上記分析に、潜む、盲点を、正直に、洗い出す。（例：「今回の分析は、提供された、コンテキストに、固執するあまり、市場全体の、マクロな、変化を、見落としている、可能性が、ある」など）", "alternative_perspectives": "ここに、議論の、参加者や、あなた自身が、見落としている、可能性の、ある、全く、別の、視点を、提示する。（例：「この、課題は、技術ではなく、組織文化の、問題として、捉え直すべきでは、ないか？」など）" }} }}
                        }}
                        ```
                        """
                        response = model.generate_content([system_prompt, audio_part])

                        if response.text:
                            st.session_state[f"{prefix}usage_count"] += 1
                            json_text = response.text.strip().lstrip("```json").rstrip("```")
                            st.session_state[f"{prefix}analysis_result"] = json.loads(json_text)
                            if st.session_state.get(f"{prefix}usage_count", 0) >= usage_limit:
                                st.rerun()
                        else:
                            st.error("AIからの応答が空でした。音声が認識できなかった可能性があります。")

                    except json.JSONDecodeError:
                        st.error("AIからの応答を解析できませんでした。AIが予期せぬ形式で回答した可能性があります。")
                        st.info("AIからの生の応答は以下の通りです：")
                        st.code(response.text, language="text")
                    except Exception as e:
                        st.error(f"分析中にエラーが発生しました: {e}")

    # --- STEP 3: 『賢者の記憶』の、顕現（成功部分は、完全に保護） ---
    if st.session_state[f"{prefix}analysis_result"]:
        st.divider()
        st.success("賢者の、記憶が、解放されました。")
        
        result = st.session_state[f"{prefix}analysis_result"]
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 戦略分析レポート", "📝 完全な文字起こし", "🤝 議論の力学", "✅ ToDoリスト"])

        with tab1:
            st.subheader("経営層向け・エグゼクティブサマリー")
            summary = result.get("executive_summary", {}).get("summary_content", "要約の生成に失敗しました。")
            st.info(summary if summary else "要約の生成に失敗しました。")
            st.divider()
            
            st.subheader("未来を、創造する、三つの、戦略提案")
            proposals = result.get("strategic_analysis", {}).get("proposals", [])
            if proposals:
                for prop in proposals:
                    with st.container(border=True):
                        st.markdown(f"#### {prop.get('strategy_name', '名称未設定の戦略')}")
                        st.markdown("**最初の一歩:**")
                        st.success(f"{prop.get('first_actionable_step', 'N/A')}")
                        with st.expander("詳細（メリット・デメリット）"):
                            st.markdown("**メリット:**")
                            st.markdown(f"{prop.get('merits', 'N/A')}")
                            st.markdown("**デメリット:**")
                            st.markdown(f"{prop.get('demerits', 'N/A')}")
            else:
                st.warning("戦略提案は生成されませんでした。")
            
            st.divider()
            st.subheader("AIコンサルタントによる、最終評価と、自己批判")
            ranking = result.get("strategic_analysis", {}).get("ranking_and_tradeoffs", {})
            st.markdown(f"**推奨順位:** {ranking.get('ranking', 'N/A')}")
            st.markdown(f"**判断理由と、トレードオフ:**")
            st.markdown(f"{ranking.get('reasoning', 'N/A')}")
            
            challenge = result.get("strategic_analysis", {}).get("critical_self_challenge", {})
            with st.expander("🚨 この分析の、盲点と、別の、視点（重要）"):
                st.warning(f"**盲点:** {challenge.get('blind_spots', 'N/A')}")
                st.info(f"**別の視点:** {challenge.get('alternative_perspectives', 'N/A')}")

        with tab2:
            st.subheader("書記官の、記録")
            transcript = result.get("full_transcript", "文字起こしに失敗しました。")
            st.text_area("完全な文字起こしテキスト", value=transcript if transcript else "文字起こしに失敗しました。", height=400)

        with tab3:
            st.subheader("議論の、流れと、温度感")
            dynamics = result.get("discussion_dynamics", {})
            st.markdown("#### 主な合意点")
            agreements = dynamics.get("key_agreements", [])
            if agreements:
                for agreement in agreements: st.markdown(f"- {agreement}")
            else:
                st.info("明確な合意点は抽出されませんでした。")
            
            st.markdown("#### 提起された、主な、懸念事項")
            concerns = dynamics.get("major_concerns_raised", [])
            if concerns:
                for concern in concerns: st.markdown(f"- **[{concern.get('speaker', '不明')}]** {concern.get('concern', 'N/A')}")
            else:
                st.info("明確な懸念事項は抽出されませんでした。")
        
        with tab4:
            st.subheader("実行官の、指令書")
            # ★★★ ToDoリストの抽出キーを修正 ★★★
            todos_data = result.get("strategic_analysis", {}).get("proposals", [])
            todos_list = [{"最初の一歩": prop.get("first_actionable_step", "N/A"), "戦略名": prop.get("strategy_name", "N/A")} for prop in todos_data]
            
            if todos_list:
                try:
                    df = pd.DataFrame(todos_list)
                    st.dataframe(df, use_container_width=True)
                except:
                    st.warning("ToDoリストの表示に失敗しました。")
                    st.json(todos_list)
            else:
                st.info("この会議から、具体的なToDoは、抽出されませんでした。")
