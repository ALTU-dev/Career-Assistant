# main.py — Career Development Assistant ALT University | GEMINI 2.5 FLASH + HH.KZ AUTO-RESUME
import telebot
import google.generativeai as genai
from telebot import types
import json
import os
import requests
import time
import re
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from datetime import datetime

# === ТОКЕНЫ ===
TELEGRAM_TOKEN = "your_telegram_token"
GEMINI_API_KEY = "your_gemini_key"
HH_TOKEN = "your_hh_token"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    generation_config=genai.GenerationConfig(
        max_output_tokens=2000,
        temperature=0.9
    )
)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === ПЕРСИСТЕНТНОЕ ХРАНИЛИЩЕ ===
DATA_FILE = "users_data.json"
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

USER_DATA = load_data()

# === Клавиатура ===
menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
menu.add("👤 Мой профиль", "📊 Карьерный план")
menu.add("📄 Резюме", "💼 Найти работу")
menu.add("🎤 Собеседование", "🔥 Топ вакансии")
menu.add("📤 Опубликовать на HH.kz")  # НОВАЯ КНОПКА

@bot.message_handler(commands=['start'])
def start(m):
    user_id = str(m.from_user.id)
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"profile": {}, "history": [], "hh_resume_id": None}
        save_data(USER_DATA)
    bot.send_message(m.chat.id,
        "🎓 Сәлем! Мен ALT University карьерный ассистентімін\n\n"
        "✅ Профиль толтыр → резюме дайын\n"
        "✅ Нақты вакансиялар табамын\n"
        "✅ HH.kz-ға автоматты жарияламын\n"
        "✅ Барлық деректер сақталады!",
        reply_markup=menu)

# Функция для экранирования Markdown символов (V1)
def escape_md(text):
    if not text:
        return text
    for char in '*_`[':
        text = text.replace(char, '\\' + char)
    return text

# === УНИВЕРСАЛЬНАЯ ФУНКЦИЯ GEMINI ===
def gemini(prompt, user_id=None):
    try:
        # Добавляем историю для контекста
        if user_id:
            history = USER_DATA.get(str(user_id), {}).get("history", [])
            if history:
                context = "\n".join(history[-3:]) # последние 3 сообщения
                prompt = f"Контекст:\n{context}\n\nЗапрос: {prompt}"
        response = model.generate_content(
            prompt,
            stream=False,
            safety_settings=[
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE
                }
            ]
        )
        # Проверяем, есть ли текст в ответе
        if not response.text:
            return "⚠️ Gemini не смог сгенерировать ответ. Попробуйте переформулировать запрос или повторите позже."
        # Сохраняем в историю
        if user_id:
            USER_DATA[str(user_id)]["history"].append(f"Q: {prompt[:100]}...")
            USER_DATA[str(user_id)]["history"].append(f"A: {response.text[:100]}...")
            save_data(USER_DATA)
        return response.text
    except ValueError as e:
        # Это ошибка блокировки контента
        return "⚠️ Gemini уақытша жауап бере алмады. Сұрақты өзгертіп көріңіз немесе кейінірек қайталаңыз."
    except Exception as e:
        return f"⚠️ Қате: {str(e)}\n\nҚайта көріңіз (5-10 секундтан кейін)..."

# === ПРОФИЛЬ ===
@bot.message_handler(func=lambda m: m.text == "👤 Мой профиль")
def profile1(m):
    user_id = str(m.from_user.id)
    # Если профиль уже есть — можно предложить обновить, но для простоты всегда перезаполняем
    msg = bot.send_message(m.chat.id, "👤 Толық аты-жөніңізді жазыңыз (тек әріптер):\n(Мысалы: Аскар Сейдуллаев)")
    bot.register_next_step_handler(msg, profile_name)

def profile_name(m):
    if not m.text:
        msg = bot.send_message(m.chat.id, "⚠️ Тек мәтін жіберіңіз! Аты-жөніңізді қайта жазыңыз:")
        bot.register_next_step_handler(msg, profile_name)
        return
    text = m.text.strip()
    # Разрешаем буквы, пробелы, дефисы (кириллица и латиница)
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁәӘіІңҢғҒүҮұҰқҚөӨһҺ\s-]+$", text):
        msg = bot.send_message(m.chat.id, "❌ Аты-жөніңізде тек әріптер, пробел және дефис болуы керек!\nҚайта жазыңыз:")
        bot.register_next_step_handler(msg, profile_name)
        return
    user_id = str(m.from_user.id)
    USER_DATA[user_id]["profile"]["name"] = text
    save_data(USER_DATA)
    msg = bot.send_message(m.chat.id, "📚 Курс + факультет?\n(Мысал: 3 курс, IT факультеті)")
    bot.register_next_step_handler(msg, profile_course)

def profile_course(m):
    if not m.text:
        msg = bot.send_message(m.chat.id, "⚠️ Тек мәтін жіберіңіз!")
        bot.register_next_step_handler(msg, profile_course)
        return
    user_id = str(m.from_user.id)
    USER_DATA[user_id]["profile"]["course"] = m.text.strip()
    save_data(USER_DATA)
    msg = bot.send_message(m.chat.id, "📧 Email адресіңіз?\n(Мысал: student@alt.edu.kz)")
    bot.register_next_step_handler(msg, profile_email)

def profile_email(m):
    if not m.text:
        msg = bot.send_message(m.chat.id, "⚠️ Тек мәтін жіберіңіз!")
        bot.register_next_step_handler(msg, profile_email)
        return
    text = m.text.strip()
    # Простая, но эффективная проверка email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", text):
        msg = bot.send_message(m.chat.id, "❌ Дұрыс email жазыңыз!\nМысалы: name@example.com\nҚайта жазыңыз:")
        bot.register_next_step_handler(msg, profile_email)
        return
    user_id = str(m.from_user.id)
    USER_DATA[user_id]["profile"]["email"] = text
    save_data(USER_DATA)
    msg = bot.send_message(m.chat.id, "📱 Телефон номеріңіз?\n(Мысал: +77771234567 немесе +7 777 123 45 67)")
    bot.register_next_step_handler(msg, profile_phone)

