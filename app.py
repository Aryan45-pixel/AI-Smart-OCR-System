import streamlit as st
import numpy as np
import cv2
from PIL import Image, ImageDraw
import re

# Optional translation
try:
    from deep_translator import GoogleTranslator
    TRANS_AVAILABLE = True
except:
    TRANS_AVAILABLE = False

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Smart OCR System", layout="wide")
st.title("🚀 AI-Powered Smart Document & Vehicle OCR System")

# ---------------- SAFE OCR LOADER ----------------
@st.cache_resource
def load_reader(lang):
    import easyocr
    return easyocr.Reader(lang, gpu=False)

# ---------------- SIDEBAR ----------------
mode = st.sidebar.selectbox("Select Mode", ["Document OCR", "Vehicle OCR"])

# 🚫 Removed 'mr' (not supported by EasyOCR)
language = st.sidebar.multiselect("Select Languages", ['en', 'hi'], default=['en'])

# ---------------- UPLOAD ----------------
uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    try:
        image = Image.open(uploaded_file).convert("RGB")
        img_np = np.array(image)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📷 Uploaded Image")
            st.image(image, use_column_width=True)

        # ---------------- PREPROCESS ----------------
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # ---------------- OCR ----------------
        with st.spinner("🔍 Extracting text..."):
            try:
                reader = load_reader(language)
                results = reader.readtext(thresh)
            except Exception as e:
                st.error(f"OCR Error: {e}")
                st.stop()

        draw = ImageDraw.Draw(image)
        extracted_text = ""
        structured_data = {}

        for (bbox, text, prob) in results:
            color = "green" if prob > 0.7 else "red"

            draw.rectangle(
                [tuple(bbox[0]), tuple(bbox[2])],
                outline=color,
                width=3
            )

            extracted_text += f"{text} ({prob:.2f})\n"

            # ---------------- STRUCTURED DATA ----------------
            if re.search(r'\d{2}/\d{2}/\d{4}', text):
                structured_data["Date"] = text

            if re.search(r'₹?\d+', text):
                structured_data["Amount"] = text

            if mode == "Vehicle OCR":
                if re.match(r'[A-Z]{2}\d{2}[A-Z]{2}\d{4}', text):
                    structured_data["Vehicle Number"] = text

        # ---------------- OUTPUT ----------------
        with col2:
            st.subheader("📝 Extracted Text")
            st.text_area("Text", extracted_text, height=250)

            st.subheader("📊 Structured Data")
            st.json(structured_data)

            st.download_button(
                "⬇ Download Text",
                extracted_text,
                "ocr_output.txt"
            )

        # ---------------- IMAGE OUTPUT ----------------
        st.subheader("🔍 Detected Text Image")
        st.image(image, use_column_width=True)

        # ---------------- SEARCH ----------------
        st.subheader("🔎 Search in Text")
        search = st.text_input("Enter keyword")

        if search:
            matches = [
                line for line in extracted_text.split("\n")
                if search.lower() in line.lower()
            ]
            if matches:
                for m in matches:
                    st.success(m)
            else:
                st.warning("No match found")

        # ---------------- TRANSLATION ----------------
        if TRANS_AVAILABLE:
            st.subheader("🌍 Translate")
            if st.button("Translate to Hindi"):
                try:
                    translated = GoogleTranslator(source='auto', target='hi').translate(extracted_text)
                    st.write(translated)
                except:
                    st.error("Translation failed")

        # ---------------- 🔊 TEXT TO SPEECH (WORKS ONLINE) ----------------
        st.subheader("🔊 Text to Speech")

        if st.button("Speak Text"):
            if extracted_text.strip():
                # Browser-based speech (works on Streamlit Cloud)
                speech_code = f"""
                <script>
                var msg = new SpeechSynthesisUtterance(`{extracted_text}`);
                window.speechSynthesis.speak(msg);
                </script>
                """
                st.components.v1.html(speech_code)
            else:
                st.warning("No text to speak")

    except Exception as e:
        st.error(f"App Error: {e}")
