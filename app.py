import ssl
from flask import Flask, request, jsonify
from transformers import pipeline
import requests
from bs4 import BeautifulSoup
import easyocr
import base64
from io import BytesIO
from PIL import Image
import numpy as np

# BYPASS SSL
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 

print("System Status: Loading English AI Engines...")
classifier = pipeline("text-classification", model="vikram71198/distilroberta-base-finetuned-fake-news-detection")
image_classifier = pipeline('image-classification', model="prithivMLmods/Deep-Fake-Detector-v2-Model")
reader = easyocr.Reader(['en'], gpu=False)

# Specialized Scraper for Astronomy & General News
def get_verified_content(url):
    try:
        # User-Agent prevents being blocked by NASA/BBC/Space.com
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Remove "Clutter" (Navbars, sidebars, ads)
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
            
        # Target article body tags
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs[:6]]) 
        return content if len(content) > 60 else soup.title.string
    except: return "Error: Could not retrieve recent news content."

@app.route('/predict', methods=['POST'])
def predict_news():
    data = request.get_json()
    u_input = data.get('text', '')
    # Check if input is a URL (NASA, BBC, etc.) or raw text
    text = get_verified_content(u_input) if u_input.startswith('http') else u_input
    res = classifier(text[:512])[0]
    return jsonify({
        'label': "FAKE" if res['label'] == 'LABEL_1' else "REAL",
        'score': round(res['score'] * 100, 1),
        'extracted_text': text
    })

@app.route('/predict_image', methods=['POST'])
def predict_image():
    data = request.get_json()
    try:
        img = Image.open(BytesIO(base64.b64decode(data.get('image', '')))).convert("RGB")
        img_np = np.array(img)
        
        deep_res = image_classifier(img)[0]
        extracted = " ".join(reader.readtext(img_np, detail=0))
        
        text_verdict = "N/A"
        if extracted.strip():
            txt_res = classifier(extracted[:512])[0]
            text_verdict = "FAKE" if txt_res['label'] == 'LABEL_1' else "REAL"
            
        return jsonify({
            'deepfake_verdict': deep_res['label'].upper(),
            'extracted_text': extracted if extracted.strip() else "None",
            'text_verdict': text_verdict
        })
    except Exception as e: return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)