def profile_phone(m):
    if not m.text:
        msg = bot.send_message(m.chat.id, "⚠️ Тек мәтін жіберіңіз!")
        bot.register_next_step_handler(msg, profile_phone)
        return
    text = m.text.strip()
    # Разрешаем +, цифры, пробелы и дефисы
    cleaned = re.sub(r"[+\d\s-]", "", text)
    if cleaned or not text: # если после очистки остались символы — ошибка
        msg = bot.send_message(m.chat.id, "❌ Телефонда тек сандар, +, пробел және дефис болуы керек!\nМысал: +77771234567\nҚайта жазыңыз:")
        bot.register_next_step_handler(msg, profile_phone)
        return
    # Extract digits
    digits = re.sub(r'\D', '', text)
    # Check if starts with +7 and has exactly 11 digits starting with 7
    if not text.startswith('+7') or len(digits) != 11 or not digits.startswith('7'):
        msg = bot.send_message(m.chat.id, "❌ Номер +7-ден басталуы керек және номер дұрыс жазыңыз!\nМысал: +77771234567\nҚайта жазыңыз:")
        bot.register_next_step_handler(msg, profile_phone)
        return
    user_id = str(m.from_user.id)
    USER_DATA[user_id]["profile"]["phone"] = text
    save_data(USER_DATA)
    msg = bot.send_message(m.chat.id, " Сіздің біліктіліктеріңізді үтірмен бөліп енгізіңіз:\n(Мысалы: Python, AutoCAD, Электротехника негіздері, Жоба менеджменті, Телекоммуникация жүйелері, Қаржы талдауы, Кадастрлық жұмыстар, Энергетика жүйелері)")
    bot.register_next_step_handler(msg, profile_skills)
def profile_skills(m):
    if not m.text:
        msg = bot.send_message(m.chat.id, "⚠️ Тек мәтін жіберіңіз!")
        bot.register_next_step_handler(msg, profile_skills)
        return
    skills_text = m.text.strip()
    skills = [s.strip() for s in skills_text.split(",") if s.strip()]
    if len(skills) == 0:
        msg = bot.send_message(m.chat.id, "❌ Кем дегенде бір навык жазыңыз!\nҮтірмен бөліп қайта жазыңыз:")
        bot.register_next_step_handler(msg, profile_skills)
        return
    user_id = str(m.from_user.id)
    USER_DATA[user_id]["profile"]["skills"] = skills
    save_data(USER_DATA)
    msg = bot.send_message(m.chat.id, "🎯 Қандай мамандыққа/позицияға қызығасыз?\n(Мысалы: IT, Энергетика, Менеджмент, Маркетинг)")
    bot.register_next_step_handler(msg, profile_target)

def profile_target(m):
    if not m.text:
        msg = bot.send_message(m.chat.id, "⚠️ Тек мәтін жіберіңіз!")
        bot.register_next_step_handler(msg, profile_target)
        return
    text = m.text.strip()
    if not text:
        msg = bot.send_message(m.chat.id, "❌ Позицияны міндетті түрде жазыңыз!\nҚайта жазыңыз:")
        bot.register_next_step_handler(msg, profile_target)
        return
    user_id = str(m.from_user.id)
    USER_DATA[user_id]["profile"]["target"] = text
    save_data(USER_DATA)
    # Теперь запрашиваем дополнительные данные для HH.kz
    msg = bot.send_message(m.chat.id, "🎂 Туған жылыңыз?\n(Мысалы: 2002)")
    bot.register_next_step_handler(msg, profile_birth_year)

def profile_birth_year(m):
    if not m.text:
        msg = bot.send_message(m.chat.id, "⚠️ Тек мәтін жіберіңіз!")
        bot.register_next_step_handler(msg, profile_birth_year)
        return
    text = m.text.strip()
    if not re.match(r"^\d{4}$", text) or int(text) < 1950 or int(text) > 2010:
        msg = bot.send_message(m.chat.id, "❌ Дұрыс жыл жазыңыз (1950-2010)!\nҚайта жазыңыз:")
        bot.register_next_step_handler(msg, profile_birth_year)
        return
    user_id = str(m.from_user.id)
    USER_DATA[user_id]["profile"]["birth_year"] = text
    save_data(USER_DATA)
   
    # Запрашиваем пол
    gender_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=True)
    gender_keyboard.add("👨 Ер адам", "👩 Әйел")
    msg = bot.send_message(m.chat.id, "👤 Жынысыңыз?", reply_markup=gender_keyboard)
    bot.register_next_step_handler(msg, profile_gender)

def profile_gender(m):
    if not m.text:
        msg = bot.send_message(m.chat.id, "⚠️ Тек мәтін жіберіңіз!")
        bot.register_next_step_handler(msg, profile_gender)
        return
    user_id = str(m.from_user.id)
    if "Ер" in m.text or "👨" in m.text:
        USER_DATA[user_id]["profile"]["gender"] = "male"
    else:
        USER_DATA[user_id]["profile"]["gender"] = "female"
    save_data(USER_DATA)
   
    msg = bot.send_message(m.chat.id, "🏙️ Қай қалада тұрасыз?\n(Мысалы: Алматы)", reply_markup=menu)
    bot.register_next_step_handler(msg, profile_city)

def profile_city(m):
    if not m.text:
        msg = bot.send_message(m.chat.id, "⚠️ Тек мәтін жіберіңіз!")
        bot.register_next_step_handler(msg, profile_city)
        return
    user_id = str(m.from_user.id)
    USER_DATA[user_id]["profile"]["city"] = m.text.strip()
    save_data(USER_DATA)
   
    # Финальное подтверждение
    p = USER_DATA[user_id]["profile"]
    summary = f"✅ *Профиль сәтті сақталды!*\n\n" \
              f"👤 {escape_md(p.get('name', '-'))}\n" \
              f"📚 {escape_md(p.get('course', '-'))}\n" \
              f"📧 {escape_md(p.get('email', '-'))}\n" \
              f"📱 {escape_md(p.get('phone', '-'))}\n" \
              f"💪 {', '.join([escape_md(s) for s in p.get('skills', ['-'])])}\n" \
              f"🎯 {escape_md(p.get('target', '-'))}\n" \
              f"🎂 {escape_md(p.get('birth_year', '-'))}\n" \
              f"👤 Жыныс: {'Ер адам' if p.get('gender') == 'male' else 'Әйел'}\n" \
              f"🏙️ {escape_md(p.get('city', '-'))}\n\n" \
              f"📤 Енді «Опубликовать на HH.kz» басып резюме жариялай аласыз!"
    bot.send_message(m.chat.id, summary, parse_mode="Markdown", reply_markup=menu)

