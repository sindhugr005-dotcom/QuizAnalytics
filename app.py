import os

import pandas as pd
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import OperationFailure, PyMongoError
from streamlit.errors import StreamlitSecretNotFoundError

st.set_page_config(page_title="Quiz Analytics", page_icon="Q", layout="wide")

st.markdown(
	"""
	<style>
		@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
		:root { --ink: #172c2b; --green: #176b59; --mint: #e6f3ed; --coral: #e87553; }
		.stApp { background: #f5f7f3; color: var(--ink); }
		header[data-testid="stHeader"] { background: #f5f7f3; }
		.stApp, .stApp button, .stApp input { font-family: 'DM Sans', sans-serif; }
		[data-testid="stMainBlockContainer"] { max-width: 1120px; padding: 3rem 2rem 4rem; }
		h1, h2, h3 { font-family: 'Manrope', sans-serif !important; color: var(--ink); }
		div[data-testid="stMarkdownContainer"] p { font-size: 1rem; line-height: 1.55; }
		[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p { color: var(--ink) !important; opacity: 1 !important; }
		div[data-testid="stRadio"] label, div[data-testid="stRadio"] label p { color: var(--ink) !important; opacity: 1 !important; }
		section[data-testid="stSidebar"] { background: #e8f1ea; }
		div[data-testid="stForm"] { border: 1px solid #dce5dd; border-radius: 8px; padding: 1.5rem; background: #fff; }
		div[data-testid="stTextInput"] input { min-height: 48px; background: #fff !important; color: var(--ink) !important; border: 1px solid #bac8be !important; font-size: 16px !important; }
		div[data-testid="stTextInput"] input::placeholder { color: #63716a !important; opacity: 1; }
		.stButton > button, .stFormSubmitButton > button { background: var(--green); color: white; border: 0; border-radius: 6px; min-height: 2.8rem; }
		.stButton > button:hover, .stFormSubmitButton > button:hover { background: #105545; color: white; }
		.login-panel { min-height: 330px; display: flex; flex-direction: column; justify-content: center; background: var(--mint); border-left: 5px solid var(--coral); padding: 2.5rem; border-radius: 8px; }
		.login-panel h1 { margin: .6rem 0 1rem; font-size: 2.5rem !important; line-height: 1.15; }
		.login-panel p { color: #435550; }
		.eyebrow { color: var(--green); font-size: .8rem; font-weight: 700; text-transform: uppercase; }
		@media (max-width: 700px) {
			[data-testid="stMainBlockContainer"] { padding: 1.5rem 1rem 3rem; }
			.login-panel { min-height: 240px; padding: 1.5rem; }
		}
	</style>
	""",
	unsafe_allow_html=True,
)


def get_mongo_uri():
	"""Read the connection string from the environment or Streamlit secrets."""
	for value in (os.getenv("MONGODB_URI"),):
		if isinstance(value, str):
			candidate = value.strip()
			if candidate:
				return candidate

	try:
		candidate = st.secrets.get("MONGODB_URI")
		if isinstance(candidate, str):
			candidate = candidate.strip()
			if candidate:
				return candidate
		return None
	except (AttributeError, StreamlitSecretNotFoundError, TypeError):
		return None


def coerce_numeric_series(series):
	"""Normalize numeric-like values from CSV/Mongo exports to a pandas float series."""
	if series is None or series.empty:
		return pd.Series(dtype="float64")

	cleaned = series.map(lambda value: value.strip() if isinstance(value, str) else value)
	cleaned = cleaned.map(lambda value: value.replace("%", "").replace(",", "") if isinstance(value, str) else value)
	return pd.to_numeric(cleaned, errors="coerce")


if "logged_in_user" not in st.session_state:
	st.session_state.logged_in_user = None

