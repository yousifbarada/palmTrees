# rag_engine.py
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3-flash-preview")

def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def chunk_text(text, size=600, overlap=120):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start+size])
        start += size - overlap
    return chunks

class RAGSystem:
    def __init__(self, text_path):
        raw_text = load_data(text_path)
        self.chunks = chunk_text(raw_text)
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        
        embeddings = self.embedder.encode(self.chunks)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(np.array(embeddings))

        tokenized = [c.split() for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized)

    def retrieve(self, query, k=5):
        q_emb = self.embedder.encode([query])
        _, I = self.index.search(np.array(q_emb), k)
        faiss_docs = [self.chunks[i] for i in I[0]]

        bm25_scores = self.bm25.get_scores(query.split())
        top_bm25 = np.argsort(bm25_scores)[-k:]
        bm25_docs = [self.chunks[i] for i in top_bm25]

        return list(set(faiss_docs + bm25_docs))

    def _assess_severity(self, pest_prob, type_prob):
        avg_prob = (pest_prob + type_prob) / 2
        if avg_prob > 0.85: return "عالي جداً - خطر فوري"
        elif avg_prob > 0.70: return "عالي - يحتاج تدخل سريع"
        elif avg_prob > 0.50: return "متوسط - يحتاج مراقبة ومكافحة"
        else: return "منخفض - يحتاج مراقبة دورية"

    def generate(self, detection_result, tree_id=None):
        if isinstance(detection_result, dict):
            pest_info = detection_result.get('pest', {})
            type_info = detection_result.get('type', {})
            
            pest_label = pest_info.get('label', 'Unknown')
            pest_prob = pest_info.get('probability', 0)
            type_label = type_info.get('label', 'Unknown')
            type_prob = type_info.get('probability', 0)
            
            severity = self._assess_severity(pest_prob, type_prob)
            query = f"""
الأعراض المكتشفة:
- الفئة الرئيسية: {pest_label} (الثقة: {pest_prob*100:.1f}%)
- نوع المرض المحدد: {type_label} (الثقة: {type_prob*100:.1f}%)
- مستوى الشدة المتوقع: {severity}
- رقم الشجرة: {tree_id if tree_id else 'غير محدد'}
المطلوب:
تقديم تقرير تفصيلي شامل يغطي جميع جوانب هذا المرض.
"""
        else:
            query = f"تشخيص المرض: {detection_result}\nرقم الشجرة: {tree_id if tree_id else 'غير محدد'}"
    
        docs = self.retrieve(query, k=8)
        context = "\n\n".join(docs)

        prompt = f"""
أنت خبير زراعي متخصص بدرجة عالية في أمراض وآفات أشجار النخيل بمنطقة الشرق الأوسط.
📋 المعلومات المتوفرة:
{query}
📚 المراجع العلمية:
{context}
---
🔍 المطلوب:
قم بإعداد تقرير تشخيصي وعلاجي شامل وعملي بالعامية المصرية (فصحى ميسرة)...
[الرجاء الحفاظ على هيكل التعليمات الأصلية للبرومبت هنا]
"""
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ خطأ في توليد التقرير: {str(e)}"

def process_disease(detection_results, rag_system):
    reports = {}
    if isinstance(detection_results, dict):
        for tree_id, detection_info in detection_results.items():
            print(f"🌴 جاري معالجة شجرة النخيل رقم {tree_id}...")
            try:
                report = rag_system.generate(detection_result=detection_info, tree_id=tree_id)
                reports[tree_id] = report
                print(f"✅ تم إنشاء التقرير للشجرة {tree_id}")
            except Exception as e:
                print(f"❌ خطأ في معالجة الشجرة {tree_id}: {e}")
                reports[tree_id] = f"خطأ في المعالجة: {str(e)}"
    else:
        report = rag_system.generate(detection_result=detection_results, tree_id=1)
        reports[1] = report
    return reports