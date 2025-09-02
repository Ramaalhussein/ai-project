# -*- coding: utf-8 -*-
import sys
import os
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from gtts import gTTS
import platform

# ✅ إعداد الترميز بطريقة آمنة
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

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
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ الملف {file_path} غير موجود.")
    
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    if 'سؤال' not in df.columns or 'إجابة' not in df.columns:
        raise ValueError("❌ الملف يجب أن يحتوي على أعمدة 'سؤال' و'إجابة'.")
    
    data = [normalize_text(q) for q in df['سؤال']]
    vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
    tfidf_matrix = vectorizer.fit_transform(data)
    return df, vectorizer, tfidf_matrix

def play_audio(filename):
    """تشغيل ملف صوتي بناءً على نظام التشغيل"""
    system = platform.system()
    try:
        if system == "Windows":
            os.system(f"start {filename}")
        elif system == "Darwin":
            os.system(f"afplay {filename}")
        elif system == "Linux":
            os.system(f"mpg123 {filename}")
        else:
            print("🔇 لا يمكن تشغيل الصوت تلقائيًا على هذا النظام.")
    except Exception as e:
        print(f"⚠️ تعذر تشغيل الصوت: {e}")

def speak(text, filename="response.mp3"):
    """تحويل نص إلى صوت وتخزينه"""
    try:
        tts = gTTS(text=text, lang='ar')
        tts.save(filename)
        play_audio(filename)
    except Exception as e:
        print(f"⚠️ تعذر تحويل النص إلى صوت: {e}")

def get_answer(question, df, vectorizer, tfidf_matrix):
    """الحصول على الإجابة فقط"""
    if not isinstance(question, str):
        question = str(question)
    
    clean_q = normalize_text(question)

    # ✅ شرط مخصص لسؤال عن التخصصات بصيغة الجمع
    if "تخصصات" in clean_q and not re.search(r'\bتخصص\b', clean_q):
        return "💡 التخصصات لهذا المجال هي: نظم المعلومات، علوم الشبكات، علوم البرمجة، الذكاء الاصطناعي."

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
    
    print(f"\n💬 الإجابة: {answer}")
    speak(answer)

def load_model():
    """تحميل النموذج والبيانات لاستخدامها"""
    return load_and_prepare("data.csv")

# ============ تشغيل البرنامج ============
if __name__ == "__main__":
    try:
        df, vectorizer, tfidf_matrix = load_and_prepare("data.csv")
        print("✅ النظام جاهز. أدخل سؤالك أو 'خروج' لإنهاء.")
        while True:
            user_input = input("\n📥 سؤالك: ").strip()
            if user_input.lower() in ["خروج", "exit"]:
                print("👋 إلى اللقاء!")
                break
            match_question(user_input, df, vectorizer, tfidf_matrix)
            
    except FileNotFoundError as e:
        print(f"\n❌ خطأ: {e}")
        print("يرجى التأكد من وجود ملف data.csv في نفس مجلد البرنامج.")
    except Exception as e:
        print (f"\n[!] حدث خطأ غير متوقع: {e}")