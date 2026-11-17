import json
import os
import re
import tempfile
import threading
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

import streamlit as st

MAX_NAME_LENGTH = 50
FILTERS = ["전체", "미완료", "완료"]
USER_PARAM = "u"
USER_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
DATA_FILE = Path(os.environ.get("SHOPPING_DATA_FILE", Path(__file__).parent / "data" / "items.json"))
MAX_QUANTITY = 999
_file_lock = threading.Lock()

CSS = """
<style>
:root {
  --bg: #F2F2F7;
  --card: #FFFFFF;
  --text: #1C1C1E;
  --text2: #6E6E73;
  --sep: #E5E5EA;
  --fill: #F2F2F7;
  --blue: #007AFF;
  --blue-text: #0066CC;
  --red: #FF3B30;
  --red-text: #D70015;
  --btn-bg: #0071E3;
  --green: #34C759;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  --font: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Apple SD Gothic Neo",
          "Pretendard", "Segoe UI", "Malgun Gothic", sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #000000;
    --card: #1C1C1E;
    --text: #F2F2F7;
    --text2: #98989D;
    --sep: #38383A;
    --fill: #2C2C2E;
    --blue: #0A84FF;
    --blue-text: #0A84FF;
    --red: #FF453A;
    --red-text: #FF453A;
    --green: #30D158;
    --shadow: none;
  }
}

/* 기본 크롬 숨김 */
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], footer, #MainMenu { display: none !important; }

/* 레이아웃 */
.stApp { background: var(--bg) !important; color: var(--text); }
.stApp, .stApp p, .stApp label, .stApp input, .stApp button, .stApp h1,
.stApp [data-testid="stMarkdownContainer"] { font-family: var(--font) !important; }
[data-testid="stMainBlockContainer"] {
  max-width: 640px; margin: 0 auto; padding: 48px 16px 64px;
}
.stApp p, .stApp label, .stApp h1 { color: var(--text); }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p {
  color: var(--text2) !important;
}

/* 라지 타이틀 */
.stApp h1 {
  font-size: 34px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.15;
  padding: 0 4px 16px;
}

/* 카드 공통 */
[data-testid="stForm"], .st-key-list_card {
  background: var(--card); border: none; border-radius: 16px;
  box-shadow: var(--shadow); padding: 16px;
}
.st-key-list_card { padding: 0; overflow: hidden; gap: 0 !important; }
/* 목록 안의 수정 폼은 카드 스타일 없이 행에 녹인다 */
.st-key-list_card [data-testid="stForm"] { background: transparent; box-shadow: none; border-radius: 0; padding: 0; }

/* 입력창 */
.stApp [data-testid="stTextInputRootElement"], .stApp [data-testid="stNumberInputContainer"] {
  background: var(--fill) !important; border: 1px solid transparent !important;
  border-radius: 10px !important; transition: border-color .2s, box-shadow .2s;
}
.stApp [data-testid="stTextInputRootElement"]:focus-within, .stApp [data-testid="stNumberInputContainer"]:focus-within {
  border-color: var(--blue) !important; box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.25);
}
.stApp input { color: var(--text) !important; background: transparent !important; }
.stApp input::placeholder { color: var(--text2) !important; }
.stApp [data-testid="stNumberInput"] button { color: var(--text2); background: transparent; }
.stApp [data-testid="stTextInput"] [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stNumberInput"] [data-testid="stWidgetLabel"] p { color: var(--text2); font-size: 13px; }

/* 버튼 */
.stApp button { transition: background-color .15s, opacity .15s, transform .15s; }
.stApp button:active { transform: scale(0.97); }
.stApp [data-testid="stBaseButton-secondary"], .stApp [class*="st-key-cancel_"] button {
  background: transparent; border: none; box-shadow: none; color: var(--blue-text);
  min-height: 36px; padding: 0 12px; border-radius: 10px; width: auto;
}
.stApp [data-testid="stBaseButton-secondary"]:hover:not(:disabled), .stApp [class*="st-key-cancel_"] button:hover {
  background: rgba(0, 122, 255, 0.1); color: var(--blue-text);
}
.stApp [data-testid="stBaseButton-secondary"] p, .stApp [class*="st-key-cancel_"] button p { color: inherit !important; }
.stApp [class*="st-key-del_"] [data-testid="stBaseButton-secondary"] { color: var(--red-text); }
.stApp [class*="st-key-del_"] [data-testid="stBaseButton-secondary"]:hover:not(:disabled) {
  background: rgba(255, 59, 48, 0.1); color: var(--red-text);
}
.stApp [data-testid="stBaseButton-secondary"]:disabled { color: var(--text2); opacity: .5; }
.stApp .st-key-add_submit button, .stApp [data-testid="stBaseButton-primary"],
.stApp [data-testid="stBaseButton-secondaryFormSubmit"], .stApp [data-testid="stBaseButton-primaryFormSubmit"] {
  background: var(--btn-bg); color: #fff; border: none; border-radius: 999px;
  min-height: 40px; padding: 0 22px; font-weight: 600; width: 100%;
}
.stApp [class*="st-key-cancel_"] button { min-height: 36px; padding: 0 12px; font-weight: 400; }
.stApp button:focus-visible, .stApp [data-testid="stRadioOption"]:has(input:focus-visible) {
  outline: 2px solid var(--blue); outline-offset: 2px;
}
.stApp .st-key-add_submit button p, .stApp [data-testid="stBaseButton-primary"] p,
.stApp [data-testid="stBaseButton-secondaryFormSubmit"] p,
.stApp [data-testid="stBaseButton-primaryFormSubmit"] p { color: #fff !important; }
.stApp .st-key-add_submit button:hover, .stApp [data-testid="stBaseButton-primary"]:hover,
.stApp [data-testid="stBaseButton-secondaryFormSubmit"]:hover,
.stApp [data-testid="stBaseButton-primaryFormSubmit"]:hover { opacity: .85; background: var(--btn-bg); }
.stApp [class*="st-key-cancel_"] button:hover { opacity: 1; }
.stApp .st-key-clear_checked button:not(:disabled) { color: var(--red-text); }

/* 진행 바 */
.stApp [data-testid="stProgressBarTrack"] {
  height: 6px; border-radius: 999px; background: var(--sep) !important; overflow: hidden;
}
.stApp [data-testid="stProgressBarTrack"] > div {
  background: var(--green) !important; border-radius: 999px; transition: width .3s ease;
}

/* 필터: 세그먼트 컨트롤 */
.stApp .stElementContainer:has([data-testid="stRadio"]), .stApp [data-testid="stRadio"] { width: 100% !important; }
.stApp [data-testid="stRadioGroup"] {
  display: flex; flex-wrap: nowrap; gap: 0; width: 100%;
  background: var(--sep); border-radius: 10px; padding: 2px; box-sizing: border-box;
}
.stApp [data-testid="stRadioGroup"] > div { flex: 1 1 0; margin: 0; }
.stApp [data-testid="stRadioOption"] {
  display: flex; justify-content: center; width: 100%; margin: 0; padding: 6px 0;
  border-radius: 8px; cursor: pointer; box-sizing: border-box;
  transition: background-color .2s, box-shadow .2s;
}
.stApp [data-testid="stRadioOption"] > div { margin: 0; }
.stApp [data-testid="stRadioOption"] > div > div:first-of-type { display: none; }
.stApp [data-testid="stRadioOption"] p { font-size: 13px; font-weight: 500; text-align: center; margin: 0; }
.stApp [data-testid="stRadioOption"]:has(input:checked) {
  background: var(--card); box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

/* 목록 행 */
.stApp [class*="st-key-row_"] {
  padding: 6px 12px 6px 16px; border-bottom: 1px solid var(--sep); gap: 0;
  transition: background-color .15s;
}
.stApp [data-testid="stLayoutWrapper"]:last-child > [class*="st-key-row_"] { border-bottom: none; }
.stApp [class*="st-key-row_"] [data-testid="stHorizontalBlock"] {
  flex-wrap: nowrap !important; gap: 4px; align-items: center;
}
.stApp [class*="st-key-row_"] [data-testid="stColumn"] { min-width: 0 !important; }
.stApp [class*="st-key-row_"] [data-testid="stColumn"]:not(:first-child) { flex: 0 0 auto !important; width: auto !important; }
.stApp [class*="st-key-row_"] [data-testid="stColumn"]:first-child { flex: 1 1 0 !important; }

/* 긴 이름은 말줄임 대신 줄바꿈 */
.stApp [class*="st-key-chk_"], .stApp [data-testid="stCheckbox"], .stApp [data-testid="stCheckbox"] label { width: 100% !important; }
.stApp [data-testid="stCheckbox"] [data-testid="stWidgetLabel"] { flex: 1 1 0; min-width: 0; width: auto; }
.stApp [data-testid="stCheckbox"] .stMarkdownEllipsis, .stApp [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"],
.stApp [data-testid="stCheckbox"] p {
  white-space: normal !important; overflow: visible !important; text-overflow: clip !important;
  overflow-wrap: anywhere;
}

/* 원형 체크박스 */
.stApp [data-testid="stCheckbox"] label { gap: 12px; min-height: 44px; align-items: center; cursor: pointer; }
.stApp [data-testid="stCheckbox"] label > div:first-of-type {
  width: 24px; height: 24px; min-width: 24px; border-radius: 50%; box-sizing: border-box;
  background: transparent !important; border: 2px solid #C7C7CC !important;
  transition: background-color .2s, border-color .2s;
}
.stApp [data-testid="stCheckbox"] label > div:first-of-type svg { display: none; }
.stApp [data-testid="stCheckbox"] label:has(input:checked) > div:first-of-type {
  background: var(--green) !important; border-color: var(--green) !important;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 12.5l4 4 8-9'/%3E%3C/svg%3E") !important;
  background-size: 70% !important; background-position: center !important; background-repeat: no-repeat !important;
}
.stApp [data-testid="stCheckbox"] label:has(input:focus-visible) > div:first-of-type {
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.35);
}
.stApp [data-testid="stCheckbox"] label:has(input:checked) p { color: var(--text2); }

/* 빈 상태 */
.empty-state { text-align: center; padding: 56px 16px; color: var(--text2); }
.empty-state .emoji { font-size: 56px; line-height: 1; margin-bottom: 12px; }
.empty-state .msg { font-size: 15px; }

/* 경고 */
.stApp [data-testid="stAlert"] { border-radius: 12px; }

/* 모바일 */
@media (max-width: 480px) {
  [data-testid="stMainBlockContainer"] { padding: 24px 16px 48px; }
  .stApp h1 { font-size: 30px; }
  .stApp button { min-height: 44px !important; }
  .stApp [data-testid="stTextInputRootElement"], .stApp [data-testid="stNumberInputContainer"] { min-height: 44px; }
  .stApp [data-testid="stNumberInputContainer"] button { display: none; }
  .stApp [data-testid="stRadioOption"] { min-height: 44px; align-items: center; }
  [data-testid="stForm"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 12px; }
  [data-testid="stForm"] [data-testid="stColumn"] { flex: 1 1 40% !important; min-width: 0 !important; }
  [data-testid="stForm"] [data-testid="stColumn"]:first-child { flex: 1 1 100% !important; }
  .stApp [class*="st-key-row_"] [data-testid="stBaseButton-secondary"] { padding: 0 8px; }
}
</style>
"""