# === КАРЬЕРНЫЙ ПЛАН ===
@bot.message_handler(func=lambda m: m.text == "📊 Карьерный план")
def plan(m):
    user_id = str(m.from_user.id)
    p = USER_DATA.get(user_id, {}).get("profile", {})
    if not p.get("name"):
        bot.send_message(m.chat.id, "⚠️ Алдымен профиль толтырыңыз!")
        return
    skills = ", ".join(p.get("skills", ["жоқ"]))
    target = p.get("target", "IT маман")
    # ТОЧНЫЙ И КРАСИВЫЙ ПРОМПТ (поместить вместо старого prompt в этой функции)
    prompt = f"""ALT University студенті үшін Қазақстандағы еңбек нарығы трендтерін ескере отырып, персонализацияланған карьерлік жоспар құр. 
Студент деректері: 
👤 Аты: {p['name']} 
📚 Курс/Факультет: {p.get('course', 'студент')} 
💪 Дағдылар: {skills} 
🎯 Карьерлік мақсат: {target}

Жоспарды келесі құрылым бойынша құр (KPI-лерді ескер: еңбекке орналасу деңгейін 15-20% арттыру, студент қанағаттануын 20-25% көтеру, консультанттардың жүктемесін 40-50% төмендету):
1. **Ұқсас мамандықтар (3 ұсыныс)**: Әрбірі үшін сәйкестік пайызын (%-бен), себептерін және Қазақстандағы сұранысты (зарплата, трендтер) көрсет.
2. **Жетіспейтін дағдылар (3-5)**: Үйрену үшін платформалар ұсын (Coursera, Udemy, Stepik, Step Academy, тегін ресурстар сияқты).
3. **Нақты қадамдар (2025-2026 жж.)**: Тоқсан сайын SMART-мақсаттармен (өлшенетін, қолжетімді, уақыттық) жоспарла.
4. **Стажировка ұсыныстары (2-3)**: Компания атауы, Қазақстандағы сілтемелер (hh.kz немесе сайттар), студент деңгейіне сәйкес.
5. **Learning Path (6 ай жоспар)**: Апта сайын тапсырмалар, прогресс бақылауы, сертификат ұсыныстары.

Қазақша жаз, эмодзи қосып, мотивирлейтін және тартымды стильде. Markdown-да форматта (тізімдер, жирный текст). Жауапты 1500 таңбаға дейін шекте, бірақ толық қамты. Нарық трендтерін (IT цифрландыру, жасыл экономика) ескер."""
    bot.send_message(m.chat.id, "📊 Карьерный жоспар дайындалуда...")
    try:
        result = gemini(prompt, user_id)
        if not result or "error" in result.lower(): # Проверка на пустой или ошибочный ответ
            bot.send_message(m.chat.id, "⚠️ Жоспарды генерациялауда қате кетті. Қайта көріңіз немесе профиліңізді жаңартыңыз!")
        else:
            bot.send_message(m.chat.id, escape_md(result), parse_mode="Markdown")
    except Exception as e:
        bot.send_message(m.chat.id, f"⚠️ Қате: {str(e)}. Қайта көріңіз (5-10 секунд күтіңіз)!")

# === РЕЗЮМЕ ===
@bot.message_handler(func=lambda m: m.text == "📄 Резюме")
def resume(m):
    user_id = str(m.from_user.id)
    p = USER_DATA.get(user_id, {}).get("profile", {})
    if not p.get("name"):
        bot.send_message(m.chat.id, "⚠️ Алдымен профиль толтырыңыз!")
        return
    # ТОЧНЫЙ И КРАСИВЫЙ ПРОМПТ (поместить вместо старого prompt в этой функции)
    prompt = f"""ALT University студенті үшін Қазақстандық еңбек нарығына сәйкес персонализацияланған түйіндеме (резюме) және ілеспе хат (сопроводительное письмо) құр.
Студент деректері: 
👤 {p['name']} 
📧 {p.get('email', 'email@example.com')} 
📱 {p.get('phone', '+7 775 123 45 67')} 
📚 {p.get('course', 'IT студент')} 
💪 Дағдылар: {', '.join(p.get('skills', []))} 
🎯 Позиция: {p.get('target', 'IT маман')}

Түйіндеме (қазақша/орысша):
- **Қысқаша сипаттама (Summary)**: 3-4 жол, күшті жақтарды және мақсатты көрсет.
- **Байланыс деректері (Contacts)**: Email, телефон, LinkedIn (болмаса, өткіз).
- **Дағдылар (Skills)**: Категориялар бойынша топтастыр (техникалық, soft skills).
- **Тәжірибе/Жобалар (Experience/Projects)**: Реалистік, студент деңгейіне сәйкес (болмаса, оқу жобаларын қос).
- **Білім (Education)**: Университет, факультет, курс.

Ілеспе хат (қазақша, 150 сөз, кәсіби стильде):
- Компанияға қызығушылықты көрсет.
- Үлес қосу мүмкіндігін сипатта.
- Мотивация мен мақсатты ескер.

Қазақша жаз, эмодзи қосып, тартымды ет. Markdown-да форматта (тізімдер, таблица). Нарық трендтерін ескер (персонализация, автоматизация). Жауапты 1500 таңбаға дейін шекте."""
    bot.send_message(m.chat.id, "📄 Резюме дайындалуда...")
    try:
        result = gemini(prompt, user_id)
        # Сохраняем резюме
        USER_DATA[user_id]["resume"] = result
        save_data(USER_DATA)
        if not result or "error" in result.lower(): # Проверка на пустой или ошибочный ответ
            bot.send_message(m.chat.id, "⚠️ Резюмені генерациялауда қате кетті. Қайта көріңіз немесе профиліңізді жаңартыңыз!")
        else:
            bot.send_message(m.chat.id, escape_md(result), parse_mode="Markdown")
            bot.send_message(m.chat.id, "✅ Резюме профильде сақталды! Енді «💼 Найти работу» басыңыз")
    except Exception as e:
        bot.send_message(m.chat.id, f"⚠️ Қате: {str(e)}. Қайта көріңіз (5-10 секунд күтіңіз)!")

