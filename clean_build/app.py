import streamlit as st
from backend.game_logic import GameLogic

def initialize_game():
    if 'game' not in st.session_state:
        # Default settings
        word_length = 5
        subject = "General"
        mode = "Fun"
        st.session_state.game = GameLogic(word_length, subject, mode)
        st.session_state.messages = []

def main():
    st.title("Word Guessing Game 🎮")
    
    # Initialize game state
    initialize_game()
    
    # Sidebar for game settings
    with st.sidebar:
        st.header("Game Settings")
        if 'game' not in st.session_state or st.button("New Game"):
            word_length = st.selectbox("Word Length", options=[3, 4, 5, 6, 7, 8], index=2)
            subject = st.selectbox("Subject", options=["General", "Animals", "Food", "Places", "Science"], index=0)
            mode = st.selectbox("Game Mode", options=["Fun", "Challenge"], index=0)
            st.session_state.game = GameLogic(word_length, subject, mode)
            st.session_state.messages = []
            st.success("New game started!")

    # Main game area
    st.subheader("Ask yes/no questions to guess the word!")
    
    # Display previous questions and answers
    for msg in st.session_state.messages:
        with st.chat_message("user"):
            st.write(msg["question"])
        with st.chat_message("assistant"):
            st.write(msg["answer"])
            if "points_added" in msg and msg["points_added"] != 0:
                st.write(f"Points: {msg['points_added']}")

    # Question input
    question = st.chat_input("Ask a yes/no question about the word...")
    
    if question:
        is_valid, answer, points = st.session_state.game.ask_question(question)
        if is_valid:
            st.session_state.messages.append({
                "question": question,
                "answer": answer,
                "points_added": points
            })
        else:
            st.error(answer)  # Show error message if question is invalid

    # Guess input
    with st.container():
        guess = st.text_input("Make your guess:", key="guess_input")
        if st.button("Submit Guess"):
            if guess:
                is_correct, message, points = st.session_state.game.make_guess(guess)
                if is_correct:
                    st.balloons()
                    st.success(message)
                    # Show game summary
                    summary = st.session_state.game.get_game_summary()
                    st.json(summary)
                else:
                    st.error(message)
            else:
                st.warning("Please enter a guess first!")

    # Show current score in Challenge mode
    if st.session_state.game.mode == "Challenge":
        st.sidebar.metric("Current Score", st.session_state.game.score)

if __name__ == "__main__":
    main() 