@dataclass
class Item:
    name: str
    quantity: int = 1
    checked: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


def normalize_name(name: str) -> str:
    return (name or "").strip()[:MAX_NAME_LENGTH]


def clamp_quantity(value: object) -> int:
    try:
        return max(1, min(MAX_QUANTITY, int(value)))
    except (TypeError, ValueError):
        return 1


def md_escape(text: str) -> str:
    """사용자 입력이 마크다운, 이모지 코드, HTML 엔티티로 해석되지 않도록 이스케이프한다."""
    return re.sub(r"([\\`*_~\[\]<>$:|#&])", r"\\\1", text)


# ---------- 저장소 ----------
# 새로고침하면 Streamlit 세션이 새로 만들어지므로, 접속자 ID를 URL(?u=...)에 두고
# 목록은 JSON 파일에 접속자 ID별로 저장한다.

def _read_store() -> dict:
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_store(store: dict) -> bool:
    """임시 파일에 쓴 뒤 교체해 파일이 반쯤 쓰인 채 손상되는 것을 막는다."""
    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=DATA_FILE.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)
        return True
    except OSError:
        return False


def _item_from_dict(raw: object) -> Item | None:
    if not isinstance(raw, dict):
        return None
    name = normalize_name(str(raw.get("name", "")))
    if not name:
        return None
    item_id = raw.get("id")
    return Item(
        name=name,
        quantity=clamp_quantity(raw.get("quantity", 1)),
        checked=bool(raw.get("checked", False)),
        id=item_id if isinstance(item_id, str) and item_id else str(uuid.uuid4()),
    )


