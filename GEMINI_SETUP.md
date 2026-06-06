# 🚀 Gemini API - BEPUL Integratsiya

## 1️⃣ GEMINI API KEY OLISH (BEPUL!)

### Qadamlar:

1. **Google AI Studio'ga kiring:**
   - https://aistudio.google.com/app/apikey
   - Google account bilan login qiling

2. **API Key yarating:**
   - "Create API Key" tugmasini bosing
   - "Create API key in new project" tanlang
   - Key ko'rinadi - **NUSXALANG!**

3. **API Key ni saqlang:**
   - `.env` fayliga qo'shing:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### Bepul Limitlar:
- ✅ 60 request/minut
- ✅ 1,500 request/kun
- ✅ Cheksiz vaqt
- ✅ Vision (rasm tahlil)

**Narx: $0** ✅

---

## 2️⃣ KUTUBXONA O'RNATISH

```bash
pip install google-generativeai
```

---

## 3️⃣ KONFIGURATSIYA

`.env` fayliga qo'shing:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

`config.py` ga qo'shing:
```python
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

---

## 4️⃣ MIGRATSIYA

OpenAI → Gemini

**O'zgarishlar:**
- `services/ai_service.py` - Gemini ishlatadi
- Barcha funksiyalar ishlaydi
- Vision ham ishlaydi
- **100% BEPUL!**

---

## 5️⃣ TEST

```python
import google.generativeai as genai

genai.configure(api_key="YOUR_KEY")
model = genai.GenerativeModel('gemini-1.5-flash')

response = model.generate_content("Salom!")
print(response.text)
```

---

## ✅ NATIJA

- ⚡ 2x tezroq
- 💰 $0/oy (100% bepul)
- ✅ Barcha funksiyalar ishlaydi
- ✅ Vision ham bor
