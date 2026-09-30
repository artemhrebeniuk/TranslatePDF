import fitz
import re
import os
import math
import json
import base64
import urllib.request
from collections import Counter
from typing import Dict, List, Any, Tuple, Optional

# Together AI Configuration (Meta Llama 3.3 70B Instruct Turbo for autonomous clinical translation)
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "tgp_v1_lXSFHV6LFj_nGjLzN_aO3x2X8t22OeqIJamDDOs_cDg")
TOGETHER_MODEL = os.getenv("TOGETHER_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo")

AI_TRANSLATION_CACHE: Dict[str, str] = {}

def call_together_ai_batch(texts: List[str], source_lang="uk", target_lang="en") -> Dict[str, str]:
    """Autonomous clinical translation via Together AI Llama 3.3 70B Instruct Turbo."""
    if not texts or not TOGETHER_API_KEY:
        return {}
    
    to_query = [t for t in texts if t and t not in AI_TRANSLATION_CACHE]
    if not to_query:
        return {t: AI_TRANSLATION_CACHE[t] for t in texts if t in AI_TRANSLATION_CACHE}
        
    system_prompt = (
        "You are an expert clinical pathologist and medical laboratory report translator. "
        "Translate the provided list of phrases from Ukrainian to formal clinical English. "
        "Keep numerical values, reference intervals, units (e.g. g/L, ng/mL, umol/L, fl, pg), and IDs identical. "
        "Output ONLY a valid JSON object mapping each original phrase to its exact clinical English translation. "
        "No markdown, no backticks, no explanations."
    )
    
    payload = {
        "model": TOGETHER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(to_query, ensure_ascii=False)}
        ],
        "temperature": 0.05,
        "max_tokens": 1500
    }
    
    try:
        req = urllib.request.Request(
            "https://api.together.xyz/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "ReviseTranslate/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw = data["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw.rsplit("\n", 1)[0]
                if raw.startswith("json\n"):
                    raw = raw[5:]
            res = json.loads(raw.strip())
            if isinstance(res, dict):
                AI_TRANSLATION_CACHE.update(res)
                return res
    except Exception as e:
        print(f"[Together AI] Translation error: {e}")
        
    return {}

# Font Configuration (Bundled project fonts for Vercel/Linux compatibility with macOS fallback)
FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
SYSTEM_FONTS = {
    "regular": os.path.join(FONTS_DIR, "Arial.ttf") if os.path.exists(os.path.join(FONTS_DIR, "Arial.ttf")) else "/System/Library/Fonts/Supplemental/Arial.ttf",
    "bold": os.path.join(FONTS_DIR, "Arial-Bold.ttf") if os.path.exists(os.path.join(FONTS_DIR, "Arial-Bold.ttf")) else "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "italic": os.path.join(FONTS_DIR, "Arial-Italic.ttf") if os.path.exists(os.path.join(FONTS_DIR, "Arial-Italic.ttf")) else "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
    "bold_italic": os.path.join(FONTS_DIR, "Arial-Bold.ttf") if os.path.exists(os.path.join(FONTS_DIR, "Arial-Bold.ttf")) else "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
    "unicode": os.path.join(FONTS_DIR, "Arial.ttf") if os.path.exists(os.path.join(FONTS_DIR, "Arial.ttf")) else "/System/Library/Fonts/Supplemental/Arial.ttf"
}

# Medical Dictionary (Ukrainian -> English)
MEDICAL_UK_EN = {
    # Headers & Accreditation
    "Гарантія точності та достовірності результатів досліджень": "Guarantee of accuracy and reliability of examination results",
    "Діагностичний центр ТОВ «МЛ «ДІЛА» акредитований Національним агентством з акредитації України": "Diagnostic Center LLC \"ML \"DILA\" accredited by the National Accreditation Agency of Ukraine",
    "на дослідження відповідно до ISO 15189:2022, атестат про акредитацію №30001 чинний до 18.10.2026": "for testing in accordance with ISO 15189:2022, accreditation certificate No. 30001 valid until 18.10.2026",
    "Україна, 01103, м. Київ, вул. Підвисоцького, 6а": "Ukraine, 01103, Kyiv, 6a Pidvysotskoho St.",
    "Інформаційно-сервісна служба: 0 800 21 78 87": "Information & Customer Service: 0 800 21 78 87",
    "Шановний клієнте!": "Dear Client!",
    "Результати лабораторних досліджень не є клінічним діагнозом.": "Laboratory test results do not constitute a clinical diagnosis.",
    "Для коректної інтерпретації результатів досліджень, зверніться, будь ласка, до лікаря.": "For correct interpretation of examination results, please consult a physician.",
    "Шановний лікарю!": "Dear Doctor!",
    "Експерти ДІЛА надають інформаційну підтримку щодо трактування": "DILA experts provide informational support regarding interpretation",
    "результатів лабораторного дослідження та інших професійних питань.": "of laboratory test results and other professional inquiries.",
    "Ліцензія МОЗ України АД №071280 від 22.11.2012 р.    ТОВ «МЛ «ДІЛА» сертифіковано згідно вимог міжнародного стандарту ISO 9001": "License of MOH of Ukraine AD No. 071280 dated 22.11.2012. LLC \"ML \"DILA\" certified per ISO 9001",
    "Ліцензія МОЗ України АД №071280 від 22.11.2012 р.": "License of MOH of Ukraine AD No. 071280 dated 22.11.2012",
    "ТОВ «МЛ «ДІЛА» сертифіковано згідно вимог міжнародного стандарту ISO 9001": "LLC \"ML \"DILA\" certified per ISO 9001",
    
    # Document Metadata & Patient
    "РЕЗУЛЬТАТИ ДОСЛІДЖЕНЬ": "EXAMINATION RESULTS",
    "Пацієнт": "Patient",
    "Єщенко Макар Олександрович": "Yeshchenko Makar Oleksandrovych",
    "Лаб. № замовлення": "Lab Order No.",
    "063758776": "063758776",
    "Дата народж.": "Date of Birth",
    "Код замовлення": "Order Code",
    "Стать": "Sex",
    "Чоловіча": "Male",
    "Жіноча": "Female",
    "Дата замовлення": "Order Date",
    "Коментарi": "Comments",
    "Кабінет МЦП №594 м. Ірпінь, вул.": "Blood Collection Center No. 594, Irpin,",
    "Соборна, 9": "9 Soborna St.",
    "символом * позначаються результати, що виходять за межі референтних значень": "* indicates results outside the reference range",
    "Пацієнт: Єщенко Макар Олександрович": "Patient: Yeshchenko Makar Oleksandrovych",
    "№ зам.:": "Order No.:",
    "№ зам.:  063758776": "Order No.: 063758776",
    "Дата друку: 24.07.2026 21:50": "Print date: 24.07.2026 21:50",
    "Дата друку:": "Print date:",
    "с.1 з 3": "p. 1 of 3",
    "с.2 з 3": "p. 2 of 3",
    "с.3 з 3": "p. 3 of 3",

    # Table Column Headers
    "Назва дослідження": "Test Name",
    "Результат": "Result",
    "Одиниці": "Units",
    "вимірювання": "of measurement",
    "Одиниці вимірювання": "Units of measurement",
    "Референтні": "Reference",
    "значення": "values",
    "значення:": "values:",
    "Референтні значення": "Reference values",
    "Референтні значення:": "Reference values:",
    
    # Panels & Medical Tests
    "Комплекс №175 \"Вияви причину анемії\"": "Panel No. 175 \"Identify Cause of Anemia\"",
    "Первинна проба: венозна кров": "Primary specimen: venous blood",
    "Інтерпретація результату має здійснюватися з урахуванням додаткових функціональних показників та клінічної оцінки лікаря.": "Result interpretation must be performed considering additional functional parameters and clinical assessment by a physician.",
    "Феритин": "Ferritin",
    "Фолієва кислота": "Folic Acid",
    "Вітамін В12 (ціанокобаламін, vitamin": "Vitamin B12 (cyanocobalamin),",
    "B12, cyanocobalamin), біотин-": "biotin-independent,",
    "незалежний, кількісний": "quantitative",
    "Увага! Оцінка дефіциту вітаміну B12 не повинна базуватися виключно на результаті одного лабораторного дослідження.": "Note: Assessment of Vitamin B12 deficiency should not rely solely on a single laboratory test result.",
    "Трансферин": "Transferrin",
    "Залізо": "Iron",
    "Насичення трансферину залізом": "Transferrin Saturation",
    "(залізо, трансферин, насичення": "(iron, transferrin, transferrin",
    "трансферину)": "saturation)",
    "Загальний розгорнутий аналіз крові (35 показників: геманалізатор з морфологічним вивченням крові)": "Complete Blood Count (35 parameters: automated hematology analyzer with morphology)",
    "Лейкоцити (WBC)": "Leukocytes (WBC)",
    "Еритроцити (RBC)": "Erythrocytes (RBC)",
    "Гемоглобін (Hgb)": "Hemoglobin (Hgb)",
    "Гематокрит (Ht)": "Hematocrit (Ht)",
    "Тромбоцити (PLT)": "Platelets (PLT)",
    "Тромбокрит (PCT)": "Plateletcrit (PCT)",
    "Незрілі гранулоцити (IG)": "Immature Granulocytes (IG)",
    "Середній об`єм еритроцитів (MCV)": "Mean Corpuscular Volume (MCV)",
    "Середній вміст гемоглобіну в одному": "Mean Corpuscular Hemoglobin in one",
    "еритроциті (MCH)": "erythrocyte (MCH)",
    "Середня концентрація гемоглобіну в": "Mean Corpuscular Hemoglobin",
    "еритроцитах (MCHC)": "Concentration (MCHC)",
    "Ширина розподілення еритроцитів по": "Red Cell Distribution Width",
    "об`єму (коефіцієнт варіації) (RDW-CV)": "by volume (CV) (RDW-CV)",
    "Низька щільність гемоглобіну (LHD)": "Low Hemoglobin Density (LHD)",
    "Фактор мікроцитарної анемії (MaF)": "Microcytic Anemia Factor (MaF)",
    "Середній об`єм тромбоцитів (MPV)": "Mean Platelet Volume (MPV)",
    "Ширина розподілення тромбоцитів": "Platelet Distribution Width",
    "по об`єму (PDW)": "by volume (PDW)",
    "Загальні нейтрофіли (сегментоядерні": "Total Neutrophils (Segmented",
    "та паличкоядерні) (Neu)": "and Band) (Neu)",
    "ПАЛИЧКОЯДЕРНІ НЕЙТРОФІЛИ < 6.0 %": "BAND NEUTROPHILS < 6.0 %",
    "ПАЛИЧКОЯДЕРНІ НЕЙТРОФІЛИ < 0.6 Г/л": "BAND NEUTROPHILS < 0.6 G/L",
    "Лімфоцити (LY)": "Lymphocytes (LY)",
    "Моноцити (Mon)": "Monocytes (Mon)",
    "Еозинофіли (Eo)": "Eosinophils (Eo)",
    "Базофіли (Bas)": "Basophils (Bas)",
    "Метамієлоцити (MetaMC)": "Metamyelocytes (MetaMC)",
    "Мієлоцити (MС)": "Myelocytes (MC)",
    "Віроцити (VIR)": "Virocytes (VIR)",
    "Швидкість осідання еритроцитів (ESR)": "Erythrocyte Sedimentation Rate (ESR)",

    # Reference Intervals (Concise Clinical Standards)
    "0-15 д. 39.84 - 539.85": "0-15 d. 39.84 - 539.85",
    "15 д.-6 м. 15.25 - 374.58": "15 d.-6 mo. 15.25 - 374.58",
    "6 м.-1 рік 13.32 - 191.89": "6 mo.-1 yr 13.32 - 191.89",
    "1-16 років 10.29 - 55.84": "1-16 yrs 10.29 - 55.84",
    "16-19 років 18.67 - 102.06": "16-19 yrs 18.67 - 102.06",
    "Від 19 років 23.9-336.2": "From 19 yrs 23.9-336.2",
    "0 - 14 років >12,2": "0 - 14 yrs >12.2",
    "14 - 19 років >8,9": "14 - 19 yrs >8.9",
    "Від 19 років 3,1-19,9": "From 19 yrs 3.1-19.9",
    "0 - 1 року >159.28": "0 - 1 yr >159.28",
    "0 - 1 рік >159.28": "0 - 1 yr >159.28",
    "1 - 2 роки >267.05": "1 - 2 yrs >267.05",
    "2 - 8 років 257.83 - 1012.91": "2 - 8 yrs 257.83 - 1012.91",
    "8 - 14 років 201.39 - 1046.25": "8 - 14 yrs 201.39 - 1046.25",
    "14 - 19 років 179.38 - 719.46": "14 - 19 yrs 179.38 - 719.46",
    
    # Page 3: 25-OH Vitamin D & Doctor Signature
    "25-гідроксивітамін Д": "25-Hydroxyvitamin D",
    "Відповідальна особа": "Responsible Person",
    "Завідувач Лабораторії клінічної біохімії Поливода А.Я.": "Head of Clinical Biochemistry Lab Polyvoda A.Y.",
    "<50 - дефіцит вітаміну D;": "<50 - Vitamin D deficiency;",
    ">=50 - <75 - недостатність": ">=50 - <75 - Insufficiency of",
    "вітаміну D;": "Vitamin D;",
    "75-125 - достатній рівень": "75-125 - Optimal level of",
    ">125-150 - безпечний, але не": ">125-150 - Safe non-target",
    "цільовий рівень вітаміну D;": "level of Vitamin D;",
    ">150-250 - зона": ">150-250 - Zone of",
    "невизначеності з": "uncertainty with",
    "потенційними перевагами чи": "potential benefits or",
    "ризиками;": "risks;",
    ">250 - надлишок/зона": ">250 - Vitamin D excess /",
    "токсичності вітаміну D.": "toxicity zone.",
    "Діагностика, профілактика та": "Diagnosis, prevention and",
    "лікування дефіциту вітаміну": "treatment of Vitamin D",
    "D у дорослих: Kонсенсус": "deficiency: Ukrainian",
    "українських експертів, 2023р": "Expert Consensus, 2023",
    "Цільовий рівень вітаміну D залежить від особливостей стану здоров’я пацієнта. Зверніться до лікаря": "The target Vitamin D level depends on patient's individual health status. Consult a physician",
    
    # Units
    "нг/мл": "ng/mL",
    "мкмоль/л": "µmol/L",
    "г/л": "g/L",
    "Г/л": "G/L",
    "Т/л": "T/L",
    "мм/год": "mm/h",
    "нмоль/л": "nmol/L",
    "пг": "pg",
    "пг/мл": "pg/mL",
    "fl": "fL",
}

# Reverse Medical Dictionary (English -> Ukrainian)
MEDICAL_EN_UK = {v: k for k, v in MEDICAL_UK_EN.items()}

# Cadastral & Enterprise Dictionary (English/French -> Ukrainian)
CADASTRAL_EN_UK = {
    "SIRENE LOCATION DOSSIER": "ДОСЬЄ РОЗТАШУВАННЯ SIRENE",
    "NATIONAL ENTERPRISE REGISTRY • FRENCH REPUBLIC (INSEE)": "НАЦІОНАЛЬНИЙ РЕЄСТР ПІДПРИЄМСТВ • ФРАНЦУЗЬКА РЕСПУБЛІКА (INSEE)",
    "SIREN : 108771452": "SIREN : 108771452",
    "COMMUNE CODE : 75101": "КОД КОМУНИ : 75101",
    "COMMERCIAL ENTITY & CADASTRAL ASSESSMENT": "КОМЕРЦІЙНИЙ ОБ'ЄКТ ТА КАДАСТРОВА ОЦІНКА",
    "BALAE": "BALAE",
    "75001 PARIS, France • Department 75 (Paris)": "75001 ПАРИЖ, Франція • Департамент 75 (Париж)",
    "SIRET IDENTIFICATION": "ІДЕНТИФІКАЦІЯ SIRET",
    "NAF 2008 ACTIVITY": "ВИД ДІЯЛЬНОСТІ NAF 2008",
    "96.04Z • Physical": "96.04Z • Фізичне",
    "Wellbeing & Spa": "оздоровлення та СПА-",
    "Services": "послуги",
    "NAF 2025 TRANSITION": "ПЕРЕХІД NAF 2025",
    "93.13Y • Sports &": "93.13Y • Спортивно-",
    "Recreation": "оздоровча освіта",
    "Education &": "та послуги",
    "Coaching": "коучингу",
    "REGISTRATION DATE": "ДАТА РЕЄСТРАЦІЇ",
    "CADASTRAL": "КАДАСТРОВА",
    "LOCATION": "КАРТА",
    "MAP": "РОЗТАШУВАННЯ",
    "BAN QUALITY 11 • EXACT PARCEL": "ЯКІСТЬ BAN 11 • ТОЧНА ДІЛЯНКА",
    "GPS : 48.863266,": "GPS : 48.863266,",
    "2.348160": "2.348160",
    "IRIS District :": "Район IRIS :",
    "Zoning :": "Зонування :",
    "DIRECT COMPETITORS (NAF": "ПРЯМІ КОНКУРЕНТИ (NAF",
    "96.04Z)": "96.04Z)",
    "SPATIAL RADAR": "ПРОСТОРОВИЙ РАДАР",
    "ESTABLISHMENT NAME": "НАЗВА ЗАКЛАДУ",
    "DISTANCE": "ВІДСТАНЬ",
    "POSTAL CODE": "ПОШТОВИЙ ІНДЕКС",
    "Computed by DuckDB spatial engine across 15.9M+ French registry": "Розраховано просторовим рушієм DuckDB на 15.9M+ записів реєстру",
    "records.": "Франції.",
    "COMPETITORS IN 75001": "КОНКУРЕНТИ В 75001",
    "Active 96.04Z in postal zone": "Активні 96.04Z у поштовій зоні",
    "COMPETITORS IN DEPT 75": "КОНКУРЕНТИ В ДЕПАРТАМЕНТІ 75",
    "Active 96.04Z in Paris": "Активні 96.04Z у Парижі",
    "TOTAL BUSINESSES IN 75001": "ВСЬОГО ПІДПРИЄМСТВ У 75001",
    "All active entities in 75001": "Усі активні суб'єкти в 75001",
    "TOTAL IN DEPT 75": "ВСЬОГО В ДЕПАРТАМЕНТІ 75",
    "Paris regional total": "Регіональний підсумок по Парижу",
    "COMMERCIAL FREIGHT &": "ПАРКОВКА ДЛЯ КОМЕРЦІЙНОГО",
    "LOGISTICS PARKING": "ТА ВАНТАЖНОГО ТРАНСПОРТУ",
    "OSM RADAR • 500M": "OSM РАДАР • 500M",
    "Parking Forum des Halles": "Парковка Forum des Halles",
    "Parking Turbigo - Saint-Denis": "Парковка Turbigo - Saint-Denis",
    "Public Parking": "Громадська парковка",
    "CADASTRAL DATA": "СПЕЦИФІКАЦІЯ",
    "SPECIFICATIONS": "КАДАСТРОВИХ ДАНИХ",
    "BAN OFFICIAL": "ОФІЦІЙНА BAN",
    "Geocoding Source": "Джерело геокодування",
    "Base Adresse Nationale (BAN)": "Національна адресна база (BAN)",
    "Precision Class Quality 11 (Exact House Number)": "Клас точності 11 (Точний номер будинку)",
    "Administrative Status": "Адміністративний статус",
    "Active": "Діє",
    "RECORD ID : 10877145200019 • SIRENE / BAN": "ID ЗАПИСУ : 10877145200019 • SIRENE / BAN",
    "CADASTRE CERTIFIED": "СЕРТИФІКОВАНО КАДАСТРОМ",
    "GOVERNMENT REGISTRY": "ДЕРЖАВНИЙ РЕЄСТР",
    "Scan to verify official dossier": "Відскануйте для перевірки досьє",
    "on data.gouv.fr": "на data.gouv.fr",
}

def classify_segment(text: str) -> str:
    """Categorize text for user-friendly UI presentation."""
    t = text.lower()
    if any(k in t for k in ["лейкоцити", "еритроцити", "гемоглобін", "гематокрит", "тромбоцити", "феритин", "вітамін", "leukocytes", "erythrocytes", "hemoglobin", "ferritin", "platelets"]):
        return "Medical Test"
    if any(k in t for k in ["референтні", "reference", "нг/мл", "мкмоль", "г/л", "ng/ml", "fl", "pg", "мм/год"]):
        return "Unit / Reference"
    if any(k in t for k in ["пацієнт", "patient", "стать", "sex", "замовлення", "order", "народж", "birth"]):
        return "Patient Demographics"
    if any(k in t for k in ["лікар", "doctor", "відповідальна", "завідувач", "responsible", "person"]):
        return "Doctor / Authority"
    if any(k in t for k in ["ліцензія", "акредит", "сертифік", "license", "accreditation", "діагноз", "diagnosis", "увага"]):
        return "Legal / Disclaimer"
    if any(k in t for k in ["sirene", "cadastral", "siren", "siret", "commune", "competitors", "naf"]):
        return "Cadastral / Official"
    return "General Text"

def translate_string(text: str, source_lang="uk", target_lang="en", mode="medical") -> str:
    cleaned = text.strip()
    if not cleaned:
        return text
        
    # Check direction
    if source_lang == "uk" and target_lang == "en":
        if cleaned in MEDICAL_UK_EN:
            return MEDICAL_UK_EN[cleaned]
        if cleaned in AI_TRANSLATION_CACHE:
            return AI_TRANSLATION_CACHE[cleaned]
    elif source_lang in ["en", "fr"] and target_lang == "uk":
        if mode == "cadastral" and cleaned in CADASTRAL_EN_UK:
            return CADASTRAL_EN_UK[cleaned]
        if cleaned in MEDICAL_EN_UK:
            return MEDICAL_EN_UK[cleaned]
        if cleaned in CADASTRAL_EN_UK:
            return CADASTRAL_EN_UK[cleaned]
    elif source_lang == "en" and target_lang == "en":
        return cleaned

    # Pure numbers, codes, symbols
    if re.match(r'^[\d\s\.,\-\:\/\*\<\>\=\+\%()#№]+$', cleaned):
        return cleaned

    if cleaned in ["dila.ua", "-", "%", "CSZ", "0204"]:
        return cleaned

    # Age pattern regex (Ukrainian to English)
    if source_lang == "uk":
        t = cleaned
        t = re.sub(r'(\d+)\s*д\.', r'\1 d.', t)
        t = re.sub(r'(\d+)\s*м\.', r'\1 mo.', t)
        t = re.sub(r'(\d+)\s*рік', r'\1 yr', t)
        t = re.sub(r'(\d+)\s*року', r'\1 yr', t)
        t = re.sub(r'(\d+)\s*роки', r'\1 yrs', t)
        t = re.sub(r'(\d+)\s*років', r'\1 yrs', t)
        t = re.sub(r'[Вв]ід\s+(\d+)\s+рок[іи]в', r'From \1 yrs', t)
        if t != cleaned:
            return t

    return cleaned

def get_clean_background_color(pix: fitz.Pixmap, rect: fitz.Rect, page_idx: int = 0) -> Tuple[float, float, float]:
    """
    Determine the true background color of a line of text by analyzing the dominant light color
    inside and immediately around its bounding box.
    This guarantees that text inside soft blue/tinted table rows gets the exact row tint,
    while text on white rows gets pure white, without accidental margin bleed.
    """
    w, h = pix.width, pix.height
    x0 = max(0, int(rect.x0))
    x1 = min(w - 1, int(rect.x1))
    y0 = max(0, int(rect.y0))
    y1 = min(h - 1, int(rect.y1))
    
    # Grid sampling inside the bounding box
    step_x = 1 if (x1 - x0) < 60 else 2
    step_y = 1
    
    light_pixels = []
    for y in range(y0, y1 + 1, step_y):
        for x in range(x0, x1 + 1, step_x):
            rgb = pix.pixel(x, y)[:3]
            lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
            if lum > 175: # background is always light
                light_pixels.append(rgb)
                
    # Also sample right-padding if available (safe from left margin bleed)
    cy = int((rect.y0 + rect.y1) / 2)
    if 0 <= cy < h:
        for offset in (3, 6, 9):
            rx = int(rect.x1 + offset)
            if 0 <= rx < w:
                rgb = pix.pixel(rx, cy)[:3]
                lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
                if lum > 175:
                    light_pixels.extend([rgb] * 5)
                    
    if not light_pixels:
        return (1.0, 1.0, 1.0)
        
    counts = Counter(light_pixels)
    most_common_rgb = counts.most_common(1)[0][0]
    
    # Snap near-white to pure white
    if all(c > 250 for c in most_common_rgb):
        return (1.0, 1.0, 1.0)
        
    return (most_common_rgb[0] / 255.0, most_common_rgb[1] / 255.0, most_common_rgb[2] / 255.0)

class PDFTranslator:
    def __init__(self):
        self.font_reg = SYSTEM_FONTS["regular"]
        self.font_bold = SYSTEM_FONTS["bold"]
        self.font_italic = SYSTEM_FONTS["italic"]
        self.font_unicode = SYSTEM_FONTS["unicode"]
        self.font_obj_reg = fitz.Font(fontfile=self.font_reg)
        self.font_obj_bold = fitz.Font(fontfile=self.font_bold)
        self.font_obj_italic = fitz.Font(fontfile=self.font_italic)
        self.font_obj_unicode = fitz.Font(fontfile=self.font_unicode)

    def extract_document_segments(self, input_path: str, source_lang="uk", target_lang="en", mode="medical") -> List[Dict[str, Any]]:
        doc = fitz.open(input_path)
        segments = []
        seg_id = 0
        
        # Discover unknown text phrases to batch translate via Together AI (Llama 3.3 70B)
        unknown_texts = []
        for page in doc:
            p_dict = page.get_text("dict")
            for b in p_dict.get("blocks", []):
                if b.get("type") == 0:
                    for l in b["lines"]:
                        txt = "".join([s["text"] for s in l["spans"]]).strip()
                        if (txt and txt not in MEDICAL_UK_EN and txt not in AI_TRANSLATION_CACHE
                            and len(txt) > 1 and not re.match(r'^[\d\s\.,\-\:\/\*\<\>\=\+\%()#№]+$', txt)):
                            unknown_texts.append(txt)
                            
        if unknown_texts and source_lang == "uk" and target_lang == "en":
            unique_unknown = list(dict.fromkeys(unknown_texts))
            for i in range(0, len(unique_unknown), 25):
                call_together_ai_batch(unique_unknown[i:i+25], source_lang=source_lang, target_lang=target_lang)

        for p_idx, page in enumerate(doc):
            page_dict = page.get_text("dict")
            for b in page_dict.get("blocks", []):
                if b.get("type") == 0:
                    for l in b["lines"]:
                        txt = "".join([s["text"] for s in l["spans"]]).strip()
                        if not txt:
                            continue
                        trans = translate_string(txt, source_lang=source_lang, target_lang=target_lang, mode=mode)
                        category = classify_segment(txt)
                        first_span = l["spans"][0]
                        
                        segments.append({
                            "id": seg_id,
                            "page": p_idx + 1,
                            "bbox": [round(x, 1) for x in l["bbox"]],
                            "original": txt,
                            "translated": trans,
                            "category": category,
                            "dir": l.get("dir", (1.0, 0.0)),
                            "is_vertical": (l.get("dir") == (0.0, -1.0) or l.get("dir") == (0.0, 1.0)),
                            "size": round(first_span.get("size", 10.0), 1),
                            "changed": (txt != trans)
                        })
                        seg_id += 1
        return segments

    def translate_and_patch(
        self,
        input_path: str,
        output_path: str,
        source_lang="uk",
        target_lang="en",
        mode="medical",
        custom_translations: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        doc = fitz.open(input_path)
        all_segments = []
        seg_id = 0

        # Discover unknown text phrases to batch translate via Together AI (Llama 3.3 70B)
        unknown_texts = []
        for page in doc:
            p_dict = page.get_text("dict")
            for b in p_dict.get("blocks", []):
                if b.get("type") == 0:
                    for l in b["lines"]:
                        txt = "".join([s["text"] for s in l["spans"]]).strip()
                        if (txt and txt not in MEDICAL_UK_EN and txt not in AI_TRANSLATION_CACHE
                            and len(txt) > 1 and not re.match(r'^[\d\s\.,\-\:\/\*\<\>\=\+\%()#№]+$', txt)):
                            unknown_texts.append(txt)
                            
        if unknown_texts and source_lang == "uk" and target_lang == "en":
            unique_unknown = list(dict.fromkeys(unknown_texts))
            for i in range(0, len(unique_unknown), 25):
                call_together_ai_batch(unique_unknown[i:i+25], source_lang=source_lang, target_lang=target_lang)

        # Determine target font encoding
        is_target_cyrillic = (target_lang == "uk")
        encoding = fitz.TEXT_ENCODING_CYRILLIC if is_target_cyrillic else fitz.TEXT_ENCODING_LATIN

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            pix = page.get_pixmap()
            page_dict = page.get_text("dict")
            
            # Register embedded fonts on page for robust Unicode/Cyrillic rendering
            page.insert_font(fontname="app_reg", fontfile=self.font_unicode if is_target_cyrillic else self.font_reg, encoding=encoding)
            page.insert_font(fontname="app_bold", fontfile=self.font_unicode if is_target_cyrillic else self.font_bold, encoding=encoding)
            page.insert_font(fontname="app_italic", fontfile=self.font_unicode if is_target_cyrillic else self.font_italic, encoding=encoding)

            # Special vector graphics text handlers for known documents:
            if source_lang == "uk" and target_lang == "en":
                slogan_rect = fitz.Rect(150.0, 24.0, 565.0, 40.0)
                drawings_top = [d for d in page.get_drawings() if 20 < d["rect"].y0 < 42 and d["rect"].x0 > 140]
                if len(drawings_top) > 20:
                    page.draw_rect(slogan_rect, color=(1, 1, 1), fill=(1, 1, 1))
                    page.insert_text((151.0, 36.0), "Guarantee of accuracy and reliability of examination results",
                                     fontname="app_reg", fontfile=self.font_reg, fontsize=12.2, color=(0.708, 0.036, 0.218))
                
                drawings_left = [d for d in page.get_drawings() if d["rect"].x1 < 25 and d.get("fill") and d["fill"][0] > 0.6]
                if len(drawings_left) > 10:
                    # Clear red vector margin rectangles cleanly
                    r_doc = fitz.Rect(9.0, 316.0, 22.0, 394.0)
                    page.draw_rect(r_doc, color=(1, 1, 1), fill=(1, 1, 1))
                    page.insert_text((18.0, 388.0), "Dear Doctor!", fontname="app_reg", fontfile=self.font_reg, fontsize=8.5, color=(0.708, 0.036, 0.218), rotate=90)
                    
                    r_client = fitz.Rect(9.0, 646.0, 22.0, 725.0)
                    page.draw_rect(r_client, color=(1, 1, 1), fill=(1, 1, 1))
                    page.insert_text((18.0, 718.0), "Dear Client!", fontname="app_reg", fontfile=self.font_reg, fontsize=8.5, color=(0.708, 0.036, 0.218), rotate=90)

                # Clear & translate header address if vector paths exist
                drawings_addr = [d for d in page.get_drawings() if 65 < d["rect"].y0 < 78 and 150 < d["rect"].x0 < 340]
                if len(drawings_addr) > 15:
                    addr_rect = fitz.Rect(149.0, 66.0, 345.0, 77.5)
                    page.draw_rect(addr_rect, color=(1, 1, 1), fill=(1, 1, 1))
                    page.insert_text(
                        (150.5, 74.2),
                        "Ukraine, 01103, Kyiv, 6a Pidvysotskoho St.",
                        fontname="app_reg",
                        fontfile=self.font_reg,
                        fontsize=7.2,
                        color=(0.0, 0.335, 0.590)
                    )

            items_to_replace = []
            
            for b in page_dict.get("blocks", []):
                if b.get("type") == 0:
                    for l in b["lines"]:
                        line_text = "".join([s["text"] for s in l["spans"]]).strip()
                        if not line_text:
                            continue
                        
                        first_span = l["spans"][0]
                        font_name = first_span.get("font", "")
                        font_flags = first_span.get("flags", 0)
                        font_size = first_span.get("size", 10.0)
                        color_int = first_span.get("color", 0)
                        r = ((color_int >> 16) & 255) / 255.0
                        g = ((color_int >> 8) & 255) / 255.0
                        b_col = (color_int & 255) / 255.0
                        
                        is_bold = ("Bold" in font_name or "bold" in font_name or (font_flags & 2 != 0))
                        is_italic = ("Italic" in font_name or "italic" in font_name or (font_flags & 1 != 0))
                        line_dir = l.get("dir", (1.0, 0.0))
                        origin = first_span.get("origin", (l["bbox"][0], l["bbox"][3]))
                        bbox = fitz.Rect(l["bbox"])
                        
                        # Apply custom overrides if user edited in UI
                        if custom_translations and str(seg_id) in custom_translations:
                            translated = custom_translations[str(seg_id)]
                        elif custom_translations and line_text in custom_translations:
                            translated = custom_translations[line_text]
                        else:
                            translated = translate_string(line_text, source_lang=source_lang, target_lang=target_lang, mode=mode)
                            
                        category = classify_segment(line_text)
                        
                        items_to_replace.append({
                            "id": seg_id,
                            "original": line_text,
                            "translated": translated,
                            "bbox": bbox,
                            "origin": origin,
                            "dir": line_dir,
                            "size": font_size,
                            "color": (r, g, b_col),
                            "is_bold": is_bold,
                            "is_italic": is_italic,
                        })
                        
                        all_segments.append({
                            "id": seg_id,
                            "page": page_idx + 1,
                            "original": line_text,
                            "translated": translated,
                            "bbox": [round(x, 1) for x in l["bbox"]],
                            "category": category,
                            "is_vertical": (line_dir == (0.0, -1.0) or line_dir == (0.0, 1.0)),
                            "changed": (line_text != translated)
                        })
                        seg_id += 1

            # 1. Add non-destructive redactions for translated lines
            for item in items_to_replace:
                if item["original"] != item["translated"]:
                    bg_col = get_clean_background_color(pix, item["bbox"], page_idx=page_idx)
                    pad = fitz.Rect(
                        item["bbox"].x0 - 0.5,
                        item["bbox"].y0 - 0.5,
                        item["bbox"].x1 + 0.5,
                        item["bbox"].y1 + 0.5
                    )
                    page.add_redact_annot(pad, fill=bg_col)
                    
            # 2. Apply redactions while guaranteeing images (stamps, signatures) remain untouched
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
            
            # 3. Inscribe translated text
            for item in items_to_replace:
                if item["original"] == item["translated"]:
                    continue
                    
                trans_text = item["translated"]
                is_vertical = (item["dir"] == (0.0, -1.0) or item["dir"] == (0.0, 1.0))
                
                if item["is_bold"]:
                    fontname = "app_bold"
                    chosen_font = self.font_bold if not is_target_cyrillic else self.font_unicode
                    chosen_font_obj = self.font_obj_bold if not is_target_cyrillic else self.font_obj_unicode
                elif item["is_italic"]:
                    fontname = "app_italic"
                    chosen_font = self.font_italic if not is_target_cyrillic else self.font_unicode
                    chosen_font_obj = self.font_obj_italic if not is_target_cyrillic else self.font_obj_unicode
                else:
                    fontname = "app_reg"
                    chosen_font = self.font_reg if not is_target_cyrillic else self.font_unicode
                    chosen_font_obj = self.font_obj_reg if not is_target_cyrillic else self.font_obj_unicode
                    
                orig_sz = item["size"]
                
                if is_vertical:
                    max_len = item["bbox"].height
                    text_len = chosen_font_obj.text_length(trans_text, fontsize=orig_sz)
                    scale = min(1.0, (max_len * 0.98) / max(1.0, text_len))
                    actual_sz = orig_sz * scale
                    # In PyMuPDF, rotate=90 draws upwards along y-axis from baseline origin
                    page.insert_text(
                        item["origin"],
                        trans_text,
                        fontname=fontname,
                        fontfile=chosen_font,
                        fontsize=actual_sz,
                        color=item["color"],
                        rotate=90
                    )
                else:
                    max_w = item["bbox"].width
                    text_w = chosen_font_obj.text_length(trans_text, fontsize=orig_sz)
                    scale = min(1.0, (max_w * 1.05) / max(1.0, text_w))
                    actual_sz = max(5.0, orig_sz * scale)
                    page.insert_text(
                        item["origin"],
                        trans_text,
                        fontname=fontname,
                        fontfile=chosen_font,
                        fontsize=actual_sz,
                        color=item["color"],
                        rotate=0
                    )
                    
        doc.save(output_path, deflate=True)
        return {
            "total_pages": len(doc),
            "total_segments": len(all_segments),
            "translated_count": sum(1 for s in all_segments if s["changed"]),
            "segments": all_segments
        }

    def render_page_previews(self, pdf_path: str, output_dir: str, prefix="page") -> List[str]:
        os.makedirs(output_dir, exist_ok=True)
        doc = fitz.open(pdf_path)
        preview_files = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            fname = f"{prefix}_{i+1}.png"
            fpath = os.path.join(output_dir, fname)
            pix.save(fpath)
            preview_files.append(fname)
        return preview_files

    def render_page_previews_b64(self, pdf_path: str, dpi: int = 125) -> List[str]:
        doc = fitz.open(pdf_path)
        b64_list = []
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            png_bytes = pix.tobytes("png")
            b64_str = f"data:image/png;base64,{base64.b64encode(png_bytes).decode('ascii')}"
            b64_list.append(b64_str)
        return b64_list

pdf_engine = PDFTranslator()