# === УНИВЕРСАЛЬНЫЙ ПОИСК ВАКАНСИЙ ДЛЯ ВСЕХ СПЕЦИАЛЬНОСТЕЙ ===
@bot.message_handler(func=lambda m: m.text == "💼 Найти работу")
def find_jobs(m):
    user_id = str(m.from_user.id)
    p = USER_DATA.get(user_id, {}).get("profile", {})
    
    if not p.get("skills") or not p.get("target"):
        bot.send_message(m.chat.id, "⚠️ Алдымен профиль толық толтырыңыз (навыктар + мақсат керек)!")
        return
    # Создаем клавиатуру для вопроса об опыте
    experience_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=True)
    experience_keyboard.add("✅ Иә (бар)", "❌ Жоқ (жоқ)")
    msg = bot.send_message(m.chat.id, "💼 Жұмыс тәжірибеңіз бар ма? (Иә/Жоқ)", reply_markup=experience_keyboard)
    bot.register_next_step_handler(msg, process_experience, m.chat.id)

def process_experience(m, chat_id):
    user_id = str(m.from_user.id)
    p = USER_DATA.get(user_id, {}).get("profile", {})
    
    experience_choice = m.text.strip()
    has_experience = None
    
    if "Иә" in experience_choice or "бар" in experience_choice.lower():
        has_experience = True
        bot.send_message(chat_id, "✅ Тәжірибе бар деп есептейміз (1-3 жылға дейін іздейміз)...")
    elif "Жоқ" in experience_choice or "жоқ" in experience_choice.lower():
        has_experience = False
        bot.send_message(chat_id, "❌ Тәжірибе жоқ - стажер/начинающий вакансиялар іздейміз...")
    else:
        bot.send_message(chat_id, "⚠️ Дұрыс таңдаңыз: Иә немесе Жоқ.")
        find_jobs(m) # Повторяем вопрос
        return
    bot.send_message(chat_id, "🔍 Сіздің резюмеңіз бойынша вакансияларды іздеуде...", reply_markup=menu)
    
    try:
        skills = p.get("skills", [])
        target = p.get("target", "")
        course = p.get("course", "")
        
        all_vacancies = []
        seen_ids = set()
        
        headers = {
            "User-Agent": "ALT University Career Bot (career@alt.edu.kz)"
        } # Убрали Authorization
        
        # === ИНТЕЛЛЕКТУАЛЬНАЯ СТРАТЕГИЯ ПОИСКА ===
        search_queries = []
        
        # 1. АНАЛИЗ ПОЗИЦИИ - извлекаем ключевые слова
        target_lower = target.lower()
        target_words = re.findall(r'\b\w{3,}\b', target_lower) # слова от 3 букв
        
        # Основной поиск по позиции
        search_queries.append(target)
        
        # 2. ОПРЕДЕЛЯЕМ КАТЕГОРИЮ СПЕЦИАЛЬНОСТИ через Gemini
        # ТОЧНЫЙ И КРАСИВЫЙ ПРОМПТ (поместить вместо старого category_prompt)
        category_prompt = f"""ALT University студентінің карьерлік мақсатын бір сөзбен (орысша) категорияла: IT, Маркетинг, Финансы, HR, Продажи, Дизайн, Логистика, Медицина, Юриспруденция, Образование, Производство немесе басқа. 
Позиция: {target} 
Навыктар: {', '.join(skills[:3])} 
Курс: {course}
Жауап: ТЕК бір сөз! Нарық трендтерін ескер (Қазақстандағы сұранысты)."""
        
        category = gemini(category_prompt, user_id).strip()
        bot.send_message(chat_id, f"🎯 Категория: {escape_md(category)}")
        
        # 3. ФОРМИРУЕМ ПОИСКОВЫЕ ЗАПРОСЫ ПО КАТЕГОРИЯМ
        
        # Универсальные слова для поиска entry-level позиций
        junior_keywords = ["junior", "стажер", "помощник", "ассистент", "младший", "начинающий"]
        
        # Добавляем ключевые слова из позиции
        for word in target_words[:2]: # берем 2 главных слова
            if len(word) > 3:
                search_queries.append(word)
        
        # Добавляем навыки как поисковые запросы
        for skill in skills[:3]:
            search_queries.append(skill)
        
        # Добавляем комбинации для студентов
        if any(junior in target_lower for junior in junior_keywords):
            search_queries.append(f"{target_words[0] if target_words else target}")
        else:
            # Если не указан уровень - ищем entry-level
            search_queries.append(f"junior {target_words[0] if target_words else target}")
            search_queries.append(f"стажер {target_words[0] if target_words else target}")
        
        # 4. КАТЕГОРИЙНЫЕ ДОПОЛНИТЕЛЬНЫЕ ЗАПРОСЫ
        category_searches = {
            "IT": ["разработчик", "developer", "программист", "аналитик", "тестировщик"],
            "Маркетинг": ["маркетолог", "smm", "контент", "реклама", "digital"],
            "Финансы": ["бухгалтер", "финансист", "аудитор", "экономист"],
            "HR": ["hr", "рекрутер", "персонал", "кадры"],
            "Продажи": ["продажи", "sales", "менеджер", "торговый"],
            "Дизайн": ["дизайнер", "designer", "графический", "веб-дизайн"],
            "Логистика": ["логист", "закупки", "снабжение", "склад"],
            "Медицина": ["медицинский", "врач", "медсестра", "фармацевт"],
            "Юриспруденция": ["юрист", "правовой", "legal", "адвокат"],
            "Образование": ["учитель", "преподаватель", "педагог", "образование"],
            "Производство": ["инженер", "технолог", "производство", "конструктор"]
        }
        
        # Добавляем категорийные запросы
        for cat_key, cat_words in category_searches.items():
            if cat_key.lower() in category.lower():
                search_queries.extend(cat_words[:3])
                break
        
        # Убираем дубликаты
        search_queries = list(dict.fromkeys(search_queries))[:8] # максимум 8 запросов
        
        bot.send_message(chat_id, f"🔄 Поиск по {len(search_queries)} запросам...\n({', '.join(search_queries[:4])}...)")
        
        # ... (начало функции process_experience без изменений)

        # Определяем параметр experience для API
        experience_param = None
        if has_experience is False:
            experience_param = "noExperience"
        elif has_experience is True:
            experience_param = "between1And3" # Предполагаем junior уровень для студентов с опытом
        # === ВЫПОЛНЯЕМ ПОИСК ===
        for query in search_queries:
            # Базовые параметры
            params = {
                "text": query,
                "area": 160,  # Изменено: Алматы (было 40 для всего Казахстана)
                "per_page": 50,
                "search_field": ["name", "description"],
            }
            if experience_param:
                params["experience"] = experience_param
            
            try:
                response = requests.get("https://api.hh.kz/vacancies",
                                      params=params,
                                      headers=headers,
                                      timeout=15)
                data = response.json()
                
                if data.get("items"):
                    for v in data["items"]:
                        if v['id'] not in seen_ids:
                            seen_ids.add(v['id'])
                            all_vacancies.append(v)
                
                time.sleep(0.3) # задержка
            except:
                continue
        
        # === ДОПОЛНИТЕЛЬНЫЙ ПОИСК БЕЗ ОПЫТА ===
        if len(all_vacancies) < 10 and has_experience is False:
            bot.send_message(chat_id, "🔄 Кеңейтемін іздеуді (без опыта)...")
            
            no_exp_params = {
                "area": 160,  # Изменено: Алматы (было 40 для всего Казахстана)
                "experience": "noExperience",
                "per_page": 50,
                "text": target_words[0] if target_words else target
            }
            
            try:
                response = requests.get("https://api.hh.kz/vacancies",
                                      params=no_exp_params,
                                      headers=headers,
                                      timeout=15)
                data = response.json()
                
                if data.get("items"):
                    for v in data["items"]:
                        if v['id'] not in seen_ids:
                            seen_ids.add(v['id'])
                            all_vacancies.append(v)
            except:
                pass

