import streamlit as st
import pandas as pd

# ==== 設定 ============================================
EXCEL_PATH = "資格報奨金_まとめ.xlsx"
PASSWORD = "SIyu0207ike&"
# =====================================================


def parse_money_to_man(yen_str: str) -> int:
    s = str(yen_str)
    s = s.replace("万円", "").replace("万", "").replace("円", "").replace(",", "")
    if s == "" or s.lower() == "nan":
        return 0
    return int(s)


def load_data():
    df = pd.read_excel(EXCEL_PATH)
    df = df.rename(columns={
        "資格名／種類": "資格名",
    })
    df = df.reset_index(drop=True)
    df["id"] = df.index

    rank_list = sorted(df["ランク"].dropna().unique())
    kubun_list = sorted(df["区分"].dropna().unique())
    return df, rank_list, kubun_list


# ====== セッション状態初期化 =========================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "acquired_ids" not in st.session_state:
    st.session_state.acquired_ids = set()

if "superior_ids" not in st.session_state:
    st.session_state.superior_ids = set()

# タブ表示オン/オフ用チェックボックス状態（デフォルトはすべて表示）
if "show_unacquired" not in st.session_state:
    st.session_state.show_unacquired = True
if "show_acquired" not in st.session_state:
    st.session_state.show_acquired = True
if "show_superior" not in st.session_state:
    st.session_state.show_superior = True

# 絞り込み条件（ボタン押下で確定する用）
if "applied_keyword" not in st.session_state:
    st.session_state.applied_keyword = ""
if "applied_ranks" not in st.session_state:
    st.session_state.applied_ranks = []
if "applied_kubun" not in st.session_state:
    st.session_state.applied_kubun = []


def reset_login_state(clear_data: bool = False):
    st.session_state.authenticated = False
    if clear_data:
        st.session_state.acquired_ids = set()
        st.session_state.superior_ids = set()


# ====== ページ設定 ====================================
st.set_page_config(
    page_title="資格報奨金 管理アプリ",
    page_icon="✅",
    layout="centered",
)