if st.session_state.logged_in_user is None:
	left, right = st.columns([1.1, 1], gap="large")
	with left:
		st.markdown(
			"""
			<section class="login-panel">
				<p class="eyebrow">Quiz Analytics</p>
				<h1>Learn by doing.</h1>
				<p>Sign in to take a quiz, check your answers, and explore performance insights.</p>
				<p><strong>Python Basics</strong> &middot; Multiple choice &middot; Instant results</p>
			</section>
			""",
			unsafe_allow_html=True,
		)
	with right:
		st.subheader("Welcome back")
		st.caption("Demo sign-in. Any name and password will open the app.")
		with st.form("login_form"):
			login_name = st.text_input("Name or email", placeholder="you@example.com")
			login_password = st.text_input("Password", type="password", placeholder="Enter any password")
			login_submitted = st.form_submit_button("Sign in", use_container_width=True)
		if login_submitted:
			if login_name.strip() and login_password:
				st.session_state.logged_in_user = login_name.strip()
				st.rerun()
			else:
				st.error("Enter your name or email and a password to continue.")
	st.stop()

with st.sidebar:
	st.markdown("### Quiz Analytics")
	st.caption(f"Signed in as {st.session_state.logged_in_user}")
	page = st.radio("Go to", ["Take a quiz", "Analytics"], label_visibility="collapsed")
	if st.button("Sign out", use_container_width=True):
		st.session_state.logged_in_user = None
		st.rerun()

if page == "Take a quiz":
	st.markdown('<p class="eyebrow">Python Basics · 10 questions</p>', unsafe_allow_html=True)
	st.title("Quick knowledge check")
	st.write("Tick one option for each question, then submit to see your score.")
	questions = [
		{
			"question": "Which keyword defines a function in Python?",
			"options": ["function", "def", "define", "fun"],
			"answer": "def",
		},
		{
			"question": "What is the result of `len([2, 4, 6])`?",
			"options": ["2", "3", "6", "An error"],
			"answer": "3",
		},
		{
			"question": "Which type stores a sequence that can be changed?",
			"options": ["tuple", "str", "list", "int"],
			"answer": "list",
		},
		{
			"question": "Which symbol starts a single-line comment in Python?",
			"options": ["//", "#", "<!--", "**"],
			"answer": "#",
		},
		{
			"question": "What does `print(2 + 3)` display?",
			"options": ["23", "5", "2 + 3", "An error"],
			"answer": "5",
		},
		{
			"question": "Which value represents an empty value in Python?",
			"options": ["None", "null", "empty", "undefined"],
			"answer": "None",
		},
		{
			"question": "Which operator checks whether two values are equal?",
			"options": ["=", "==", "!=", ":="],
			"answer": "==",
		},
		{
			"question": "Which built-in function converts text to an integer?",
			"options": ["str()", "int()", "list()", "float()"],
			"answer": "int()",
		},
		{
			"question": "What is the index of the first item in a Python list?",
			"options": ["0", "1", "-1", "It has no index"],
			"answer": "0",
		},
		{
			"question": "Which loop is commonly used to iterate over a sequence?",
			"options": ["for", "switch", "repeat", "case"],
			"answer": "for",
		},
	]
	with st.form("quiz_form"):
		answers = []
		for question_number, item in enumerate(questions, start=1):
			st.markdown(f"**{question_number}. {item['question']}**")
			answers.append(
				st.radio(
					f"Answer {question_number}",
					item["options"],
					index=None,
					key=f"quiz_answer_{question_number}",
					label_visibility="collapsed",
				)
			)
		quiz_submitted = st.form_submit_button("Submit answers", use_container_width=True)
	if quiz_submitted:
		if any(answer is None for answer in answers):
			st.warning("Please select an answer for every question before submitting.")
		else:
			score = sum(answer == item["answer"] for answer, item in zip(answers, questions))
			st.session_state.latest_quiz_result = {"score": score, "total": len(questions), "answers": answers}
			st.success(f"You scored {score} out of {len(questions)}.")
			for question_number, (answer, item) in enumerate(zip(answers, questions), start=1):
				if answer == item["answer"]:
					st.write(f"{question_number}. Correct")
				else:
					st.write(f"{question_number}. Correct answer: **{item['answer']}**")
	elif "latest_quiz_result" in st.session_state:
		result = st.session_state.latest_quiz_result
		st.info(f"Your latest score: {result['score']} / {result['total']}")
	st.stop()

st.title("Online Quiz Performance Analytics")

