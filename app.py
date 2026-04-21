import random
import streamlit as st

st.set_page_config(page_title="Тренажер множення", page_icon="✖️", layout="wide")


def init_app_state():
    if "game" not in st.session_state:
        st.session_state.game = {
            "started": False,
            "finished": False,
            "student_name": "",
            "pairs": {},
            "total_pairs": 0,
            "current_pair": None,
            "questions_count": 0,
            "correct_count": 0,
            "wrong_count": 0,
            "mistakes": {},
            "message": "Налаштуйте діапазон і натисніть «Почати».",
            "message_type": "info",
        }


def generate_pairs(start: int, end: int) -> dict[tuple[int, int], int]:
    return {(a, b): 0 for a in range(start, end + 1) for b in range(a, end + 1)}


def choose_weighted_pair(pairs: dict[tuple[int, int], int]) -> tuple[int, int]:
    pair_list = list(pairs.keys())
    weights = [3 - pairs[pair] for pair in pair_list]
    return random.choices(pair_list, weights=weights, k=1)[0]


def set_message(text: str, msg_type: str = "info") -> None:
    st.session_state.game["message"] = text
    st.session_state.game["message_type"] = msg_type


def pick_next_task() -> None:
    game = st.session_state.game
    if not game["pairs"]:
        game["current_pair"] = None
        game["finished"] = True
        name = game["student_name"].strip()
        if name:
            set_message(f"Вітаю, {name}! Усі пари засвоєно.", "success")
        else:
            set_message("Вітаю! Усі пари засвоєно.", "success")
        return
    game["current_pair"] = choose_weighted_pair(game["pairs"])


def start_training() -> None:
    game = st.session_state.game
    start = int(st.session_state.range_start)
    end = int(st.session_state.range_end)
    if start > end:
        start, end = end, start

    game["started"] = True
    game["finished"] = False
    game["student_name"] = st.session_state.student_name_input.strip()
    game["pairs"] = generate_pairs(start, end)
    game["total_pairs"] = len(game["pairs"])
    game["questions_count"] = 0
    game["correct_count"] = 0
    game["wrong_count"] = 0
    game["mistakes"] = {}
    game["current_pair"] = None

    if game["student_name"]:
        set_message(f"Тренування розпочато, {game['student_name']}.", "info")
    else:
        set_message("Тренування розпочато.", "info")

    # очистити поле відповіді ДО створення форми на rerun
    st.session_state.answer_field = ""
    pick_next_task()


def register_mistake(pair: tuple[int, int]) -> None:
    mistakes = st.session_state.game["mistakes"]
    mistakes[pair] = mistakes.get(pair, 0) + 1


def submit_answer() -> None:
    game = st.session_state.game
    if game["finished"] or game["current_pair"] is None:
        return

    raw = str(st.session_state.answer_field).strip()
    if raw == "":
        set_message("Введіть відповідь.", "error")
        return

    try:
        user_answer = int(raw)
    except ValueError:
        set_message("Потрібно ввести ціле число.", "error")
        return

    a, b = game["current_pair"]
    correct_answer = a * b
    game["questions_count"] += 1

    if user_answer == correct_answer:
        game["correct_count"] += 1
        game["pairs"][(a, b)] += 1
        streak = game["pairs"][(a, b)]

        if streak >= 3:
            del game["pairs"][(a, b)]
            set_message(f"Правильно. Пару {a} × {b} засвоєно.", "success")
        else:
            set_message(f"Правильно. Для пари {a} × {b}: {streak}/3 правильних поспіль.", "success")
    else:
        game["wrong_count"] += 1
        game["pairs"][(a, b)] = 0
        register_mistake((a, b))
        set_message(
            f"Неправильно. Правильна відповідь: {correct_answer}. "
            f"Серію для {a} × {b} скинуто.",
            "error",
        )

    # st.session_state.answer_field = ""
    pick_next_task()


def reset_game() -> None:
    st.session_state.game = {
        "started": False,
        "finished": False,
        "student_name": "",
        "pairs": {},
        "total_pairs": 0,
        "current_pair": None,
        "questions_count": 0,
        "correct_count": 0,
        "wrong_count": 0,
        "mistakes": {},
        "message": "Налаштуйте діапазон і натисніть «Почати».",
        "message_type": "info",
    }

    if "answer_field" in st.session_state:
        del st.session_state["answer_field"]


def render_message():
    game = st.session_state.game
    color = "#1f2937"
    if game["message_type"] == "success":
        color = "#15803d"
    elif game["message_type"] == "error":
        color = "#b91c1c"

    st.markdown(
        f"""
        <div style="font-weight:700; color:{color}; font-size:1.05rem; margin:10px 0;">
            {game["message"]}
        </div>
        """,
        unsafe_allow_html=True,
    )


init_app_state()
game = st.session_state.game

st.title("Тренажер множення")

with st.container(border=True):
    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1.2])

    with c1:
        st.text_input("Ім'я учня", key="student_name_input", value=game["student_name"])
    with c2:
        st.number_input("Від", key="range_start", value=11, step=1)
    with c3:
        st.number_input("До", key="range_end", value=20, step=1)
    with c4:
        st.write("")
        st.write("")
        st.button("Почати / перезапустити", key="start_btn", on_click=start_training, use_container_width=True)

st.sidebar.header("Помилки")
if game["mistakes"]:
    rows = [
        {"Пара": f"{a} × {b}", "Помилки": count}
        for (a, b), count in sorted(game["mistakes"].items(), key=lambda x: (-x[1], x[0]))
    ]
    st.sidebar.table(rows)
else:
    st.sidebar.write("Помилок поки немає.")

if game["started"]:
    mastered = game["total_pairs"] - len(game["pairs"])
    total = game["total_pairs"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Засвоєно пар", f"{mastered}/{total}")
    m2.metric("Залишилось", len(game["pairs"]))
    m3.metric("Правильних", game["correct_count"])
    m4.metric("Помилок", game["wrong_count"])

    st.divider()

    if game["finished"]:
        render_message()
        st.balloons()
        if st.button("Скинути все", key="reset_all_btn"):
            reset_game()
            st.rerun()
    else:
        a, b = game["current_pair"]
        st.markdown(
            f'<div style="text-align:center;font-size:48px;font-weight:700;margin:24px 0 18px 0;">{a} × {b} = ?</div>',
            unsafe_allow_html=True,
        )

        with st.form("answer_form", clear_on_submit=True):
            st.text_input("Ваша відповідь", key="answer_field", placeholder="Введіть число і натисніть Enter")
            submitted = st.form_submit_button("Перевірити", on_click=submit_answer, use_container_width=True)

        render_message()

        if st.button("Скинути тренування", key="reset_training_btn"):
            reset_game()
            st.rerun()