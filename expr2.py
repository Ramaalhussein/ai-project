import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from gtts import gTTS
import platform
# -*- coding: utf-8 -*-
import sys
import io
import tempfile
import os
from pygame import mixer
sys.stdout.reconfigure(encoding='utf-8')
from  gtts import gTTS
def speak(text):
    """تحويل النص إلى صوت وتشغيله مباشرة من الذاكرة باستخدام pygame"""
    try:
        tts = gTTS(text=text, lang='ar', slow=False)
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as fp:
            temp_path = fp.name
            tts.save(temp_path)
        
        mixer.init()
        mixer.music.load(temp_path)
        mixer.music.play()
        
        while mixer.music.get_busy():
            pass
        
        mixer.quit()
        os.unlink(temp_path)
        
    except Exception as e:
        print(f"⚠️ خطأ في تشغيل الصوت: {e}")

def normalize_text(text):
    """تنظيف وتوحيد النص"""
    if not isinstance(text, str):
        text = str(text)
    text = re.sub(r'[^\w\s]', '', text)
    synonyms = {'مجال': 'تخصص', 'فرع': 'تخصص', 'it': 'تقنية المعلومات'}
    for word, rep in synonyms.items():
        text = re.sub(word, rep, text, flags=re.IGNORECASE)
    return text.strip().lower()

def load_and_prepare(file_path):
    """تحميل الأسئلة وتهيئة TF-IDF"""
    # التحقق من وجود الملف أولاً
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"الملف {file_path} غير موجود. يرجى التأكد من وجوده في المسار الصحيح.")
    
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    data = [normalize_text(q) for q in df['سؤال']]
    vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
    tfidf_matrix = vectorizer.fit_transform(data)
    return df, vectorizer, tfidf_matrix

def play_audio(filename):
    """تشغيل ملف صوتي بناءً على نظام التشغيل"""
    system = platform.system()
    if system == "Windows":
        os.system(f"start {filename}")
    elif system == "Darwin":  # macOS
        os.system(f"afplay {filename}")
    elif system == "Linux":
        os.system(f"mpg123 {filename}")
    else:
        print("🔇 لا يمكن تشغيل الصوت تلقائيًا على هذا النظام.")

def speak(text, filename="response.mp3"):
    """تحويل نص إلى صوت وتخزينه"""
    tts = gTTS(text=text, lang='ar')
    tts.save(filename)
    play_audio(filename)

def get_answer(question, df, vectorizer, tfidf_matrix):
    """الحصول على الإجابة فقط"""
    if not isinstance(question, str):
        question = str(question)
    
    clean_q = normalize_text(question)
    query_vec = vectorizer.transform([clean_q])
    similarities = cosine_similarity(query_vec, tfidf_matrix)
    best_idx = similarities.argmax()
    score = similarities[0][best_idx]

    if score > 0.4:
        return df.iloc[best_idx]['إجابة']
    else:
        return "عذرًا، لم أتمكن من العثور على إجابة دقيقة لهذا السؤال."

def match_question(user_question, df, vectorizer, tfidf_matrix):
    """مطابقة السؤال والرد عليه نصيًا وصوتيًا"""
    answer = get_answer(user_question, df, vectorizer, tfidf_matrix)
    
    if "عذرًا" not in answer:
        print(f"\n💡 الإجابة الأنسب: {answer}")
        speak(answer)
    else:
        print(f"\n❌ {answer}")
        speak(answer)

def load_model():
    """تحميل النموذج والبيانات لاستخدامها في Flask"""
    return load_and_prepare("data.csv")

# ============ تشغيل البرنامج ============
if __name__ == "__main__":
    try:
        # تحميل البيانات من الملف الصحيح data.csv
        df, vectorizer, tfidf_matrix = load_and_prepare("data.csv")
        
        print("🌟 نظام الإجابة على الأسئلة جاهز للاستخدام")
        while True:
            user_input = input("\n📥 أدخل سؤالك (أو 'خروج' لإنهاء): ").strip()
            if user_input.lower() in ["خروج", "exit"]:
                print("👋 تم إنهاء البرنامج، إلى اللقاء!")
                break
            match_question(user_input, df, vectorizer, tfidf_matrix)
            
    except FileNotFoundError as e:
        print(f"\n❌ خطأ: {e}")
        print("يرجى التأكد من:")
        print("1. وجود ملف data.csv في نفس مجلد البرنامج")
        print("2. أن اسم الملف مكتوب بشكل صحيح (data.csv)")
        print("3. أن الملف يحتوي على أعمدة 'سؤال' و'إجابة'")
    except Exception as e:
        print(f"\n❌ حدث خطأ غير متوقع: {e}")