import streamlit as st
import requests

# ایپ کا عنوان
st.title("Advanced Text-to-Speech")

# ٹیبز بنائیں
tab1, tab2 = st.tabs(["ElevenLabs API", "Play.ht API"])

# ElevenLabs API کے لیے ٹیب 1 کی تفصیلات
with tab1:
    st.header("ElevenLabs API کی تفصیلات")
    st.markdown("""
        **ElevenLabs API** ایک طاقتور ٹیکسٹ ٹو اسپیچ سروس فراہم کرتا ہے جو وائس کلوننگ، سٹائل کی تبدیلی، اور رفتار کی تخصیص جیسے فیچرز فراہم کرتا ہے۔
    """)
    st.text_area("API کی تفصیلات یہاں شامل کریں", key="elevenlabs_details")
    elevenlabs_api_key = st.text_input("ElevenLabs API Key", type="password")
    if elevenlabs_api_key:
        st.success("API Key محفوظ ہو گئی ہے!")

# Play.ht API کے لیے ٹیب 2 کی تفصیلات
with tab2:
    st.header("Play.ht API کی تفصیلات")
    st.markdown("""
        **Play.ht API** ایک اور مضبوط ٹیکسٹ ٹو اسپیچ سروس ہے جو وائس کلوننگ، سٹائل کی تبدیلی، اور رفتار کی تخصیص کی اجازت دیتا ہے۔
    """)
    st.text_area("API کی تفصیلات یہاں شامل کریں", key="playht_details")
    playht_api_key = st.text_input("Play.ht API Key", type="password")
    if playht_api_key:
        st.success("API Key محفوظ ہو گئی ہے!")

# API کے ذریعے اسپچ بنانے کا فنکشن
def generate_speech(api_key, text, voice_id, service="elevenlabs"):
    if service == "elevenlabs":
        url = "https://api.elevenlabs.io/v1/text-to-speech/stream"
    elif service == "playht":
        url = "https://play.ht/api/v1/convert"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "voice_id": voice_id,
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        audio_data = response.content
        return audio_data
    else:
        st.error("API کال میں مسئلہ آیا: " + response.text)
        return None

