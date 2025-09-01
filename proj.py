# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file, jsonify
from expr1 import load_model, get_answer, speak
import pandas as pd
import os
from datetime import datetime

# تحديد مجلد static بشكل صريح
app = Flask(__name__, static_folder='static', static_url_path='/static')

# إنشاء مجلد static إذا لم يكن موجوداً
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    print(f"✅ تم إنشاء مجلد static: {static_dir}")

# تحميل النموذج والبيانات عند بدء التطبيق
try:
    df, vectorizer, tfidf_matrix = load_model()
    print("✅ تم تحميل النموذج بنجاح")
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
            audio_file = speak(answer, static_dir)
    
    return render_template('index.html', answer=answer, audio=audio_file)

@app.route('/audio/<filename>')
def serve_audio(filename):
    """خدمة ملفات الصوت من مجلد static"""
    try:
        filepath = os.path.join(static_dir, filename)
        
        # التحقق من وجود الملف
        if not os.path.exists(filepath):
            print(f"❌ ملف الصوت غير موجود: {filepath}")
            return jsonify({"error": "الملف غير موجود"}), 404
        
        # التحقق من أن الملف ضمن مجلد static للأمان
        if not filepath.startswith(static_dir):
            return jsonify({"error": "مسار غير مسموح"}), 403
            
        return send_file(filepath, mimetype='audio/mpeg')
        
    except Exception as e:
        print(f"❌ خطأ في خدمة الصوت: {e}")
        return jsonify({"error": f"خطأ في خدمة الصوت: {str(e)}"}), 500

@app.route('/api/voice', methods=['POST'])
def voice_api():
    """API لمعالجة الصوت"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "لم يتم تقديم بيانات JSON"}), 400
            
        voice_text = data.get('voiceText', '').strip()
        if not voice_text:
            return jsonify({"error": "لم يتم تقديم نص صوتي"}), 400

        answer = get_answer(voice_text, df, vectorizer, tfidf_matrix)
        audio_file = speak(answer, static_dir)

        response = {"answer": answer}
        if audio_file:
            response["audio_url"] = f"/audio/{audio_file}"

        return jsonify(response)
        
    except Exception as e:
        print(f"❌ خطأ في voice_api: {e}")
        return jsonify({"error": f"خطأ في المعالجة: {str(e)}"}), 500

@app.route('/api/text', methods=['POST'])
def text_api():
    """API لمعالجة النص"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "لم يتم تقديم بيانات JSON"}), 400
            
        question = data.get('question', '').strip()
        if not question:
            return jsonify({"error": "لم يتم تقديم سؤال"}), 400

        answer = get_answer(question, df, vectorizer, tfidf_matrix)
        audio_file = speak(answer, static_dir)

        response = {"answer": answer}
        if audio_file:
            response["audio_url"] = f"/audio/{audio_file}"

        return jsonify(response)
        
    except Exception as e:
        print(f"❌ خطأ في text_api: {e}")
        return jsonify({"error": f"خطأ في المعالجة: {str(e)}"}), 500

@app.route('/cleanup', methods=['POST'])
def cleanup_audio():
    """حذف ملفات الصوت القديمة (اختياري)"""
    try:
        # حذف الملفات الأقدم من 24 ساعة
        now = datetime.now()
        deleted_files = 0
        
        for filename in os.listdir(static_dir):
            if filename.endswith('.mp3'):
                filepath = os.path.join(static_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                if (now - file_time).total_seconds() > 86400:  # 24 ساعة
                    os.remove(filepath)
                    deleted_files += 1
        
        return jsonify({"message": f"تم حذف {deleted_files} ملف صوتي"})
        
    except Exception as e:
        return jsonify({"error": f"خطأ في التنظيف: {str(e)}"}), 500

# ✅ تشغيل التطبيق بمنفذ ديناميكي مناسب لـ Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