def _items_of(store: dict, user_id: str) -> list[Item]:
    raw_items = store.get(user_id, [])
    if not isinstance(raw_items, list):
        return []
    return [i for i in (_item_from_dict(r) for r in raw_items) if i is not None]


def load_items(user_id: str) -> list[Item]:
    with _file_lock:
        return _items_of(_read_store(), user_id)


def apply_change(change: Callable[[list[Item]], None]) -> None:
    """파일의 최신 목록을 읽어 변경을 적용하고 저장한다.

    세션이 들고 있는 목록이 아니라 파일을 기준으로 바꾸므로, 같은 URL을 연 다른 탭이
    저장한 항목을 덮어써서 잃지 않는다.
    """
    user_id = st.session_state["user_id"]
    with _file_lock:
        store = _read_store()
        # 저장이 실패한 상태(offline)에서는 파일에 없는 변경이 세션에만 있으므로 세션 목록을 기준으로 한다.
        items = st.session_state["items"] if st.session_state.get("offline") else _items_of(store, user_id)
        change(items)
        store[user_id] = [asdict(i) for i in items]
        saved = _write_store(store)
    st.session_state["offline"] = not saved
    if not saved:
        st.session_state["save_failed"] = True
    st.session_state["items"] = items


def get_user_id() -> str:
    user_id = st.query_params.get(USER_PARAM, "")
    if not USER_ID_PATTERN.match(user_id):
        user_id = uuid.uuid4().hex
        st.query_params[USER_PARAM] = user_id
    return user_id


