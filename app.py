import streamlit as st
import os

st.title("🕵️ 環境診断レポート")

st.info(
    "このアプリは、実行されている環境にどんなファイルやフォルダが見えているかを確認するためのものです。"
)

# --- 現在の作業フォルダを表示 ---
try:
    current_directory = os.getcwd()
    st.header("1. 私が今いる場所（カレントディレクトリ）")
    st.code(current_directory, language="bash")
except Exception as e:
    st.error(f"現在地の取得中にエラーが発生しました: {e}")

# --- カレントディレクトリのファイルとフォルダを一覧表示 ---
try:
    st.header("2. 私のすぐ周りにあるファイルとフォルダ")
    files_and_folders = os.listdir(".") # "." はカレントディレクトリを意味します
    st.write(files_and_folders)

    # "tools" フォルダが一覧にあれば、成功の印
    if "tools" in files_and_folders:
        st.success("✅ 「tools」フォルダが見つかりました！")
    else:
        st.error("❌ 致命的な問題：「tools」フォルダが見つかりません。これがエラーの根本原因です。")

except Exception as e:
    st.error(f"周囲のファイル確認中にエラーが発生しました: {e}")


# --- "tools" フォルダの中身を一覧表示 ---
try:
    st.header("3. 「tools」フォルダの中身")
    # "tools" フォルダへのパスを指定
    tools_path = "./tools" 
    
    # そもそも "tools" フォルダが存在するかチェック
    if os.path.isdir(tools_path):
        tools_contents = os.listdir(tools_path)
        st.write(tools_contents)
        
        # __init__.py の存在チェック
        if "__init__.py" in tools_contents:
            st.success("✅ 「__init__.py」が見つかりました！パッケージとして認識できるはずです。")
        else:
            st.error("❌ 致命的な問題：「__init__.py」が見つかりません。これが原因でインポートに失敗しています。")
            
        # ai_memory_partner_tool.py の存在チェック
        if "ai_memory_partner_tool.py" in tools_contents:
            st.success("✅ 「ai_memory_partner_tool.py」も見つかりました。")
        else:
            st.warning("⚠️ 「ai_memory_partner_tool.py」が見つかりません。")

    else:
        st.error("❌ 「tools」という名前のフォルダ自体が存在しないため、中身を確認できません。")

except Exception as e:
    st.error(f"「tools」フォルダの中身を確認中にエラーが発生しました: {e}")

st.divider()
st.warning("この診断結果のスクリーンショットをAIに見せると、問題解決が早まる可能性があります。")
