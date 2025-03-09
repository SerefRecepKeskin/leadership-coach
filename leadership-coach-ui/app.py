import streamlit as st
import requests
import uuid
from loguru import logger

# Oturum durumu başlat
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = []

# API ayarları
url = "http://localhost:5006/api/v1/chat/message"
headers = {"Content-Type": "application/json", "Accept": "application/json"}

# Başlık
st.header("AI Asistan ile Sohbet Et")

# Sohbet geçmişini göster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        logger.info(f"Displaying message with role: {message['role']}")
        # Show references if they exist and this is an assistant message
        if message["role"] == "bot_message" and "references" in message:
            with st.expander("References"):
                for ref in message["references"]:
                    ref_type = ref.get("type", "")
                    source = ref.get("source", "")
                    title = ref.get("title", source)
                    
                    if ref_type == "video":
                        st.write(f"📺 Video: [{title}]({source})")
                    elif ref_type == "web":
                        st.write(f"🌐 Web: [{title}]({source})")

# Kullanıcı girişi
user_input = st.chat_input("Mesajınızı buraya yazın...")
if user_input:
    # Kullanıcı mesajını ekrana yazdır
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    logger.info(f"User message with role 'user': {user_input}")

    # Backend'e istek gönder
    payload = {"user_message": user_input, "session_identifier": st.session_state.session_id}
    try:
        with st.spinner("Asistan düşünüyor..."):
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            logger.debug(f"Backend yanıtı: {response_data}")
            bot_message = response_data.get("bot_message", "Yanıt alınamadı.")

            # Yanıtı state'e ekle ve ekrana yazdır
            st.session_state.messages.append({
                "role": "bot_message", 
                "content": bot_message,
                "references": response_data.get("references", [])
            })
            with st.chat_message("bot_message"):
                st.markdown(bot_message)
                logger.info(f"Bot message with role 'bot_message': {bot_message}")
                # Show references for the new message
                if response_data.get("references"):
                    with st.expander("References"):
                        for ref in response_data["references"]:
                            ref_type = ref.get("type", "")
                            source = ref.get("source", "")
                            title = ref.get("title", source)
                            
                            if ref_type == "video":
                                st.write(f"📺 Video: [{title}]({source})")
                            elif ref_type == "web":
                                st.write(f"🌐 Web: [{title}]({source})")

            logger.info(f"Asistan mesajı: {bot_message}")

    except requests.exceptions.RequestException as e:
        error_message = f"Sunucu hatası: {str(e)}"
        st.session_state.messages.append({"role": "bot_message", "content": error_message})
        with st.chat_message("bot_message"):
            st.markdown(error_message)
        logger.error(f"Hata: {error_message}")

# Sohbeti sıfırlama
with st.sidebar:
    if st.button("Sohbeti Temizle"):
        st.session_state.messages = []
        st.success("Sohbet geçmişi temizlendi!")
        logger.info("Sohbet geçmişi temizlendi")