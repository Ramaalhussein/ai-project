import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

CSV_PATH = r"C:\Users\pc\Desktop\uni\مشروع\data.csv"

def load_csv_data():
    try:
        # محاولة قراءة الملف بترميز utf-8-sig أولاً (يدعم BOM)
        try:
            df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
        except UnicodeDecodeError:
            # إذا فشل، جرب utf-16 ثم latin1
            try:
                df = pd.read_csv(CSV_PATH, encoding='utf-16')
            except:
                df = pd.read_csv(CSV_PATH, encoding='latin1')
        
        # تنظيف أسماء الأعمدة
        df.columns = df.columns.str.strip().str.lower()
        
        # التحقق من وجود الأعمدة المطلوبة
        required = ['question', 'answer']
        if not all(col in df.columns for col in required):
            available_cols = ", ".join(df.columns)
            raise ValueError(f"الأعمدة المطلوبة: {required}\nالأعمدة المتوفرة: {available_cols}")
        
        return df.dropna(subset=['question', 'answer'])
    
    except Exception as e:
        print(f"⚠️ خطأ في تحميل البيانات: {e}")
        # بيانات افتراضية للطوارئ
        return pd.DataFrame({
            'question': ['ما اسمك', 'كيف حالك', 'what is your name'],
            'answer': ['أنا المساعد الذكي', 'بخير الحمد لله', 'My name is AI Assistant']
        })

def find_answer(question):
    df = load_csv_data()
    if df.empty:
        return "قاعدة البيانات غير متوفرة حالياً"
    
    question = str(question).strip().lower()
    match = df[df['question'].str.lower().str.strip() == question]
    
    return match.iloc[0]['answer'] if not match.empty else "لا أعرف الإجابة"

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "يجب إرسال سؤال"}), 400
    
    question = data['question'].strip()
    if not question:
        return jsonify({"error": "السؤال لا يمكن أن يكون فارغاً"}), 400
    
    answer = find_answer(question)
    return jsonify({
        "question": question,
        "answer": answer,
        "source": "CSV" if "المساعد" not in answer else "default"
    })

if __name__ == '__main__':
    # اختبار التحميل عند التشغيل
    test_data = load_csv_data()
    print("\n📄 عينة من البيانات المحملة:")
    print(test_data.head(3))
    
    # تشغيل السيرفر
    print("\n🚀 تطبيق Flask جاهز على http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
