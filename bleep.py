import streamlit as st
from audio_recorder_streamlit import audio_recorder
import openai
import base64
import time

# ----------------------- SETUP -----------------------
def setup_openai_client(api_key):
    return openai.OpenAI(api_key=api_key)

# -------------------- TRANSCRIBE ---------------------
def transcribe_audio(client, audio_path):
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
        return transcript.text

# -------------------- GET RESPONSE --------------------
def fetch_ai_responses(client, input_text):
    messages = [{"role": "user", "content": input_text}]
    response = client.chat.completions.create(
        model="gpt-4o", messages=messages
    )
    return response.choices[0].message.content

# ---------------------- TEXT TO AUDIO ----------------------
def text_to_audio(client, text, audio_path):
    response = client.audio.speech.create(
        model="tts-1", voice="nova", input=text
    )
    response.stream_to_file(audio_path)

# ------------------- AUTOPLAY AUDIO ---------------------
def auto_play_audio(audio_file):
    with open(audio_file, "rb") as af:
        audio_bytes = af.read()
    base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f"""
    <audio controls autoplay>
        <source src="data:audio/mp3;base64,{base64_audio}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# --------------------- TEXT CARD ----------------------
def create_text_card(text, title="Response"):
    card_html = f"""
    <style>
        .card {{
            background-color: #1f1f1f;
            color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }}
        .container {{
            padding: 5px 20px;
        }}
        .card h4 {{
            font-size: 1.3rem;
            margin-bottom: 10px;
            color: #4fc3f7;
        }}
    </style>
    <div class="card">
        <div class="container">
            <h4><b>{title}</b></h4>
            <p>{text}</p>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# ---------------------- MAIN -------------------------
def main():
    st.set_page_config(page_title="Bleep", layout="centered")
    st.markdown("""
        <style>
        body {{
            background-color: #121212;
            color: white;
        }}
        .pulse {{
            animation: pulse-animation 1.5s infinite;
        }}
        @keyframes pulse-animation {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.2); }}
            100% {{ transform: scale(1); }}
        }}
        .typing {{
            font-style: italic;
            color: #cccccc;
            margin-top: 5px;
        }}
        </style>
    """, unsafe_allow_html=True)

    st.title("✨ BleepAI ✨")
    st.write("Hello! Click on the voice recorder to interact with me. How can I assist you today?")

    api_key = st.sidebar.text_input("🔑 Enter your API Key", type="password")

    # Initialize session state for history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if api_key:
        client = setup_openai_client(api_key)

        # Pulse mic animation
        st.markdown('<div class="pulse">🎙️ Click to record</div>', unsafe_allow_html=True)
        recorded_audio = audio_recorder()

        if recorded_audio:
            audio_file = "audio.mp3"
            with open(audio_file, "wb") as f:
                f.write(recorded_audio)

            # Show transcription
            transcribed_text = transcribe_audio(client, audio_file)
            st.session_state.chat_history.append(("You", transcribed_text))

            # Show transcription card
            create_text_card(transcribed_text, "Transcribed Text")

            # AI Typing Animation
            typing_placeholder = st.empty()
            typing_placeholder.markdown('<div class="typing">AI is typing...</div>', unsafe_allow_html=True)
            time.sleep(1.5)

            # AI response
            ai_response = fetch_ai_responses(client, transcribed_text)
            typing_placeholder.empty()
            st.session_state.chat_history.append(("AI", ai_response))

            # TTS + Audio
            response_audio_file = "audio_response.mp3"
            text_to_audio(client, ai_response, response_audio_file)
            auto_play_audio(response_audio_file)

    # Render chat history (after interactions)
    for sender, message in st.session_state.chat_history:
        if sender == "You":
            create_text_card(message, "You Said")
        else:
            create_text_card(message, "AI Response")

if __name__ == "__main__":
    main()