# ... (остальной код без изменений)
        # === ДОПОЛНИТЕЛЬНЫЙ ПОИСК БЕЗ ОПЫТА ===
        if len(all_vacancies) < 10 and has_experience is False:
            bot.send_message(chat_id, "🔄 Кеңейтемін іздеуді (без опыта)...")
            
            no_exp_params = {
                "area": 40,
                "experience": "noExperience",
                "per_page": 50,
                "text": target_words[0] if target_words else target
            }
            
            try:
                response = requests.get("https://api.hh.kz/vacancies",
                                      params=no_exp_params,
                                      headers=headers,
                                      timeout=15)
                data = response.json()
                
                if data.get("items"):
                    for v in data["items"]:
                        if v['id'] not in seen_ids:
                            seen_ids.add(v['id'])
                            all_vacancies.append(v)
            except:
                pass
        
        # === ЕСЛИ НИЧЕГО НЕ НАЙДЕНО ===
        if not all_vacancies:
            # ТОЧНЫЙ И КРАСИВЫЙ ПРОМПТ (поместить вместо старого suggestion_prompt)
            suggestion_prompt = f"""ALT University студенті вакансия таппай қалды. Қазақша 3 нақты кеңес бер: 
Позиция: {target} 
Навыктар: {', '.join(skills)}
Құрылым:
1. Іздеу сұрауын қалай өзгерту керек (2-3 нақты мысал)?
2. Қандай жақын позицияларды қарауға болады (3-4 атау, Қазақстан нарығына сәйкес)?
3. Профильге қандай дағдылар қосу керек (2-3 ұсыныс, трендтерге сүйен)?
Қысқа, мотивирлейтін, эмодзи қосып. Markdown-да форматта."""
            
            suggestions = gemini(suggestion_prompt, user_id)
            
            bot.send_message(chat_id,
                f"😔 Қазір вакансия табылмады\n\n"
                f"🔍 *Іздеген:*\n"
                f"• {escape_md(target)}\n"
                f"• {', '.join([escape_md(s) for s in skills[:5]])}\n\n"
                f"💡 *КЕҢЕСТЕР:*\n{escape_md(suggestions)}",
                parse_mode="Markdown")
            return
        
        bot.send_message(chat_id, f"✅ Табылды: {len(all_vacancies)} вакансия. AI іріктеуде...")
        
        # === УМНАЯ ФИЛЬТРАЦИЯ ЧЕРЕЗ GEMINI ===
        vacancies_sample = all_vacancies[:25] # увеличили до 25
        
        brief_list = []
        for i, v in enumerate(vacancies_sample, 1):
            emp = v.get('employer', {}).get('name', 'Компания')
            exp = v.get('experience', {}).get('name', 'Не указано')
            area = v.get('area', {}).get('name', '')
            brief_list.append(f"{i}. {v['name']} | {emp} | {area} | Опыт: {exp}")
        
        # ТОЧНЫЙ И КРАСИВЫЙ ПРОМПТ (поместить вместо старого filter_prompt)
        filter_prompt = f"""ALT University студентінің профиліне сәйкес вакансияларды ірікте. 
Профиль: 
Мақсат: {target} 
Навыктар: {', '.join(skills)} 
Курс: {course} 
Категория: {category}

ВАКАНСИЯЛАР ({len(brief_list)}): 
{chr(10).join(brief_list)}

Міндет: 10-12 ЕҢ ҮЗДІК вакансияны таңда. 
Критериялар (ҚАЗАҚСТАН НАРЫҒЫНА СҮЙЕН):
✅ Навыктар толық немесе ішінара сәйкес.
✅ Junior/стажер/entry-level (тәжірибе аз немесе жоқ).
✅ Студентке қолжетімді (оқумен үйлестіру мүмкіндігі).
✅ Компанияның карьералық перспективасы бар.
✅ Навыктар сәйкес болса, позиция жақын болуы мүмкін (мысалы, Data Analyst үшін Junior Developer - жарайды, егер Python бар болса).

Жауап: ТЕК номерлер үтірмен (мысалы: 1,3,5,7,9,11,13,15,17,20,22,25). Ең сәйкестерді басымдық бер."""
        
        gemini_response = gemini(filter_prompt, user_id)
        
        # Парсим номера
        try:
            numbers = re.findall(r'\d+', gemini_response)
            selected_indices = [int(n) - 1 for n in numbers if 0 < int(n) <= len(vacancies_sample)]
            
            if not selected_indices or len(selected_indices) < 5:
                selected_indices = list(range(min(10, len(vacancies_sample))))
        except:
            selected_indices = list(range(min(10, len(vacancies_sample))))
        
        selected_vacancies = [vacancies_sample[i] for i in selected_indices]
        
        # === ФОРМИРУЕМ РЕЗУЛЬТАТЫ ===
        vacancies = []
        for v in selected_vacancies:
            salary_info = "Көрсетілмеген"
            if v.get('salary'):
                sal = v['salary']
                curr = sal.get('currency', 'KZT')
                if sal.get('from') and sal.get('to'):
                    salary_info = f"{sal['from']:,} - {sal['to']:,} {curr}"
                elif sal.get('from'):
                    salary_info = f"{sal['from']:,}+ {curr}"
                elif sal.get('to'):
                    salary_info = f"{sal['to']:,}-ке дейін {curr}"
            
            vacancies.append({
                "title": escape_md(v['name']),
                "company": escape_md(v.get('employer', {}).get('name', 'Компания')),
                "salary": salary_info, # '-' не проблема в V1
                "area": escape_md(v.get('area', {}).get('name', 'Қазақстан')),
                "url": v['alternate_url'],
                "experience": escape_md(v.get('experience', {}).get('name', 'Көрсетілмеген')),
                "employment": escape_md(v.get('employment', {}).get('name', 'Толық жұмыс күні'))
            })
        
        # === ВЫВОД ТОП-5 ===
        result_text = f"📊 *AI ІРІКТЕУІ: {len(vacancies)} вакансия*\n"
        result_text += f"🎯 {escape_md(target)}\n"
        result_text += f"💪 {', '.join([escape_md(s) for s in skills[:3]])}\n"
        result_text += f"📍 {escape_md(category)}\n\n"
        result_text += "🔝 *ТОП-5:*\n\n"
        
        for i, v in enumerate(vacancies[:5], 1):
            result_text += f"*{i}. {v['title']}*\n"
            result_text += f"🏢 {v['company']}\n"
            result_text += f"💰 {v['salary']}\n" # '-' ок
            result_text += f"📍 {v['area']} | 💼 {v['experience']}\n"
            result_text += f"🔗 [Өтінім беру]({v['url']})\n\n"
        
        bot.send_message(chat_id, result_text, parse_mode="Markdown", disable_web_page_preview=True)
        
        # === ДЕТАЛЬНЫЙ АНАЛИЗ ===
        analysis_data = "\n".join([
            f"{i+1}. {v['title']} - {v['company']}\n {v['area']} | Опыт: {v['experience']} | ЗП: {v['salary']}"
            for i, v in enumerate(vacancies[:5])
        ])
        
        # ТОЧНЫЙ И КРАСИВЫЙ ПРОМПТ (поместить вместо старого analysis_prompt)
        analysis_prompt = f"""ALT University студентінің профиліне сәйкес ТОП-5 вакансияны талда. 
Студент: 👤 {escape_md(p.get('name', 'Студент'))} 📚 {escape_md(course)} 💪 {', '.join([escape_md(s) for s in skills])} 🎯 {escape_md(target)} 📍 {escape_md(category)}

ТОП-5: 
{analysis_data}

Әр вакансияға қысқа талдау (4-5 жол):
* N. Вакансия аты *
• Сәйкестік: XX% - себебі (нақты 4-5 сөз, навыктарға сүйен).
• Плюстар: 2-3 артықшылық (компания, зарплата, өсу).
• Үйрену керек: 1-2 дағды (немесе "Дайынсыз" / "Базалық жеткілікті").
• Ұсыныс: ✅ Қазір өтінім беріңіз / ⏳ 1-2 ай үйреніңіз / 📚 Курстан кейін.

Қазақша, нақты, эмодзи қосып, мотивирлейтін. Markdown-да форматта."""
        
        bot.send_message(chat_id, "🧠 AI детальды талдап жатыр...")
        analysis = gemini(analysis_prompt, user_id)
        bot.send_message(chat_id, f"📊 *ДЕТАЛЬДЫ ТАЛДАУ:*\n\n{escape_md(analysis)}", parse_mode="Markdown")
        
        # === ҚАЛҒАН ВАКАНСИЯЛАР ===
        if len(vacancies) > 5:
            more_text = f"\n📌 *Басқа {len(vacancies)-5} вакансия:*\n\n"
            for i, v in enumerate(vacancies[5:], 6):
                more_text += f"*{i}. {v['title']}*\n"
                more_text += f"🏢 {v['company']} | 💰 {v['salary']}\n"
                more_text += f"📍 {v['area']} | 🔗 [Сілтеме]({v['url']})\n\n"
            
            bot.send_message(chat_id, more_text, parse_mode="Markdown", disable_web_page_preview=True)
        
        # === ИТОГОВАЯ СТАТИСТИКА + РЕКОМЕНДАЦИИ ===
        # ТОЧНЫЙ И КРАСИВЫЙ ПРОМПТ (поместить вместо старого final_prompt)
        final_prompt = f"""ALT University студенті үшін іздеу нәтижесіне негізделген 2-3 нақты кеңес бер. 
Табылды: {len(all_vacancies)} вакансия 
Іріктелді: {len(vacancies)} 
Позиция: {target} 
Категория: {category}

Кеңестер (қазақша, қысқа):
1. Навыктарды қалай жақсарту (1-2 ұсыныс, трендтерге сүйен: IT цифрландыру, жасыл технологиялар).
2. Жақын позициялар (2-3 атау, Қазақстан нарығына сәйкес).
3. Профильді жақсарту (1 нақты идея: сертификат, портфолио).

Эмодзи қосып, мотивирлейтін стильде. Markdown-да форматта."""
        
        recommendations = gemini(final_prompt, user_id)
        
        bot.send_message(chat_id,
            f"📈 *СТАТИСТИКА:*\n"
            f"• Жалпы: {len(all_vacancies)} вакансия\n"
            f"• AI іріктеді: {len(vacancies)}\n"
            f"• Ұсыныс: ТОП-3 вакансияға өтінім беріңіз\n\n"
            f"💡 *КЕҢЕСТЕР:*\n{escape_md(recommendations)}",
            parse_mode="Markdown")
        
    except requests.exceptions.Timeout:
        bot.send_message(chat_id, "⏱️ HH.KZ жауап бермеді. 10 секундтан кейін қайталаңыз...")
    except requests.exceptions.RequestException as e:
        bot.send_message(chat_id, f"❌ Интернет қатесі: {str(e)}\n\nҚайта байланыс орнатылуда...")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Қате орын алды: {str(e)}\n\nҚайталап көріңіз немесе профильді тексеріңіз.")

