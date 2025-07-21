import streamlit as st
from st_audiorec import st_audiorec

# --- アプリの基本設定 ---
st.set_page_config(
    page_title="音声録音テスト",
    page_icon="🎤"
)

# --- メイン画面 ---
st.title("🎤 音声録音テスト（PoC）")
st.write("---")
st.write("""
このアプリは、「トランシーバー型・音声翻訳アプリ」が実現可能かを検証するためのテスト（PoC: Proof of Concept）です。

**【検証内容】**
以下のマイクボタンを使い、音声の録音と再生が正常に完了するかを確認します。

**【操作方法】**
1. **マイクアイコンのボタンを1回クリック**すると、録音が開始されます。（ブラウザからマイクの使用許可を求められます）
2. 話したい内容を録音してください。
3. **停止アイコンの四角いボタンを1回クリック**すると、録音が停止されます。
4. 録音が完了すると、下にオーディオプレーヤーが表示されます。
5. 再生ボタンを押して、録音した音声が聞こえるかを確認してください。

この一連の動作が問題なく行えれば、私たちのプロジェクトの最大のリスクは解消されます。
""")

# 音声録音ウィジェットを配置
wav_audio_data = st_audiorec()

# 録音されたデータがある場合
if wav_audio_data is not None:
    st.write("---")
    st.success("🎉 録音が完了しました！")
    st.write("以下のプレーヤーで、録音した音声を確認できます。")
    
    # st.audioを使って、録音された音声データを再生する
    st.audio(wav_audio_data, format='audio/wav')
    
    # （オプション）ダウンロードリンクを表示
    st.download_button(
        label="録音データをダウンロード",
        data=wav_audio_data,
        file_name="recorded_audio.wav",
        mime="audio/wav"
    )
