import random
import streamlit as st


st.set_page_config(page_title="Тренажер множення", page_icon="✖️", layout="wide")


def init_state():
    defaults = {
        "started": False,
        "pairs": {},
        "total_pairs": 0,
        "current_pair": None,
        "message": "Налаштуйте діапазон і натисніть «Почати».",
        "message_type": "info",  # info / success / error
        "questions_count": 0,
        "correct_count": 0,
        "wrong_count": 0,
        "finished": False,
        "answer_input": "",
        "student_name": "",
        "mistakes": {},  # {(a,b): count}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def generate_pairs(start: int, end: int) -> dict[tuple[int, int], int]:
    return {(a, b): 0 for a in range(start, end + 1) for b in range(a, end + 1)}


def choose_weighted_pair(pairs: dict[tuple[int, int], int]) -> tuple[int, int]:
    pair_list = list(pairs.keys())
    weights = [3 - pairs[pair] for pair in pair_list]
    return random.choices(pair_list, weights=weights, k=1)[0]


def pair_to_text(pair: tuple[int, int]) -> str:
    a, b = pair
    return f"{a} × {b}"


def set_message(text: str, msg_type: str = "info"):
    st.session_state.message = text
    st.session_state.message_type = msg_type


def render_message():
    msg = st.session_state.message
    msg_type = st.session_state.message_type

    color = "#1f2937"
    if msg_type == "success":
        color = "#15803d"
    elif msg_type == "error":
        color = "#b91c1c"

    st.markdown(
        f"""
        <div style="
            font-weight: 700;
            color: {color};
            font-size: 1.05rem;
            margin-top: 10px;
            margin-bottom: 10px;
        ">
            {msg}
        </div>
        """,
        unsafe_allow_html=True,
    )


def pick_next_task():
    if not st.session_state.pairs:
        st.session_state.current_pair = None
        st.session_state.finished = True

        name = st.session_state.student_name.strip()
        if name:
            set_message(f"Вітаю, {name}! Усі пари засвоєно.", "success")
        else:
            set_message("Вітаю! Усі пари засвоєно.", "success")
        return

    st.session_state.current_pair = choose_weighted_pair(st.session_state.pairs)


def start_training(start: int, end: int, student_name: str):
    if start > end:
        start, end = end, start

    st.session_state.pairs = generate_pairs(start, end)
    st.session_state.total_pairs = len(st.session_state.pairs)
    st.session_state.current_pair = None
    st.session_state.questions_count = 0
    st.session_state.correct_count = 0
    st.session_state.wrong_count = 0
    st.session_state.started = True
    st.session_state.finished = False
    st.session_state.answer_input = ""
    st.session_state.student_name = student_name.strip()
    st.session_state.mistakes = {}

    if st.session_state.student_name:
        set_message(f"Тренування розпочато, {st.session_state.student_name}.", "info")
    else:
        set_message("Тренування розпочато.", "info")

    pick_next_task()


def register_mistake(pair: tuple[int, int]):
    if pair not in st.session_state.mistakes:
        st.session_state.mistakes[pair] = 0
    st.session_state.mistakes[pair] += 1


def check_answer():
    if st.session_state.finished or st.session_state.current_pair is None:
        return

    raw = str(st.session_state.answer_input).strip()

    if raw == "":
        set_message("Введіть відповідь.", "error")
        return

    try:
        user_answer = int(raw)
    except ValueError:
        set_message("Потрібно ввести ціле число.", "error")
        st.session_state.answer_input = ""
        return

    a, b = st.session_state.current_pair
    correct_answer = a * b
    st.session_state.questions_count += 1

    if user_answer == correct_answer:
        st.session_state.correct_count += 1
        st.session_state.pairs[(a, b)] += 1
        streak = st.session_state.pairs[(a, b)]

        if streak >= 3:
            del st.session_state.pairs[(a, b)]
            set_message(f"Правильно. Пару {a} × {b} засвоєно.", "success")
        else:
            set_message(
                f"Правильно. Для пари {a} × {b}: {streak}/3 правильних поспіль.",
                "success"
            )
    else:
        st.session_state.wrong_count += 1
        st.session_state.pairs[(a, b)] = 0
        register_mistake((a, b))
        set_message(
            f"Неправильно. Правильна відповідь: {correct_answer}. "
            f"Серію для {a} × {b} скинуто.",
            "error"
        )

    st.session_state.answer_input = ""
    pick_next_task()


def reset_training():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_state()


def render_mistakes_sidebar():
    st.sidebar.header("Помилки")

    if not st.session_state.started:
        st.sidebar.write("Після початку тренування тут з’явиться статистика помилок.")
        return

    if not st.session_state.mistakes:
        st.sidebar.write("Помилок поки немає.")
        return

    rows = []
    for pair, count in sorted(
        st.session_state.mistakes.items(),
        key=lambda item: (-item[1], item[0])
    ):
        rows.append({
            "Пара": pair_to_text(pair),
            "Помилки": count
        })

    st.sidebar.table(rows)


init_state()

st.title("Тренажер множення")
st.write(
    "Пара вважається засвоєною після **3 правильних відповідей поспіль**. "
    "Пари **{a, b}** і **{b, a}** вважаються однією й тією ж парою."
)

render_mistakes_sidebar()

with st.container(border=True):
    c1, c2, c3, c4 = st.columns([1.1, 1, 1, 1.2])

    with c1:
        student_name = st.text_input(
            "Ім'я учня",
            value=st.session_state.student_name,
            placeholder="Наприклад: Андрій"
        )

    with c2:
        start = st.number_input("Від", value=11, step=1)

    with c3:
        end = st.number_input("До", value=20, step=1)

    with c4:
        st.write("")
        st.write("")
        if st.button("Почати / перезапустити", use_container_width=True):
            start_training(int(start), int(end), student_name)
            st.rerun()

if st.session_state.started:
    mastered = st.session_state.total_pairs - len(st.session_state.pairs)
    total = st.session_state.total_pairs
    remaining = len(st.session_state.pairs)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Засвоєно пар", f"{mastered}/{total}")
    m2.metric("Залишилось", remaining)
    m3.metric("Правильних", st.session_state.correct_count)
    m4.metric("Помилок", st.session_state.wrong_count)

    st.divider()

    if st.session_state.finished:
        render_message()
        st.balloons()

        if st.session_state.questions_count > 0:
            accuracy = 100 * st.session_state.correct_count / st.session_state.questions_count
            st.write(f"**Усього прикладів:** {st.session_state.questions_count}")
            st.write(f"**Точність:** {accuracy:.1f}%")

        if st.button("Скинути все"):
            reset_training()
            st.rerun()

    else:
        a, b = st.session_state.current_pair

        st.markdown(
            f"""
            <div style="
                text-align:center;
                font-size:48px;
                font-weight:700;
                margin: 24px 0 18px 0;
            ">
                {a} × {b} = ?
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.text_input(
            "Ваша відповідь",
            key="answer_input",
            placeholder="Введіть число і натисніть Enter",
            on_change=check_answer,
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Скинути тренування", use_container_width=True):
                reset_training()
                st.rerun()
        with col2:
            st.write("")

        render_message()

        with st.expander("Показати детальний прогрес"):
            if st.session_state.pairs:
                rows = []
                for (x, y), streak in sorted(st.session_state.pairs.items()):
                    rows.append({"Пара": f"{x} × {y}", "Серія": f"{streak}/3"})
                st.table(rows)