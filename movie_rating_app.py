import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import os

# Initialize SQLite Database
engine = create_engine('sqlite:///ratings.db')

def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                movie TEXT,
                plot INTEGER,
                acting INTEGER,
                direction INTEGER,
                screenplay INTEGER,
                sound INTEGER,
                cinematography INTEGER,
                editing INTEGER,
                design INTEGER,
                emotion INTEGER,
                entertainment INTEGER,
                average REAL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

init_db()

# Set up session state
if "user" not in st.session_state:
    st.session_state["user"] = None

# Sidebar login
st.sidebar.title("🔐 Login")
username_input = st.sidebar.text_input("👤 Enter your username")
if username_input and st.sidebar.button("Login"):
    st.session_state["user"] = username_input
    st.success(f"Welcome to 🎥 Filmtopia, {username_input}!")

# Main App
if st.session_state["user"]:
    st.title("🎥 Filmtopia – Rate Your Favorite Movies")
    user = st.session_state["user"]

    criteria = ["Plot", "Acting", "Direction", "Screenplay", "Sound",
                "Cinematography", "Editing", "Design", "Emotion", "Entertainment"]

    with st.expander("🌟 Submit a New Rating"):
        movie = st.text_input("🎬 Movie Title")
        scores = [st.slider(f"⭐ {c}", 1, 10, 5) for c in criteria]
        comment = st.text_area("💬 Your Comment")
        if st.button("✅ Submit Rating") and movie:
            avg = round(sum(scores)/len(scores), 2)
            row = {
                "user": user,
                "movie": movie,
                **{criteria[i].lower(): scores[i] for i in range(10)},
                "average": avg,
                "comment": comment
            }
            pd.DataFrame([row]).to_sql("ratings", engine, if_exists="append", index=False)
            st.success("✅ Rating saved successfully!")
            st.subheader(f"🎯 Final Score: {avg} / 10")

            bar = px.bar(x=criteria, y=scores, labels={"x": "Criteria", "y": "Score"}, title="📊 Your Rating Breakdown")
            st.plotly_chart(bar)

            radar = go.Figure(data=go.Scatterpolar(r=scores, theta=criteria, fill='toself', name="Your Rating"))
            radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False)
            st.plotly_chart(radar)

    # View your ratings
    df_user = pd.read_sql(f"SELECT * FROM ratings WHERE user = :user", engine, params={"user": user})
    my_movies = df_user['movie'].unique().tolist()
    selected_movie = st.sidebar.selectbox("🎞 Select a Movie to View Your Rating", my_movies) if my_movies else None

    if selected_movie:
        st.subheader(f"🎞 Your Rating for: {selected_movie}")
        row = df_user[df_user["movie"] == selected_movie].iloc[-1]
        user_scores = [row[c.lower()] for c in criteria]
        st.write(f"📝 Comment: {row['comment']}")
        st.write(f"🎯 Final Score: {row['average']}")
        bar = px.bar(x=criteria, y=user_scores, labels={"x": "Criteria", "y": "Score"})
        st.plotly_chart(bar)

    # Global Stats
    with st.expander("📈 Overall Ratings from All Users"):
        df_all = pd.read_sql("SELECT movie, ROUND(AVG(average), 2) as avg_rating FROM ratings GROUP BY movie", engine)
        st.dataframe(df_all.rename(columns={"movie": "🎬 Movie", "avg_rating": "⭐ Avg Rating"}))
        st.bar_chart(df_all.set_index("movie"))
else:
    st.warning("🔐 Please log in from the sidebar to access the Filmtopia app.")