demo_results = [
	{"result_id": "QZ-1001", "user_id": "U-101", "student": "Ava", "quiz": "Python Basics", "score": 9, "percentage": 90, "status": "Pass"},
	{"result_id": "QZ-1002", "user_id": "U-102", "student": "Noah", "quiz": "Python Basics", "score": 8, "percentage": 80, "status": "Pass"},
	{"result_id": "QZ-1003", "user_id": "U-103", "student": "Mia", "quiz": "Data Analytics", "score": 10, "percentage": 100, "status": "Pass"},
	{"result_id": "QZ-1004", "user_id": "U-104", "student": "Liam", "quiz": "Data Analytics", "score": 4, "percentage": 40, "status": "Fail"},
	{"result_id": "QZ-1005", "user_id": "U-101", "student": "Ava", "quiz": "Python Basics", "score": 6, "percentage": 60, "status": "Pass"},
]

mongo_uri = get_mongo_uri()
if not mongo_uri:
	st.warning(
		"Demo mode: showing sample quiz results because MongoDB is not configured. "
		"Set MONGODB_URI to load your real results."
	)
	results = demo_results
	using_demo_data = True
else:
	try:
		with MongoClient(mongo_uri, serverSelectionTimeoutMS=8000) as client:
			results = list(client["QuizDB"]["Results"].find({}, {"_id": 0}))
		using_demo_data = False
	except (OperationFailure, ValueError, TypeError) as exc:
		if isinstance(exc, OperationFailure) and (exc.code == 8000 or "auth" in str(exc).lower()):
			st.error(
				"MongoDB authentication failed. Check the database username and "
				"password in MONGODB_URI, and URL-encode any special characters "
				"in the password."
			)
		elif isinstance(exc, OperationFailure):
			st.error(f"MongoDB rejected the request: {exc}")
		else:
			st.error(f"Could not connect to MongoDB: {exc}")
		st.stop()
	except PyMongoError as exc:
		st.error(f"Could not connect to MongoDB: {exc}")
		st.stop()

df = pd.DataFrame(results)

if df.empty:
	st.info("The Results collection is reachable, but it contains no quiz results yet.")
	st.subheader("Quiz Results")
	st.dataframe(df, use_container_width=True)
	st.stop()

scores = coerce_numeric_series(df["score"]) if "score" in df else pd.Series(dtype="float64")
percentages = coerce_numeric_series(df["percentage"]) if "percentage" in df else pd.Series(dtype="float64")

average_score = scores.mean() if not scores.empty else float("nan")
highest_score = scores.max() if not scores.empty else float("nan")
average_percentage = percentages.mean() if not percentages.empty else float("nan")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Attempts", len(df))
col2.metric("Average Score", f"{average_score:.2f}" if pd.notna(average_score) else "—")
col3.metric("Highest Score", f"{highest_score:g}" if pd.notna(highest_score) else "—")
col4.metric(
	"Average Percentage",
	f"{average_percentage:.1f}%" if pd.notna(average_percentage) else "—",
)

if using_demo_data:
	st.caption("These sample values are for preview only; they are not read from MongoDB.")

st.subheader("Score Analysis")
if scores.notna().any():
	chart_data = pd.DataFrame({"Score": scores})
	if "result_id" in df:
		chart_data.index = df["result_id"].astype(str)
	st.bar_chart(chart_data)
else:
	st.info("No numeric score values are available to chart.")

st.subheader("Pass / Fail Analysis")
if "status" in df and df["status"].notna().any():
	status_counts = df["status"].dropna().astype(str).value_counts()
	st.bar_chart(status_counts)
else:
	st.info("Pass/fail analysis requires a 'status' field in the Results collection.")

st.subheader("Percentage Analysis")
if percentages.notna().any():
	percentage_chart = pd.DataFrame({"Percentage": percentages})
	if "result_id" in df:
		percentage_chart.index = df["result_id"].astype(str)
	st.bar_chart(percentage_chart)
else:
	st.info("No numeric percentage values are available to chart.")

st.subheader("Student Performance")
student_column = "user_id" if "user_id" in df else "student" if "student" in df else None
if student_column and scores.notna().any():
	student_scores = pd.DataFrame(
		{"student": df[student_column].astype(str), "score": scores}
	).dropna(subset=["score"])
	student_performance = student_scores.groupby("student")["score"].mean().sort_values(ascending=False)
	st.bar_chart(student_performance)
else:
	st.info("Student performance requires a 'user_id' (or 'student') field and numeric scores.")

st.subheader("Detailed Quiz Results")
st.dataframe(df, use_container_width=True)