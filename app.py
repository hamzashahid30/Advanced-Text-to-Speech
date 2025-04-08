import streamlit as st
import requests
import json
import os

# --- Configuration ---
ELEVEN_LABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVEN_LABS_VOICES_URL = "https://api.elevenlabs.io/v1/voices"
PLAY_HT_API_URL = "https://api.play.ht/api/v2/tts"
PLAY_HT_VOICES_URL = "https://api.play.ht/api/v2/voices"

# --- Helper Functions ---
def st_style(style_dict):
    style_str = ""
    for key, value in style_dict.items():
        style_str += f"{key}:{value};"
    return style_str

def load_voices_elevenlabs(api_key):
    headers = {
        "xi-api-key": api_key
    }
    try:
        response = requests.get(ELEVEN_LABS_VOICES_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        voices = {voice["name"]: voice["id"] for voice in data["voices"]}
        return voices
    except requests.exceptions.RequestException as e:
        st.error(f"Error loading ElevenLabs voices: {e}")
        return {}

def generate_audio_elevenlabs(api_key, text, voice_id, stability=0.5, similarity=0.75, style=0.0, model="eleven_multilingual_v2"):
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity,
            "style": style
        }
    }
    try:
        response = requests.post(ELEVEN_LABS_API_URL.format(voice_id=voice_id), headers=headers, json=payload, stream=True)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating ElevenLabs audio: {e}")
        return None