# ====== 全体 CSS ======================================
st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        font-size: 16px;
    }

    /* 1枚のカード全体の見た目（資格情報の枠） */
    .qual-card-wrapper {
        padding: 0.45rem 0.6rem 0.4rem;
        margin-bottom: 0.45rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        background-color: #ffffff;
    }

    /* 資格名の黒太枠 */
    .qual-name-box {
        border: 2px solid #000000;
        border-radius: 0.35rem;
        padding: 0.25rem 0.5rem;
        margin-bottom: 0.35rem;
        display: inline-block;
    }
    .qual-name-text {
        font-weight: 800;
        font-size: 1.05rem;
    }

    .qual-meta {
        font-size: 0.9rem;
        line-height: 1.4;
        margin-bottom: 0.2rem;
    }

    /* カード下部のボタン行：テキストとボタンの間隔を少しだけ */
    .qual-card-btn-row {
        margin-top: 0.3rem;
        margin-bottom: 0.1rem;
    }

    /* ▼ ボタンのデザイン（かなり薄い青 + さらに小さめサイズ＆同じ大きさ） */
    .stButton > button {
        white-space: nowrap;
        font-size: 0.55rem;          /* 文字さらに小さめ */
        padding: 0.1rem 0.25rem;     /* 余白さらに少なめ */
        background-color: #e8f4ff;   /* かなり薄い青 */
        color: #0d47a1;
        border: 1px solid #bcdfff;
        border-radius: 0.25rem;
        width: 100%;                 /* カラム／コンテナの幅いっぱいに */
        min-width: 0;
        min-height: 1.4rem;          /* 高さをそろえるための下限値 */
        box-sizing: border-box;
        display: block;
    }
    .stButton > button:hover {
        background-color: #d7ecff;   /* 少し濃く */
        color: #0d47a1;
        border-color: #99cdff;
    }

    h2, h3 {
        margin-top: 0.8rem;
        margin-bottom: 0.4rem;
    }
    section[data-testid="stSidebar"] {
        font-size: 14px;
    }

    .tab-toggle-label {
        font-size: 0.8rem;
        color: #555555;
        margin-bottom: 0.1rem;
    }

    .card-root {
        padding: 0;
        margin: 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ====== タイトル ======================================
st.markdown(
    "<h1>資格報奨金 管理アプリ（Streamlit 版）</h1>",
    unsafe_allow_html=True
)

# ==== タブ表示オン/オフ用チェックボックス ====
if st.session_state.authenticated:
    st.markdown('<div class="tab-toggle-label">表示するタブを選択：</div>', unsafe_allow_html=True)
    tab_col1, tab_col2, tab_col3 = st.columns(3)
    with tab_col1:
        st.session_state.show_unacquired = st.checkbox(
            "未取得",
            value=st.session_state.show_unacquired,
            key="chk_unacquired"
        )
    with tab_col2:
        st.session_state.show_acquired = st.checkbox(
            "取得済み",
            value=st.session_state.show_acquired,
            key="chk_acquired"
        )
    with tab_col3:
        st.session_state.show_superior = st.checkbox(
            "上位互換済み",
            value=st.session_state.show_superior,
            key="chk_superior"
        )

# ---- ログイン画面 ----
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
                st.rerun()
            else:
                st.session_state.authenticated = False
                st.error("パスワードが違います。")

    st.stop()

st.markdown("---")

# ---- データ読込 ----
try:
    df, rank_list, kubun_list = load_data()
except FileNotFoundError:
    st.error(f"Excel ファイルが見つかりませんでした: {EXCEL_PATH}")
    st.stop()

acquired_ids = st.session_state.acquired_ids
superior_ids = st.session_state.superior_ids

records = df.to_dict(orient="records")
remaining_records = []
acquired_records = []
superior_records = []

for rec in records:
    idx = rec["id"]
    if idx in acquired_ids:
        if idx in superior_ids:
            superior_records.append(rec)
        else:
            acquired_records.append(rec)
    else:
        remaining_records.append(rec)

# ---- サイドバー（検索UI + 絞り込みボタン + ログアウト） ----
st.sidebar.header("検索・フィルタ")

# ① フリーワード
st.sidebar.subheader("フリーワード検索")
keyword_input = st.sidebar.text_input(
    "キーワード",
    value=st.session_state.applied_keyword,
    placeholder="例）IT パスポート, 技術士 など",
    key="kw_input"
)
st.sidebar.caption("※ 資格名・ランク・区分・金額から部分一致で検索します。")

st.sidebar.markdown("---")

# ② ランク／区分（複数選択・未選択なら全件）
st.sidebar.subheader("詳細条件")

selected_ranks_input = st.sidebar.multiselect(
    "ランクを選択（複数可・未選択なら全件）",
    options=rank_list,
    default=st.session_state.applied_ranks,
    key="rank_multi",
)

selected_kubun_input = st.sidebar.multiselect(
    "区分を選択（複数可・未選択なら全件）",
    options=kubun_list,
    default=st.session_state.applied_kubun,
    key="kubun_multi",
)

# === 絞り込みボタン & 絞り込み解除ボタン ===
btn_col1, btn_col2 = st.sidebar.columns(2)
with btn_col1:
    if st.button("絞り込み", key="do_filter_sidebar"):
        st.session_state.applied_keyword = st.session_state.kw_input
        st.session_state.applied_ranks = st.session_state.rank_multi
        st.session_state.applied_kubun = st.session_state.kubun_multi
        st.rerun()

with btn_col2:
    if st.button("絞り込み解除", key="clear_filter_sidebar"):
        st.session_state.applied_keyword = ""
        st.session_state.applied_ranks = []
        st.session_state.applied_kubun = []
        st.session_state.kw_input = ""
        st.session_state.rank_multi = []
        st.session_state.kubun_multi = []
        st.rerun()

st.sidebar.markdown("---")

# === ログアウトボタン ===
if st.session_state.authenticated:
    if st.sidebar.button("ログアウト", key="logout_sidebar"):
        reset_login_state(clear_data=False)
        st.rerun()


# ===== 実際に使う絞り込み条件は「適用済み」の値 =====
applied_keyword = st.session_state.applied_keyword
applied_ranks = st.session_state.applied_ranks
applied_kubun = st.session_state.applied_kubun


def match_freeword(rec: dict, keyword: str) -> bool:
    if not keyword:
        return True
    k = keyword.lower()
    fields = [
        str(rec.get("資格名", "")),
        str(rec.get("ランク", "")),
        str(rec.get("区分", "")),
        str(rec.get("金額", "")),
    ]
    text = " ".join(fields).lower()
    return k in text


def filter_records(rec_list):
    filtered = []
    for r in rec_list:
        rank_val = str(r.get("ランク", ""))
        kubun_val = str(r.get("区分", ""))

        if applied_ranks:
            if rank_val not in map(str, applied_ranks):
                continue

        if applied_kubun:
            if kubun_val not in map(str, applied_kubun):
                continue

        if not match_freeword(r, applied_keyword):
            continue

        filtered.append(r)
    return filtered


remaining_records_filtered = filter_records(remaining_records)
acquired_records_filtered = filter_records(acquired_records)
superior_records_filtered = filter_records(superior_records)

# =========================================================
#  カード描画用の共通処理
# =========================================================
def render_qual_card(rec, mode: str):
    """
    mode: "unacquired" / "acquired" / "superior"
    """
    idx = rec["id"]
    qual_name = rec.get("資格名", "")
    rank = rec.get("ランク", "")
    kubun = rec.get("区分", "")
    money = rec.get("金額", "")

    with st.container():
        # 資格情報の枠
        st.markdown(
            f"""
            <div class="card-root"><div class="qual-card-wrapper"><div class="qual-name-box"><span class="qual-name-text">{qual_name}</span></div><div class="qual-meta">
                    ランク: {rank}<br>
                    区分: {kubun}<br>
                    金額: {money}
                </div></div></div>
            """,
            unsafe_allow_html=True
        )

        # ▼ ボタン行（枠のすぐ下・縦並び）
        st.markdown('<div class="qual-card-btn-row">', unsafe_allow_html=True)

        if mode == "unacquired":
            if st.button("取得", key=f"acquire_{idx}"):
                acquired_ids = st.session_state.acquired_ids
                superior_ids = st.session_state.superior_ids
                acquired_ids.add(idx)
                if idx in superior_ids:
                    superior_ids.discard(idx)
                st.session_state.acquired_ids = acquired_ids
                st.session_state.superior_ids = superior_ids
                st.rerun()

            if st.button("上位互換取得", key=f"acquire_superior_{idx}"):
                acquired_ids = st.session_state.acquired_ids
                superior_ids = st.session_state.superior_ids
                acquired_ids.add(idx)
                superior_ids.add(idx)
                st.session_state.acquired_ids = acquired_ids
                st.session_state.superior_ids = superior_ids
                st.rerun()

        elif mode == "acquired":
            if st.button("取得解除", key=f"unacquire_{idx}"):
                acquired_ids = st.session_state.acquired_ids
                superior_ids = st.session_state.superior_ids
                if idx in acquired_ids:
                    acquired_ids.remove(idx)
                if idx in superior_ids:
                    superior_ids.remove(idx)
                st.session_state.acquired_ids = acquired_ids
                st.session_state.superior_ids = superior_ids
                st.rerun()

            if st.button("上位互換取得に変更", key=f"set_superior_{idx}"):
                acquired_ids = st.session_state.acquired_ids
                superior_ids = st.session_state.superior_ids
                acquired_ids.add(idx)
                superior_ids.add(idx)
                st.session_state.acquired_ids = acquired_ids
                st.session_state.superior_ids = superior_ids
                st.rerun()

        elif mode == "superior":
            if st.button("上位互換フラグ解除", key=f"unset_superior_{idx}"):
                superior_ids = st.session_state.superior_ids
                if idx in superior_ids:
                    superior_ids.remove(idx)
                st.session_state.superior_ids = superior_ids
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
#  未取得の資格
# =========================================================
if st.session_state.show_unacquired:
    st.subheader("未取得の資格")

    if not remaining_records_filtered:
        st.info("条件に合致する未取得の資格はありません。")
    else:
        for rec in remaining_records_filtered:
            render_qual_card(rec, mode="unacquired")

# =========================================================
#  取得済み（上位互換はまだ）
# =========================================================
if st.session_state.show_acquired:
    st.subheader("取得済み（上位互換はまだ）の資格")

    if not acquired_records_filtered:
        st.info("条件に合致する『取得済み（上位互換はまだ）』の資格はありません。")
    else:
        for rec in acquired_records_filtered:
            render_qual_card(rec, mode="acquired")

# =========================================================
#  上位互換を取得済みの資格
# =========================================================
if st.session_state.show_superior:
    st.subheader("上位互換を取得済みの資格")

    if not superior_records_filtered:
        st.info("条件に合致する『上位互換を取得済み』の資格はありません。")
    else:
        for rec in superior_records_filtered:
            render_qual_card(rec, mode="superior")
