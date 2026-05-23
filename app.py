import streamlit as st
import pandas as pd
 
# ==== 設定 ============================================
 
# Excel ファイルのパス
EXCEL_PATH = "資格報奨金_まとめ.xlsx"
 
# ログイン用パスワード（必ず自分用に変更）
PASSWORD = "SIyu0207ike&"   # 元コードと同じ値にしてください
 
# =====================================================
 
 
def parse_money_to_man(yen_str: str) -> int:
    """
    '100万円' や '1万円' などから 数字部分だけを取り出して int 化
    （現状では未使用ですが、今後金額計算に使う想定の関数）
    """
    s = str(yen_str)
    s = s.replace("万円", "").replace("万", "").replace("円", "").replace(",", "")
    if s == "" or s.lower() == "nan":
        return 0
    return int(s)
 
 
def load_data():
    """
    Excel からデータを読み込んで、必要な列を整形して返す
    - Flask 版の load_data() に相当
    """
    df = pd.read_excel(EXCEL_PATH)
 
    # Excel の列名を Python で使う列名にそろえる（Flask 版と同じ）
    df = df.rename(columns={
        "資格名／種類": "資格名",  # 必要に応じてここを調整
        # 他にも列名が微妙に違う場合はここに追加
        # 例: "金額（円）": "金額"
    })
 
    # 行番号を ID として振る（Flask 版では enumerate の idx を ID にしていた）
    df = df.reset_index(drop=True)
    df["id"] = df.index
 
    # ランク一覧
    rank_list = sorted(df["ランク"].dropna().unique())
    # 区分一覧
    kubun_list = sorted(df["区分"].dropna().unique())
 
    return df, rank_list, kubun_list
 
 
# ====== Streamlit セッション状態の初期化 =========================
 
if "authenticated" not in st.session_state:
    # パスワード認証済みかどうか
    st.session_state.authenticated = False
 
if "acquired_ids" not in st.session_state:
    # 取得済み資格の ID セット
    st.session_state.acquired_ids = set()
 
if "superior_ids" not in st.session_state:
    # 「上位互換を取得済み」とマークされた資格の ID セット
    st.session_state.superior_ids = set()
 
 
def reset_login_state(clear_data: bool = False):
    """
    ログアウト時に状態をリセットするヘルパ
    clear_data=True の場合は取得状況も消す
    """
    st.session_state.authenticated = False
    if clear_data:
        st.session_state.acquired_ids = set()
        st.session_state.superior_ids = set()
 
 
# ====== 画面構成 ==========================================
 
st.set_page_config(page_title="資格報奨金 管理アプリ", page_icon="✅", layout="wide")
st.title("資格報奨金 管理アプリ（Streamlit 版）")
 
# ---- まだログインしていない場合は、パスワード画面だけを表示 ----
if not st.session_state.authenticated:
    st.markdown("### ログイン")
    st.write("パスワードを入力してください。")
    password_input = st.text_input("パスワード", type="password")
 
    col_login1, col_login2 = st.columns([1, 3])
    with col_login1:
        if st.button("ログイン"):
            if password_input == PASSWORD:
                st.session_state.authenticated = True
                st.success("ログインに成功しました。")
                st.rerun()  # 画面を再描画してメインUIを表示
            else:
                st.session_state.authenticated = False
                st.error("パスワードが違います。")
 
    # ログインしていない間はここで処理終了
    st.stop()
 
# ---- ここから下は「ログイン後のみ」表示される ----
 
# ログアウトと取得状況リセットボタン
top_col1, top_col2, top_col3 = st.columns([1, 1, 6])
with top_col1:
    if st.button("ログアウト"):
        reset_login_state(clear_data=False)  # 取得状況は残す
        st.rerun()
with top_col2:
    if st.button("取得状況をリセット"):
        st.session_state.acquired_ids = set()
        st.session_state.superior_ids = set()
        st.success("取得状況をリセットしました。")
with top_col3:
    st.write("")  # 余白
 
st.markdown("---")
 
# ---- データ読み込み ----
try:
    df, rank_list, kubun_list = load_data()
except FileNotFoundError:
    st.error(f"Excel ファイルが見つかりませんでした: {EXCEL_PATH}")
    st.stop()
 
acquired_ids = st.session_state.acquired_ids
superior_ids = st.session_state.superior_ids
 
# ---- データの仕分け（Flask 版の login() でやっていた部分） ----
records = df.to_dict(orient="records")
 
remaining_records = []  # 未取得
acquired_records = []   # 取得済み（上位互換はまだ）
superior_records = []   # 上位互換を取得済み
 
for rec in records:
    idx = rec["id"]
    if idx in acquired_ids:
        if idx in superior_ids:
            superior_records.append(rec)
        else:
            acquired_records.append(rec)
    else:
        remaining_records.append(rec)
 
 
# ---- フィルタ・検索（サイドバー） ----
 
st.sidebar.header("検索・フィルタ")
 
# 見出しと余白で少し見やすくする
st.sidebar.subheader("基本条件")
selected_ranks = st.sidebar.multiselect(
    "ランクで絞り込み",
    options=rank_list,
    default=rank_list,
)
st.sidebar.write("")  # 余白
 
selected_kubun = st.sidebar.multiselect(
    "区分で絞り込み",
    options=kubun_list,
    default=kubun_list,
)
st.sidebar.markdown("---")
 