# ---------- 상태 ----------

def init_state() -> None:
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = get_user_id()
    # 매 실행마다 파일에서 읽어 다른 탭의 변경도 반영한다. 저장이 실패한 상태면 세션 목록을 유지한다.
    if not st.session_state.get("offline") or "items" not in st.session_state:
        st.session_state["items"] = load_items(st.session_state["user_id"])
    if "editing_id" not in st.session_state:
        st.session_state["editing_id"] = None
    if "edit_error" not in st.session_state:
        st.session_state["edit_error"] = None
    editing = st.session_state["editing_id"]
    if editing is not None and find_item(editing) is None:
        cancel_edit()


def find_item(item_id: str, items: list[Item] | None = None) -> Item | None:
    if items is None:
        items = st.session_state["items"]
    return next((i for i in items if i.id == item_id), None)


# ---------- 로직 ----------

def add_item(name: str, quantity: int) -> bool:
    name = normalize_name(name)
    if not name:
        return False
    new_item = Item(name=name, quantity=clamp_quantity(quantity))
    apply_change(lambda items: items.append(new_item))
    return True


def start_edit(item_id: str) -> None:
    item = find_item(item_id)
    if item is None:
        return
    st.session_state["editing_id"] = item_id
    st.session_state["edit_error"] = None
    st.session_state[f"edit_name_{item_id}"] = item.name
    st.session_state[f"edit_qty_{item_id}"] = item.quantity


def cancel_edit() -> None:
    st.session_state["editing_id"] = None
    st.session_state["edit_error"] = None


def update_item(item_id: str) -> None:
    name = normalize_name(st.session_state.get(f"edit_name_{item_id}", ""))
    if not name:
        st.session_state["edit_error"] = "아이템 이름을 입력해 주세요."
        return
    quantity = clamp_quantity(st.session_state.get(f"edit_qty_{item_id}", 1))

    def change(items: list[Item]) -> None:
        item = find_item(item_id, items)
        if item is not None:
            item.name, item.quantity = name, quantity

    apply_change(change)
    cancel_edit()


def delete_item(item_id: str) -> None:
    def change(items: list[Item]) -> None:
        items[:] = [i for i in items if i.id != item_id]

    apply_change(change)
    if st.session_state["editing_id"] == item_id:
        cancel_edit()


def toggle_item(item_id: str) -> None:
    checked = bool(st.session_state.get(f"chk_{item_id}", False))

    def change(items: list[Item]) -> None:
        item = find_item(item_id, items)
        if item is not None:
            item.checked = checked

    apply_change(change)


def clear_checked() -> None:
    def change(items: list[Item]) -> None:
        items[:] = [i for i in items if not i.checked]

    apply_change(change)
    editing = st.session_state["editing_id"]
    if editing is not None and find_item(editing) is None:
        cancel_edit()


# ---------- 화면 ----------