def load_voices_playht(api_key, user_id):
    headers = {
        "X-User-ID": user_id,
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.get(PLAY_HT_VOICES_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        voices = {f"{voice['name']} ({voice['language']})": voice["id"] for voice in data}
        return voices
    except requests.exceptions.RequestException as e:
        st.error(f"Error loading Play.ht voices: {e}")
        return {}

def generate_audio_playht(api_key, user_id, text, voice_id, speed=1.0, quality="premium"):
    headers = {
        "X-User-ID": user_id,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": [text],
        "voice": voice_id,
        "speed": speed,
        "quality": quality
    }
    try:
        response = requests.post(PLAY_HT_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if "url" in data and data["url"]:
            audio_url = data["url"]
            audio_response = requests.get(audio_url)
            audio_response.raise_for_status()
            return audio_response.content
        else:
            st.error(f"Error generating Play.ht audio: {data.get('message', 'No audio URL received')}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating Play.ht audio: {e}")
        return None

def display_api_status(api_key_eleven, api_key_playht, user_id_playht):
    st.subheader("API Status")
    eleven_status = "Error"
    playht_status = "Error"
    eleven_usage_limit = "Error"
    eleven_usage_used = "Error"
    eleven_usage_tier = "Error"

    if api_key_eleven:
        headers = {"xi-api-key": api_key_eleven}
        try:
            usage_response = requests.get("https://api.elevenlabs.io/v1/user", headers=headers)
            usage_response.raise_for_status()
            usage_data = usage_response.json()
            eleven_status = "OK"
            eleven_usage_limit = usage_data.get("subscription", {}).get("character_limit", "N/A")
            eleven_usage_used = usage_data.get("subscription", {}).get("character_count", "N/A")
            eleven_usage_tier = usage_data.get("subscription", {}).get("tier", "N/A")
        except requests.exceptions.RequestException as e:
            eleven_status = f"Error: {e}"

    if api_key_playht and user_id_playht:
        headers = {
            "X-User-ID": user_id_playht,
            "Authorization": f"Bearer {api_key_playht}"
        }
        try:
            response = requests.get("https://api.play.ht/api/v2/me", headers=headers)
            response.raise_for_status()
            playht_status = "OK"
            # You might need to parse the response to get usage details if Play.ht provides them in this endpoint.
            # This is a placeholder as the exact structure might differ.
            playht_usage = response.json().get("usage", "N/A")
            st.markdown(f"**Play.ht Usage:** `{playht_usage}`")
        except requests.exceptions.RequestException as e:
            playht_status = f"Error: {e}"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**ElevenLabs API Status:** `{eleven_status}`")
        st.markdown(f"**Limit:** `{eleven_usage_limit}`")
        st.markdown(f"**Used:** `{eleven_usage_used}`")
        st.markdown(f"**Tier:** `{eleven_usage_tier}`")
    with col2:
        st.markdown(f"**Play.ht API Status:** `{playht_status}`")
        # Add more Play.ht usage details here if available

def display_how_to_use():
    st.subheader("How to Use This Tool")
    st.markdown("""
    1.  **Enter API Keys:**
        * Click the settings icon (⚙️) in the sidebar.
        * Input your ElevenLabs API key and Play.ht API key and User ID.
        * Click "Save & Connect". Your keys are stored locally in your browser's session.

    2.  **Select Service & Configure:**
        * Choose either "ElevenLabs" or "Play.ht" from the radio buttons.
        * **ElevenLabs:**
            * Use the filters (Language, Gender) or the dropdown to find and select a voice.
            * Adjust **Stability**, **Similarity**, and **Style Exaggeration**.
            * Choose the desired **Generation Model**.
        * **Play.ht:**
            * Select a voice from the dropdown.
            * Adjust **Speed**.
            * Choose the **Quality**.

    3.  **Generate & Manage:**
        * Enter your text in the main text area.
        * Click the "Generate Audio" button.
        * The generated audio will appear in the "Generated Audio" section. You can listen to or download it.
        * Access, reload, or delete previous generations from the "History" list.

    """)

# --- Sidebar for Settings ---
with st.sidebar:
    st.header("⚙️ Settings")
    elevenlabs_api_key = st.text_input("ElevenLabs API Key", type="password")
    playht_api_key = st.text_input("Play.ht API Key", type="password")
    playht_user_id = st.text_input("Play.ht User ID")
    st.markdown("Your API keys are stored locally in your browser's session.")

# --- Main Application ---
st.title("Advanced Text-to-Speech")

display_api_status(elevenlabs_api_key, playht_api_key, playht_user_id)

tts_service = st.radio("Choose TTS Service:", ("ElevenLabs", "Play.ht"))

st.subheader("Text Input & Settings")
text_input = st.text_area("Enter Text:", height=150, placeholder="Type your text here...")

col_settings1, col_settings2 = st.columns(2)

generated_audio_placeholder = st.empty()
history_placeholder = st.empty()

if "audio_history" not in st.session_state:
    st.session_state["audio_history"] = []

if "eleven_voices" not in st.session_state:
    st.session_state["eleven_voices"] = {}

if "playht_voices" not in st.session_state:
    st.session_state["playht_voices"] = {}

if elevenlabs_api_key and not st.session_state["eleven_voices"]:
    st.session_state["eleven_voices"] = load_voices_elevenlabs(elevenlabs_api_key)

if playht_api_key and playht_user_id and not st.session_state["playht_voices"]:
    st.session_state["playht_voices"] = load_voices_playht(playht_api_key, playht_user_id)

with col_settings1:
    if tts_service == "ElevenLabs":
        st.subheader("ElevenLabs Voice Settings")
        language_filter = st.selectbox("Language Filter:", ["All"] + list(set([name.split()[0] for name in st.session_state["eleven_voices"]])))
        gender_filter = st.selectbox("Gender Filter:", ["All", "Male", "Female"])

        filtered_voices = ["Select a voice"]
        for name, _ in st.session_state["eleven_voices"].items():
            include = True
            if language_filter != "All" and not name.startswith(language_filter):
                include = False
            if gender_filter != "All":
                if gender_filter == "Male" and "(male)" not in name.lower():
                    include = False
                if gender_filter == "Female" and "(female)" not in name.lower():
                    include = False
            if include:
                filtered_voices.append(name)

        selected_eleven_voice_name = st.selectbox("Voices:", filtered_voices)
        selected_eleven_voice_id = st.session_state["eleven_voices"].get(selected_eleven_voice_name)

        stability = st.slider("Stability", 0.0, 1.0, 0.5, 0.01, help="Higher = consistent, Lower = expressive.")
        similarity = st.slider("Similarity", 0.0, 1.0, 0.75, 0.01, help="Higher = closer to original voice.")
        style_exagg = st.slider("Style Exagg.", 0.0, 1.0, 0.0, 0.01, help="(V2 models) Higher = more pronounced style.")
        model = st.selectbox("Model", ["eleven_multilingual_v2", "eleven_multilingual_v1", "eleven_english_v1", "eleven_turbo_v2"])

    elif tts_service == "Play.ht":
        st.subheader("Play.ht Voice Settings")
        playht_voice_options = ["Select a voice"] + list(st.session_state["playht_voices"].keys())
        selected_playht_voice_name = st.selectbox("Voices:", playht_voice_options)
        selected_playht_voice_id = st.session_state["playht_voices"].get(selected_playht_voice_name)
        speed = st.slider("Speed", 0.5, 2.0, 1.0, 0.1)
        quality = st.selectbox("Quality", ["premium", "standard", "fast"])

with col_settings2:
    st.subheader("Text Settings")
    emphasis_placeholder = st.empty() # Placeholder for future emphasis controls
    rate_placeholder = st.empty()     # Placeholder for future rate controls
    pitch_placeholder = st.empty()    # Placeholder for future pitch controls
    char_count = st.markdown(f"Character Count: **{len(text_input)}**")

st.subheader("Output & History")
col_generate, col_clear = st.columns([3, 1])
with col_generate:
    if st.button("Generate Audio"):
        if text_input:
            if tts_service == "ElevenLabs" and elevenlabs_api_key and selected_eleven_voice_id:
                audio_bytes = generate_audio_elevenlabs(elevenlabs_api_key, text_input, selected_eleven_voice_id, stability, similarity, style_exagg, model)
                if audio_bytes:
                    st.session_state["audio_history"].append(("ElevenLabs", selected_eleven_voice_name, text_input, audio_bytes))
            elif tts_service == "Play.ht" and playht_api_key and playht_user_id and selected_playht_voice_id:
                audio_bytes = generate_audio_playht(playht_api_key, playht_user_id, text_input, selected_playht_voice_id, speed, quality)
                if audio_bytes:
                    st.session_state["audio_history"].append(("Play.ht", selected_playht_voice_name, text_input, audio_bytes))
            elif not elevenlabs_api_key and tts_service == "ElevenLabs":
                st.error("Please enter your ElevenLabs API key in the settings.")
            elif not (playht_api_key and playht_user_id) and tts_service == "Play.ht":
                st.error("Please enter your Play.ht API key and User ID in the settings.")
            elif selected_eleven_voice_id == "Select a voice" and tts_service == "ElevenLabs":
                st.warning("Please select an ElevenLabs voice.")
            elif selected_playht_voice_id == "Select a voice" and tts_service == "Play.ht":
                st.warning("Please select a Play.ht voice.")
        else:
            st.warning("Please enter some text to generate speech.")

with col_clear:
    if st.button("Clear All History"):
        st.session_state["audio_history"] = []

st.subheader("Generated Audio")
if st.session_state["audio_history"]:
    latest_generation = st.session_state["audio_history"][-1]
    service, voice_name, text, audio_bytes = latest_generation
    st.markdown(f"**Service:** {service}")
    st.markdown(f"**Voice:** {voice_name}")
    st.markdown(f"**Text:** {text}")
    st.audio(audio_bytes, format="audio/mpeg")
else:
    st.info("Audio will appear here.")

st.subheader("History")
if st.session_state["audio_history"]:
    for i, (service, voice_name, text, audio_bytes) in enumerate(reversed(st.session_state["audio_history"])):
        with st.expander(f"Generation {len(st.session_state['audio_history']) - i} ({service} - {voice_name})"):
            st.markdown(f"**Text:** {text}")
            st.audio(audio_bytes, format="audio/mpeg")
else:
    st.info("No history yet.")

display_how_to_use()

st.markdown("---")
st.markdown("© 2024-2025 Learn with Faizen & Muddasir Zeb. All rights reserved.")
st.markdown("Powered by ElevenLabs API & Play.ht API")