# === СОБЕСЕДОВАНИЕ ===
@bot.message_handler(func=lambda m: m.text == "🎤 Собеседование")
def interview(m):
    user_id = str(m.from_user.id)
    p = USER_DATA.get(user_id, {}).get("profile", {})
    # ТОЧНЫЙ И КРАСИВЫЙ ПРОМПТ (поместить вместо старого question = gemini(...))
    question_prompt = f"""ALT University студенті үшін {p.get('target', 'IT маман')} позициясына реалистік HR сұрақ құр. 
Қазақстандық компаниялар стилінде (Kaspi, Halyk сияқты), қазақша. 
Навыктарды ескер: {', '.join(p.get('skills', []))}. 
Жауап: ТЕК сұрақ! Нақты және кәсіби."""
    question = gemini(question_prompt, user_id)
    msg = bot.send_message(m.chat.id, f"🎤 *СОБЕСЕДОВАНИЕ ТРЕНИНГІ*\n\n{escape_md(question)}\n\n✍️ Жауапты жазыңыз:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, interview_feedback)

def interview_feedback(m):
    user_id = str(m.from_user.id)
    # ТОЧНЫЙ И КРАСИВЫЙ ПРОМПТ (поместить вместо старого prompt в этой функции)
    prompt = f"""ALT University студентінің сұхбат жауабын бағала, Қазақстандық HR ретінде (Kaspi.kz стилінде). 
Жауап: {m.text}

Баға құрылымы (қазақша):
* Балл: X/10 (нақты себеппен) *
* Күшті жақтары: 2-3 пункт (эмодзи қосып).
* Әлсіз жақтары: 2-3 пункт (конструктивті).
* Жақсарту кеңесі: Нақты 1-2 идея (мысалдармен).

Мотивирлейтін және қолдаушы стильде. Markdown-да форматта."""
    feedback = gemini(prompt, user_id)
    bot.send_message(m.chat.id, escape_md(feedback), parse_mode="Markdown")

# === ТОП ВАКАНСИИ ===
@bot.message_handler(func=lambda m: m.text == "🔥 Топ вакансии")
def top_jobs(m):
    # ТОЧНЫЙ И КРАСИВЫЙ ПРОМПТ (поместить вместо старого prompt в этой функции)
    prompt = f"""2025-2026 жылдардағы Қазақстан еңбек нарығындағы топ-7 жоғары төлемді мамандықтарды сипатта (ALT University контекстінде, трендтер: цифрландыру, жасыл экономика). 
Құрылым:
1. Мамандық атауы + орташа жалақы (KZT, нақты сандармен).
2. Неге сұранысты? (2-3 себеп, статистикаға сүйен).
3. Негізгі дағдылар (3-5, үйрену ұсыныстарымен).

Қазақша, қысқа, эмодзи қосып, мотивирлейтін. Markdown-да форматта (тізімдер). Жауапты толық, бірақ 1000 таңбаға дейін шекте."""
    result = gemini(prompt, str(m.from_user.id))
    bot.send_message(m.chat.id, escape_md(result), parse_mode="Markdown")

# === ПРОСМОТР ПРОФИЛЯ ===
@bot.message_handler(commands=['profile'])
def view_profile(m):
    user_id = str(m.from_user.id)
    p = USER_DATA.get(user_id, {}).get("profile", {})
    if not p:
        bot.send_message(m.chat.id, "⚠️ Профиль толтырылмаған!")
        return
    summary = f"👤 *ПРОФИЛЬ*\n\n" \
              f"Аты: {escape_md(p.get('name', '-'))}\n" \
              f"Курс: {escape_md(p.get('course', '-'))}\n" \
              f"📧 Email: {escape_md(p.get('email', '-'))}\n" \
              f"📱 Телефон: {escape_md(p.get('phone', '-'))}\n" \
              f"Навыки: {', '.join([escape_md(s) for s in p.get('skills', ['-'])])}\n" \
              f"Мақсат: {escape_md(p.get('target', '-'))}\n" \
              f"🎂 {escape_md(p.get('birth_year', '-'))}\n" \
              f"👤 Жыныс: {'Ер адам' if p.get('gender') == 'male' else 'Әйел'}\n" \
              f"🏙️ {escape_md(p.get('city', '-'))}"
    bot.send_message(m.chat.id, summary, parse_mode="Markdown")

# === НОВАЯ ФУНКЦИЯ: ПУБЛИКАЦИЯ НА HH.KZ ===
@bot.message_handler(func=lambda m: m.text == "📤 Опубликовать на HH.kz")
def publish_to_hh(m):
    user_id = str(m.from_user.id)
    p = USER_DATA.get(user_id, {}).get("profile", {})
    
    # Проверяем наличие всех обязательных полей
    required_fields = ["name", "email", "phone", "skills", "target", "birth_year", "gender", "city"]
    missing = [f for f in required_fields if not p.get(f)]
    
    if missing:
        bot.send_message(m.chat.id,
            f"⚠️ Профиль толық емес!\n\n"
            f"Жетіспейтін деректер:\n" +
            "\n".join([f"• {escape_md(f)}" for f in missing]) +
            "\n\n👤 «Мой профиль» басып толтырыңыз!",
            parse_mode="Markdown")
        return
    
    bot.send_message(m.chat.id, "📤 HH.kz-ға резюме жариялауда...\n⏳ Күтіңіз...")
    
    try:
        # Получаем area_id для города
        area_id = get_area_id(p.get("city", "Алматы"))
        
        # Формируем данные резюме
        resume_data = create_resume_data(p, area_id)
        
        # Отправляем на HH.kz
        result = upload_to_hh(resume_data, user_id)
        
        if result["success"]:
            bot.send_message(m.chat.id,
                f"✅ *РЕЗЮМЕ СӘТТІ ЖАРИЯЛАНДЫ!*\n\n"
                f"🔗 Сілтеме: {escape_md(result['url'])}\n"
                f"📋 ID: {escape_md(result['resume_id'])}\n\n"
                f"💡 Енді сіз:\n"
                f"• Резюмені HH.kz-да көре аласыз\n"
                f"• Вакансияларға өтінім бере аласыз\n"
                f"• Работодательдер сізді таба алады",
                parse_mode="Markdown")
        else:
            bot.send_message(m.chat.id,
                f"❌ Қате орын алды:\n{escape_md(result['error'])}\n\n"
                f"💡 Себептері:\n"
                f"• API токен жарамсыз\n"
                f"• Деректер дұрыс емес\n"
                f"• HH.kz қолжетімсіз\n\n"
                f"🔄 Кейінірек қайталап көріңіз немесе тех.қолдауға жазыңыз.",
                parse_mode="Markdown")
    
    except Exception as e:
        bot.send_message(m.chat.id,
            f"❌ Жүйелік қате: {escape_md(str(e))}\n\n"
            f"Администраторға хабарласыңыз.",
            parse_mode="Markdown")

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ HH.KZ ===
def get_area_id(city_name):
    """Получает ID города из HH.kz API"""
    try:
        # Словарь популярных городов Казахстана
        cities = {
            "алматы": 160,
            "астана": 162,
            "нур-султан": 162,
            "шымкент": 164,
            "караганда": 165,
            "актобе": 166,
            "тараз": 167,
            "павлодар": 168,
            "усть-каменогорск": 169,
            "семей": 170,
            "атырау": 171,
            "костанай": 172,
            "кызылорда": 173,
            "уральск": 174,
            "петропавловск": 175,
            "актау": 176,
            "темиртау": 177,
            "туркестан": 178,
            "кокшетау": 179,
            "талдыкорган": 180,
            "экибастуз": 181,
            "рудный": 182,
            "жанаозен": 183,
            "балхаш": 184,
            "сатпаев": 185,
            "жезказган": 186,
            "аркалык": 187,
            "кентау": 188,
            "риддер": 189,
            "жаркент": 190,
            "каскелен": 191,
            "капшагай": 192
        }
        
        city_lower = city_name.lower().strip()
        if city_lower in cities:
            return cities[city_lower]
        
        # Если не нашли в словаре, ищем через API
        response = requests.get(
            "https://api.hh.kz/areas",
            headers={"User-Agent": "ALT University Career Bot"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Ищем Казахстан (ID 40)
            for country in data:
                if country['id'] == '40': # Казахстан
                    for area in country.get('areas', []):
                        if city_lower in area['name'].lower():
                            return int(area['id'])
        
        # По умолчанию возвращаем Алматы
        return 160
    
    except:
        return 160 # Алматы по умолчанию

def create_resume_data(profile, area_id):
    """Формирует данные резюме для HH.kz API"""
    
    # Разбиваем ФИО
    name_parts = profile['name'].split()
    first_name = name_parts[0] if len(name_parts) > 0 else "Имя"
    last_name = name_parts[-1] if len(name_parts) > 1 else "Фамилия"
    middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else None
    
    # Формируем дату рождения
    birth_date = f"{profile['birth_year']}-01-01"
    
    # Генерируем описание через Gemini
    description_prompt = f"""Напиши короткое профессиональное описание (2-3 предложения) для резюме на русском языке для студента:
Позиция: {profile.get('target', 'Специалист')}
Навыки: {', '.join(profile.get('skills', []))}
Курс: {profile.get('course', 'студент')}
Сделай акцент на мотивации, обучаемости и готовности к работе."""
    text = gemini(description_prompt)
    
    # Формируем навыки
    skill_set = profile.get("skills", [])
    
    resume_data = {
        "first_name": first_name,
        "last_name": last_name,
        "middle_name": middle_name,
        "birth_date": birth_date,
        "gender": {"id": profile["gender"]},
        "area": {"id": str(area_id)},
        "citizenship": [{"id": "113"}],  # Казахстан
        "contact": [
            {"type": {"id": "email"}, "value": profile["email"]},
            {"type": {"id": "cell"}, "value": profile["phone"]}
        ],
        "skill_set": skill_set,
        "skills": ", ".join(skill_set),
        "title": profile["target"],
        "text": text,
        "education_level": {"id": "higher"},
        "education": {
            "primary": [
                {
                    "name": "ALT University",
                    "organization": profile.get("course", "IT факультет"),
                    "year": datetime.now().year + 1  # Примерный год окончания
                }
            ]
        }
    }
    return resume_data

def upload_to_hh(resume_data, user_id):
    """Создает или обновляет резюме на HH.kz и публикует его"""
    headers = {
        "Authorization": f"Bearer {HH_TOKEN}",
        "User-Agent": "ALT University Career Bot (career@alt.edu.kz)"
    }
    
    resume_id = USER_DATA[user_id].get("hh_resume_id")
    
    if resume_id:
        # Обновляем существующее резюме
        response = requests.put(f"https://api.hh.kz/resumes/{resume_id}", json=resume_data, headers=headers)
    else:
        # Создаем новое резюме
        response = requests.post("https://api.hh.kz/resumes", json=resume_data, headers=headers)
        if response.status_code == 201:
            resume_id = response.json().get("id")
            USER_DATA[user_id]["hh_resume_id"] = resume_id
            save_data(USER_DATA)
    
    if response.status_code in [200, 201, 204]:
        # Публикуем резюме
        publish_response = requests.post(f"https://api.hh.kz/resumes/{resume_id}/publish", headers=headers)
        if publish_response.status_code in [200, 204]:
            url = f"https://hh.kz/resume/{resume_id}"
            return {"success": True, "resume_id": resume_id, "url": url}
        else:
            return {"success": False, "error": publish_response.text}
    else:
        return {"success": False, "error": response.text}

print("✅ Career Development Assistant ALT University — ЗАПУЩЕН!")
print("📊 Персистентное хранилище активировано")
print("🔍 Поиск вакансий через HH.KZ API")
print("🧠 История разговоров сохраняется")
bot.infinity_polling()