def render_add_form() -> None:
    with st.form("add_form", clear_on_submit=True):
        col_name, col_qty, col_btn = st.columns([5, 2, 2], vertical_alignment="bottom")
        name = col_name.text_input(
            "이름", max_chars=MAX_NAME_LENGTH, placeholder="살 물건을 입력하세요", key="add_name"
        )
        qty = col_qty.number_input("수량", min_value=1, max_value=MAX_QUANTITY, value=1, step=1, key="add_qty")
        submitted = col_btn.form_submit_button("추가", key="add_submit")
    if not submitted:
        return
    if not add_item(name, qty):
        st.warning("아이템 이름을 입력해 주세요.")
    elif st.session_state.get("filter") == "완료":
        # 새 항목은 미완료라서 '완료' 필터에서는 보이지 않으므로 전체 보기로 돌린다.
        st.session_state["filter"] = "전체"


def render_item(item: Item) -> None:
    with st.container(key=f"row_{item.id}"):
        if st.session_state["editing_id"] == item.id:
            render_item_editing(item)
        else:
            render_item_view(item)


def render_item_view(item: Item) -> None:
    col_check, col_edit, col_del = st.columns([7, 1.5, 1.5], vertical_alignment="center")
    label = f"{md_escape(item.name)} × {item.quantity}"
    if item.checked:
        label = f"~~{label}~~"
    # 다른 탭에서 바뀐 값이 위젯의 옛 상태에 가려지지 않도록 매번 항목 값으로 맞춘다.
    st.session_state[f"chk_{item.id}"] = item.checked
    col_check.checkbox(label, key=f"chk_{item.id}", on_change=toggle_item, args=(item.id,))
    col_edit.button("수정", key=f"edit_{item.id}", on_click=start_edit, args=(item.id,))
    col_del.button("삭제", key=f"del_{item.id}", on_click=delete_item, args=(item.id,))


def render_item_editing(item: Item) -> None:
    name_key, qty_key = f"edit_name_{item.id}", f"edit_qty_{item.id}"
    # 필터 등으로 이 행이 잠시 사라지면 Streamlit이 위젯 값을 지우므로, 없으면 현재 값으로 채운다.
    st.session_state.setdefault(name_key, item.name)
    st.session_state.setdefault(qty_key, item.quantity)
    # 폼으로 감싸면 이름 입력창에서 Enter를 눌렀을 때 [저장]이 실행된다.
    with st.form(f"edit_form_{item.id}", border=False):
        col_name, col_qty, col_save, col_cancel = st.columns([5, 2, 1.5, 1.5], vertical_alignment="bottom")
        col_name.text_input("이름", max_chars=MAX_NAME_LENGTH, key=name_key)
        col_qty.number_input("수량", min_value=1, max_value=MAX_QUANTITY, step=1, key=qty_key)
        col_save.form_submit_button(
            "저장", key=f"save_{item.id}", type="primary", on_click=update_item, args=(item.id,)
        )
        col_cancel.form_submit_button("취소", key=f"cancel_{item.id}", on_click=cancel_edit)
    if st.session_state["edit_error"]:
        st.warning(st.session_state["edit_error"])


def render_summary(items: list[Item]) -> None:
    done = sum(1 for i in items if i.checked)
    st.caption(f"전체 {len(items)}개 중 {done}개 완료")
    st.progress(done / len(items))


def render_list() -> None:
    items: list[Item] = st.session_state["items"]
    if not items:
        st.markdown(
            '<div class="empty-state"><div class="emoji">🛒</div>'
            '<div class="msg">아직 아이템이 없어요.<br>위에서 살 물건을 추가해 보세요.</div></div>',
            unsafe_allow_html=True,
        )
        return

    render_summary(items)
    selected = st.radio("보기", FILTERS, horizontal=True, key="filter", label_visibility="collapsed")
    if selected == "미완료":
        visible = [i for i in items if not i.checked]
    elif selected == "완료":
        visible = [i for i in items if i.checked]
    else:
        visible = items

    if not visible:
        st.caption("해당하는 항목이 없어요.")
    with st.container(key="list_card"):
        for item in visible:
            render_item(item)

    st.write("")
    st.button(
        "완료 항목 모두 삭제",
        key="clear_checked",
        on_click=clear_checked,
        disabled=not any(i.checked for i in items),
    )


def main() -> None:
    st.set_page_config(page_title="쇼핑리스트", page_icon="🛒")
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    st.title("🛒 쇼핑리스트")
    save_warning = st.empty()  # 저장 실패 여부는 이번 실행의 모든 처리가 끝난 뒤에 알 수 있다.
    render_add_form()
    st.write("")
    render_list()
    if st.session_state.pop("save_failed", False):
        save_warning.warning("목록을 저장하지 못했어요. 새로고침하면 변경 내용이 사라질 수 있어요.")


main()
