import streamlit as st
import sys
import os

st.set_page_config(layout="wide")
st.title("🕵️ 英雄（ツール）個別召喚テスト")
st.info("どのツールファイルの読み込みでエラーが起きるかを特定します。")

# --- 現在のPythonがモジュールを探しに行く場所の一覧を表示 ---
st.header("Pythonの探索パス（sys.path）")
st.write(sys.path)
st.caption("このリストのどこかに、`/mount/src/test` のような、プロジェクトのルートフォルダが含まれているはずです。")


st.header("英雄たちの個別召喚結果")

# 召喚リスト
heroes = [
    "translator_tool",
    "okozukai_recorder_tool",
    "calendar_tool",
    "gijiroku_tool",
    "kensha_no_kioku_tool",
    "ai_memory_partner_tool"
]

has_error = False

# 一人ずつ召喚を試みる
for hero in heroes:
    st.subheader(f"召喚テスト：`{hero}`")
    try:
        # この書き方で、動的にインポートを試みます
        __import__(f"tools.{hero}")
        st.success(f"✅ 英雄 **`{hero}`** の召喚に成功しました。")
    except Exception as e:
        st.error(f"❌ 英雄 **`{hero}`** の召喚に失敗しました！これがエラーの直接の原因です。")
        st.exception(e) # エラーの詳細を表示
        has_error = True

st.divider()

if has_error:
    st.error("上記で失敗したファイルに、何らかの問題（ファイルの破損、構文エラー、あるいはそのファイル内での別のImportErrorなど）が潜んでいます。")
else:
    st.success("🎉 すべての英雄の召喚に成功しました！もしこれでも元のアプリでエラーが出る場合、キャッシュなど環境側の問題が強く疑われます。")
