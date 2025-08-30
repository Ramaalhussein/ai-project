
from flask import Flask, render_template, request, send_file, jsonify
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file
from expr1 import load_model, get_answer, speak
import pandas as pd
import os

app = Flask(__name__)

# تحميل النموذج والبيانات عند بدء التطبيق
try:
    df, vectorizer, tfidf_matrix = load_model()
except FileNotFoundError as e:
    print(f"❌ ملف CSV غير موجود: {e}")
    print(f"المسار الحالي: {os.getcwd()}")
    exit()
except pd.errors.EmptyDataError:
    print("❌ ملف CSV فارغ أو تالف")
    exit()
except Exception as e:
    print(f"❌ خطأ غير متوقع في تحميل النموذج: {e}")
    exit()

@app.route('/', methods=['GET', 'POST'])
def home():
    answer = None
    audio_file = None
    
    if request.method == 'POST':
        question = request.form.get('question')
        if question:
            answer = get_answer(question, df, vectorizer, tfidf_matrix)
            audio_file = speak(answer)
    
    return render_template('prof.html', answer=answer, audio=audio_file)

@app.route('/play-audio/<expr1>')
def play_audio(expr1):
    filepath = os.path.join('static', expr1)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='audio/mpeg')
    return "الملف غير موجود", 404
@app.route('/api/voice', methods=['POST'])
def voice_api():
    data = request.get_json()
    voice_text = data.get('voiceText', '').strip()
    if not voice_text:
        return jsonify({"error": "لم يتم تقديم نص صوتي"}), 400

    answer = get_answer(voice_text, df, vectorizer, tfidf_matrix)
    audio_file = speak(answer)

    response = {"answer": answer}
    if audio_file:
        response["audio_url"] = f"/audio/{audio_file}"

    return jsonify(response)
@app.route('/api/text', methods=['POST'])
@app.route('/api/text', methods=['POST'])
def text_api():
    data = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({"error": "لم يتم تقديم سؤال"}), 400

    answer = get_answer(question, df, vectorizer, tfidf_matrix)
    audio_file = speak(answer)

    response = {"answer": answer}
    if audio_file:
        response["audio_url"] = f"/audio/{audio_file}"

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