st.sidebar.subheader("フリーワード検索")
keyword = st.sidebar.text_input(
    "資格名・ランク・区分・金額 などを横断検索",
    value="",
    placeholder="例）IT パスポート, 技術士, Aランク など"
)
st.sidebar.caption("※ 大文字／小文字は区別しません。部分一致です。")
 
st.sidebar.markdown("---")
st.sidebar.caption("条件を変更すると自動で絞り込みが反映されます。")
 
 
def match_freeword(rec: dict, keyword: str) -> bool:
    """
    フリーワード検索用:
    資格名 / ランク / 区分 / 金額 などをまとめて文字列にし、
    keyword が含まれるかどうかを判定する
    """
    if not keyword:
        return True
 
    k = keyword.lower()
    # 検索対象にするカラムを必要に応じて増減してください
    fields = [
        str(rec.get("資格名", "")),
        str(rec.get("ランク", "")),
        str(rec.get("区分", "")),
        str(rec.get("金額", "")),
    ]
    text = " ".join(fields).lower()
    return k in text
 
 
def filter_records(rec_list):
    """
    ランク・区分・フリーワードでフィルタする共通関数
    """
    filtered = []
    for r in rec_list:
        if r.get("ランク") not in selected_ranks:
            continue
        if r.get("区分") not in selected_kubun:
            continue
        if not match_freeword(r, keyword):
            continue
        filtered.append(r)
    return filtered
 
 
remaining_records_filtered = filter_records(remaining_records)
acquired_records_filtered = filter_records(acquired_records)
superior_records_filtered = filter_records(superior_records)
 
# =========================================================
#  未取得の資格
# =========================================================
st.subheader("未取得の資格")
 
if not remaining_records_filtered:
    st.info("条件に合致する未取得の資格はありません。")
else:
    for rec in remaining_records_filtered:
        idx = rec["id"]
        qual_name = rec.get("資格名", "")
        rank = rec.get("ランク", "")
        kubun = rec.get("区分", "")
        money = rec.get("金額", "")
 
        # 表示行
        # col2: 「取得」ボタン（= 取得済みタブに移動）
        # col3: 「上位互換を取得」ボタン（= 上位互換を取得済みタブに移動）
        row_col1, row_col2, row_col3 = st.columns([4, 1, 1])
        with row_col1:
            st.markdown(
                f"**{qual_name}**  "
                f"(ランク: {rank}, 区分: {kubun}, 金額: {money})"
            )
        with row_col2:
            if st.button("取得", key=f"acquire_{idx}"):
                # 取得済みにする（上位互換フラグは外す）
                acquired_ids.add(idx)
                if idx in superior_ids:
                    superior_ids.discard(idx)
                st.session_state.acquired_ids = acquired_ids
                st.session_state.superior_ids = superior_ids
                st.rerun()
        with row_col3:
            if st.button("上位互換を取得", key=f"acquire_superior_{idx}"):
                # 直接「上位互換を取得済み」にする
                acquired_ids.add(idx)
                superior_ids.add(idx)
                st.session_state.acquired_ids = acquired_ids
                st.session_state.superior_ids = superior_ids
                st.rerun()
 
# 少し余白
st.markdown("")
 
# =========================================================
#  取得済み（上位互換はまだ）
# =========================================================
st.subheader("取得済み（上位互換はまだ）の資格")
 
if not acquired_records_filtered:
    st.info("条件に合致する『取得済み（上位互換はまだ）』の資格はありません。")
else:
    for rec in acquired_records_filtered:
        idx = rec["id"]
        qual_name = rec.get("資格名", "")
        rank = rec.get("ランク", "")
        kubun = rec.get("区分", "")
        money = rec.get("金額", "")
 
        row_col1, row_col2, row_col3 = st.columns([4, 1, 2])
        with row_col1:
            st.markdown(
                f"**{qual_name}**  "
                f"(ランク: {rank}, 区分: {kubun}, 金額: {money})"
            )
        with row_col2:
            if st.button("取得解除", key=f"unacquire_{idx}"):
                # acquired_ids / superior_ids から削除
                if idx in acquired_ids:
                    acquired_ids.remove(idx)
                if idx in superior_ids:
                    superior_ids.remove(idx)
                st.session_state.acquired_ids = acquired_ids
                st.session_state.superior_ids = superior_ids
                st.rerun()
        with row_col3:
            if st.button("上位互換取得済みにする", key=f"set_superior_{idx}"):
                # acquired_ids / superior_ids に追加
                acquired_ids.add(idx)
                superior_ids.add(idx)
                st.session_state.acquired_ids = acquired_ids
                st.session_state.superior_ids = superior_ids
                st.rerun()
 
st.markdown("")
 
# =========================================================
#  上位互換を取得済みの資格
# =========================================================
st.subheader("上位互換を取得済みの資格")
 
if not superior_records_filtered:
    st.info("条件に合致する『上位互換を取得済み』の資格はありません。")
else:
    for rec in superior_records_filtered:
        idx = rec["id"]
        qual_name = rec.get("資格名", "")
        rank = rec.get("ランク", "")
        kubun = rec.get("区分", "")
        money = rec.get("金額", "")
 
        row_col1, row_col2 = st.columns([4, 2])
        with row_col1:
            st.markdown(
                f"**{qual_name}**  "
                f"(ランク: {rank}, 区分: {kubun}, 金額: {money})"
            )
        with row_col2:
            if st.button("上位互換フラグ解除", key=f"unset_superior_{idx}"):
                if idx in superior_ids:
                    superior_ids.remove(idx)
                st.session_state.superior_ids = superior_ids
                st.rerun()
