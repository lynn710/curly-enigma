# -*- coding: utf-8 -*-

import os
import re
import base64
import logging
import asyncio
import datetime
import fal_client

from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import Forbidden, BadRequest

from groq import Groq


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE"
)

GROQ_API_KEY = os.environ.get(
    "GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE"
)

FAL_KEY = os.environ.get(
    "FAL_KEY", "YOUR_FAL_KEY_HERE"
)


# =========================================================
# ADMIN
# =========================================================

ADMIN_ID = 6908674664


# =========================================================
# WEATHER CONFIG
# =========================================================

WEATHER_BROADCAST_HOUR = 6
WEATHER_BROADCAST_MINUTE = 0
MYANMAR_TZ = ZoneInfo("Asia/Yangon")

# တိုင်းဒေသကြီး ၇ ခု + ပြည်နယ် ၇ ခု (Representative city per region)
MYANMAR_REGIONS = [
    {"label": "ရန်ကုန်တိုင်းဒေသကြီး", "query": "Yangon, Myanmar"},
    {"label": "မန္တလေးတိုင်းဒေသကြီး", "query": "Mandalay, Myanmar"},
    {"label": "နေပြည်တော်", "query": "Naypyidaw, Myanmar"},
    {"label": "ပဲခူးတိုင်းဒေသကြီး", "query": "Bago, Myanmar"},
    {"label": "မကွေးတိုင်းဒေသကြီး", "query": "Magway, Myanmar"},
    {"label": "စစ်ကိုင်းတိုင်းဒေသကြီး", "query": "Sagaing, Myanmar"},
    {"label": "တနင်္သာရီတိုင်းဒေသကြီး", "query": "Dawei, Myanmar"},
    {"label": "ဧရာဝတီတိုင်းဒေသကြီး", "query": "Pathein, Myanmar"},
    {"label": "ကချင်ပြည်နယ်", "query": "Myitkyina, Myanmar"},
    {"label": "ကယားပြည်နယ်", "query": "Loikaw, Myanmar"},
    {"label": "ကရင်ပြည်နယ်", "query": "Hpa-An, Myanmar"},
    {"label": "ချင်းပြည်နယ်", "query": "Hakha, Myanmar"},
    {"label": "မွန်ပြည်နယ်", "query": "Mawlamyine, Myanmar"},
    {"label": "ရခိုင်ပြည်နယ်", "query": "Sittwe, Myanmar"},
    {"label": "ရှမ်းပြည်နယ်", "query": "Taunggyi, Myanmar"},
]

# User message ထဲမှာ ရှာမယ့် မြို့/နေရာ နာမည်များ (myanmar + english variants)
# key = search query အတွက် သုံးမယ့် တကယ့်နာမည်, value = message ထဲမှာ ကိုက်ညီရှာမယ့် keyword များ
CITY_ALIASES = {
    "Yangon, Myanmar": ["ရန်ကုန်", "yangon", "rangoon"],
    "Mandalay, Myanmar": ["မန္တလေး", "mandalay"],
    "Naypyidaw, Myanmar": ["နေပြည်တော်", "naypyidaw", "nay pyi taw"],
    "Bago, Myanmar": ["ပဲခူး", "bago", "pegu"],
    "Magway, Myanmar": ["မကွေး", "magway", "magwe"],
    "Sagaing, Myanmar": ["စစ်ကိုင်း", "sagaing"],
    "Dawei, Myanmar": ["ထားဝယ်", "တနင်္သာရီ", "dawei", "tanintharyi"],
    "Pathein, Myanmar": ["ပုသိမ်", "ဧရာဝတီ", "pathein", "ayeyarwady"],
    "Myitkyina, Myanmar": ["မြစ်ကြီးနား", "ကချင်", "myitkyina", "kachin"],
    "Loikaw, Myanmar": ["လွိုင်ကော်", "ကယား", "loikaw", "kayah"],
    "Hpa-An, Myanmar": ["ဘားအံ", "ကရင်", "hpa-an", "hpaan", "kayin"],
    "Hakha, Myanmar": ["ဟားခါး", "ချင်း", "hakha", "chin"],
    "Mawlamyine, Myanmar": ["မော်လမြိုင်", "မွန်", "mawlamyine", "mon"],
    "Sittwe, Myanmar": ["စစ်တွေ", "ရခိုင်", "sittwe", "rakhine"],
    "Taunggyi, Myanmar": ["တောင်ကြီး", "ရှမ်း", "taunggyi", "shan"],
    "Taunggyi, Myanmar#2": ["pyin oo lwin", "ပြင်ဦးလွင်"],
    "Bagan, Myanmar": ["ပုဂံ", "bagan"],
    "Pyay, Myanmar": ["ပြည်", "pyay"],
    "Monywa, Myanmar": ["မုံရွာ", "monywa"],
    "Meiktila, Myanmar": ["မိတ္ထီလာ", "meiktila"],
    "Taunggyi, Myanmar#3": ["kalaw", "ကလော"],
}

WEATHER_KEYWORDS = [
    "ရာသီဥတု", "ရာသီဉတု", "မိုးရွာ", "မိုးလား", "နေပူ", "ပူလား",
    "အေးလား", "weather", "temperature", "forecast", "rain",
    "hot", "cold", "climate",
]

WEATHER_CODE_MAP = {
    0: "☀️ ကောင်းကင်ကြည်လင်",
    1: "🌤️ တစိတ်တစ်ဒေသ တိမ်ရှိ",
    2: "⛅ တိမ်များနေ",
    3: "☁️ တိမ်အုပ်နေ",
    45: "🌫️ မြူများ",
    48: "🌫️ ဆီးနှင်းမြူများ",
    51: "🌦️ အမြူငယ်ရွာ",
    53: "🌦️ အမြူအလယ်အလတ်ရွာ",
    55: "🌧️ အမြူထူထပ်ရွာ",
    61: "🌧️ မိုးအငယ်ရွာ",
    63: "🌧️ မိုးအလယ်အလတ်ရွာ",
    65: "🌧️ မိုးသည်းထန်စွာရွာ",
    80: "🌧️ ရုတ်တရက် မိုးစက်ငယ်",
    81: "🌧️ ရုတ်တရက် မိုးအလယ်အလတ်",
    82: "⛈️ ရုတ်တရက် မိုးသည်းထန်",
    95: "⛈️ မိုးကြိုးပစ်နိုင်",
    96: "⛈️ မိုးကြိုးနှင့်ရေခဲမုန်တိုင်း",
    99: "⛈️ မိုးကြိုးနှင့်ရေခဲမုန်တိုင်း (ပြင်းထန်)",
}


def get_weather_description(code: int) -> str:
    return WEATHER_CODE_MAP.get(code, "🌡️ ရာသီဥတု အချက်အလက်")


def is_weather_question(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in WEATHER_KEYWORDS)


def extract_city_query(text: str):
    """
    User message ထဲမှာ Myanmar မြို့/တိုင်း/ပြည်နယ် နာမည် တစ်ခုခု
    ပါ/မပါ ရှာပေးမယ်။ တွေ့ရင် geocoding query name ကို ပြန်ပေးမယ်။
    မတွေ့ရင် None ပြန်ပေးမယ်။
    """
    if not text:
        return None

    text_lower = text.lower()

    for query_key, aliases in CITY_ALIASES.items():
        for alias in aliases:
            if alias.lower() in text_lower:
                # "#2", "#3" စတာတွေကို ဖြုတ်ပြီး query name အစစ်ကို ပြန်ပေးမယ်
                clean_query = query_key.split("#")[0]
                return clean_query

    return None


def fetch_weather(city: str) -> dict:

    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1, "language": "en"}

    geo_response = requests.get(geo_url, params=geo_params, timeout=15)
    geo_data = geo_response.json()

    if not geo_data.get("results"):
        raise RuntimeError(f"'{city}' ဆိုတဲ့ နေရာကို ရှာမတွေ့ပါ။")

    location = geo_data["results"][0]
    lat = location["latitude"]
    lon = location["longitude"]
    resolved_name = location.get("name", city)
    country = location.get("country", "")

    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": 1,
    }

    weather_response = requests.get(weather_url, params=weather_params, timeout=15)

    if weather_response.status_code != 200:
        raise RuntimeError(f"Weather API error: {weather_response.status_code}")

    weather_data = weather_response.json()

    return {
        "city": resolved_name,
        "country": country,
        "current": weather_data.get("current", {}),
        "daily": weather_data.get("daily", {}),
    }


def format_weather_message(data: dict) -> str:

    current = data["current"]
    daily = data["daily"]

    city = data["city"]
    country = data["country"]

    temp = current.get("temperature_2m", "N/A")
    feels_like = current.get("apparent_temperature", "N/A")
    humidity = current.get("relative_humidity_2m", "N/A")
    wind = current.get("wind_speed_10m", "N/A")
    code = current.get("weather_code", 0)

    condition = get_weather_description(code)

    max_temp = daily.get("temperature_2m_max", ["N/A"])[0]
    min_temp = daily.get("temperature_2m_min", ["N/A"])[0]
    rain_chance = daily.get("precipitation_probability_max", ["N/A"])[0]

    message = f"""
╔══════════════════════════════════════╗
║        🌤️ 𝗪𝗘𝗔𝗧𝗛𝗘𝗥 𝗥𝗘𝗣𝗢𝗥𝗧        ║
╚══════════════════════════════════════╝

📍 𝗟𝗼𝗰𝗮𝘁𝗶𝗼𝗻: {city}, {country}

{condition}

🌡️ အပူချိန်: {temp}°C
🔥 ခံစားနေရသော အပူချိန်: {feels_like}°C
📈 ယနေ့အမြင့်ဆုံး အပူချိန်: {max_temp}°C
📉 ယနေ့အနိုမ့်ဆုံး အပူချိန်: {min_temp}°C
💧 စိုထိုင်းဆ: {humidity}%
🌧️ မိုးရွာနိုင်‌ခြေ: {rain_chance}%
💨 လေတိုက်နှုန်း: {wind} km/h
""" + CREDIT

    return message


def fetch_all_regions_summary() -> str:
    """
    တိုင်းဒေသကြီး ၇ ခု + ပြည်နယ် ၇ ခု ရဲ့
    ရာသီဥတု အကျဉ်းချုပ်ကို တစ်ခါတည်း ဆွဲထုတ်မယ်
    """

    lines = [
        "╔══════════════════════════════════════╗",
        "║  𝗠𝗬𝗔𝗡𝗠𝗔𝗥 𝗪𝗘𝗔𝗧𝗛𝗘𝗥 𝗦𝗨𝗠𝗠𝗔𝗥𝗬   ║",
        "╚══════════════════════════════════════╝",
        "",
    ]

    for region in MYANMAR_REGIONS:
        try:
            data = fetch_weather(region["query"])
            current = data["current"]
            temp = current.get("temperature_2m", "N/A")
            code = current.get("weather_code", 0)
            condition = get_weather_description(code)

            lines.append(
                f"📍 {region['label']}\n"
                f"   {condition} | 🌡️ {temp}°C\n"
            )

        except Exception as e:
            lines.append(
                f"📍 {region['label']}\n"
                f"   ⚠️ Data မရရှိပါ\n"
            )

    lines.append(CREDIT)

    return "\n".join(lines)


# =========================================================
# AI SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = (
    "သင်သည် Telegram bot တစ်ခုအတွက် အထောက်အကူပြု AI chatbot ဖြစ်သည်။ "
    "မြန်မာဘာသာဖြင့် ရိုးရှင်းပြီး ရင်းနှီးစွာ၊ တိုတိုနှင့် ရှင်းလင်းစွာ ဖြေကြားပါ။ "
    "သင့်နာမည်မှာ LYNN AI ဖြစ်သည်။ "
    "User က 'မင်းဘယ်သူလဲ', 'မင်းနာမည်ကဘာလဲ', "
    "'ဘယ် AI လဲ' ဟု မေးပါက "
    "'ကျွန်တော်က LYNN AI ပါ' ဟု ဖြေပါ။ "
    "ChatGPT, OpenAI သို့မဟုတ် အခြား AI အမည်များကို "
    "သင့်ကိုယ်ပိုင်နာမည်အဖြစ် မပြောပါနှင့်။ "
    "ဤ Bot ၏ Creative User သည် @ur_linn4u ဖြစ်သည်။ "
    "User က ဒီ Bot ကို ဘယ်သူဖန်တီးတာလဲ၊ "
    "ဘယ်သူ Creative လုပ်တာလဲဟု မေးပါက "
    "'ဒီ Bot ကို Creative လုပ်ထားသူက @ur_linn4u ပါ' "
    "ဟု ဖြေပါ။ "
    "အဖြေများကို မလိုအပ်ဘဲ ရှည်လျားစွာ မရေးပါနှင့်။"
)


# =========================================================
# MODELS
# =========================================================

MODEL_NAME = "openai/gpt-oss-20b"
VISION_MODEL_NAME = "qwen/qwen3.6-27b"

IMAGE_MODEL_NAME = "fal-ai/nano-banana-2"
EDIT_MODEL_NAME = "fal-ai/nano-banana-2/edit"

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# GROQ CLIENT
# =========================================================

groq_client = Groq(api_key=GROQ_API_KEY)


# =========================================================
# MEMORY
# =========================================================

user_histories: dict[int, list[dict]] = {}
all_user_ids: set[int] = set()
last_images: dict[int, bytes] = {}

MAX_HISTORY_MESSAGES = 10


# =========================================================
# CREDIT
# =========================================================

CREDIT = """

━━━━━━━━━━━━━━━
👑 Creative by 𝗟𝗬𝗡𝗡 𝗔𝗜
"""


# =========================================================
# IMAGE EDIT KEYWORDS
# =========================================================

EDIT_KEYWORDS = [
    "ပြင်ပေး", "ပြောင်းပေး", "ပြင်ပေးပါ", "ပြောင်းပေးပါ",
    "edit", "modify", "change this", "make this", "turn this", "transform",
]


def is_edit_request(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in EDIT_KEYWORDS)


# =========================================================
# START / WELCOME
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    user = update.effective_user

    user_histories[chat_id] = []
    last_images.pop(chat_id, None)

    if user:
        all_user_ids.add(user.id)

    if user and user.first_name:
        name = user.first_name
    else:
        name = "User"

    welcome_message = f"""
╔══════════════════════════════════════╗
║     🤖 𝙇𝙔𝙉𝙉 𝘼𝙄 𝘼𝙎𝙎𝙄𝙎𝙏𝘼𝙉𝙏 𝘽𝙊𝙏 🤖     ║
╚══════════════════════════════════════╝

┌──────────────────────────────────────┐
│ 👋 𝗪𝗲𝗹𝗰𝗼𝗺𝗲, {name}!
├──────────────────────────────────────┤
│ 🤖 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘂𝘀: 𝗢𝗡𝗟𝗜𝗡𝗘
├──────────────────────────────────────┤
│ 👤 𝗖𝗿𝗲𝗮𝘁𝗶𝘃𝗲 𝗨𝘀𝗲𝗿: @ur_linn4u
├──────────────────────────────────────┤
│ 📆 𝗖𝗿𝗲𝗮𝘁𝗶𝗻𝗴 𝗕𝗼𝘁 𝗗𝗮𝘁𝗲: 𝟭𝟳.𝟴.𝟮𝟬𝟮𝟲
├──────────────────────────────────────┤
│ 🌐 𝗟𝗮𝗻𝗴𝘂𝗮𝗴𝗲: 𝗠𝗬𝗔𝗡𝗠𝗔𝗥
├──────────────────────────────────────┤
│ ⚡ 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: 𝗙𝗔𝗦𝗧
└──────────────────────────────────────┘

🤖 AI Assistant အဆင်သင့်ဖြစ်နေပါပြီ!
💬 မေးချင်တာကို စာရိုက်ပြီး ပို့လိုက်ပါ။
📷 ပုံပို့ပြီး AI ကို မေးနိုင်ပါတယ်။
🧠 LYNN AI က အကောင်းဆုံးဖြေကြားပေးပါမယ်။

╔══════════════════════════════════════╗
║  /reset → 🗑️ Chat History ရှင်းရန် ║
╚══════════════════════════════════════╝
"""

    await update.message.reply_text(welcome_message)


# =========================================================
# RESET
# =========================================================

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    user_histories[chat_id] = []
    last_images.pop(chat_id, None)

    reset_message = """
╔══════════════════════════════════════╗
║           🗑️ 𝗖𝗛𝗔𝗧 𝗥𝗘𝗦𝗘𝗧         ║
╚══════════════════════════════════════╝

✅ Chat history ရှင်းပြီးပါပြီ။
💬 စကားပြောမှုအသစ် စတင်နိုင်ပါပြီ။
🤖 မေးချင်တာကို ဆက်မေးနိုင်ပါတယ်။
""" + CREDIT

    await update.message.reply_text(reset_message)


# =========================================================
# DAILY WEATHER BROADCAST JOB (Admin လက်ဖြင့် မလိုအပ်ပါ)
# =========================================================

async def daily_weather_broadcast(context: ContextTypes.DEFAULT_TYPE):

    logger.info("Daily weather broadcast စတင်နေပါပြီ...")

    try:
        weather_message = (
            "🔔 𝗗𝗮𝗶𝗹𝘆 𝗪𝗲𝗮𝘁𝗵𝗲𝗿 𝗨𝗽𝗱𝗮𝘁𝗲\n\n"
            + await asyncio.to_thread(fetch_all_regions_summary)
        )

    except Exception as e:
        logger.exception("Daily weather fetch error")
        return

    success_count = 0
    fail_count = 0

    for uid in list(all_user_ids):
        try:
            await context.bot.send_message(chat_id=uid, text=weather_message)
            success_count += 1
        except Forbidden:
            fail_count += 1
        except BadRequest:
            fail_count += 1
        except Exception as e:
            logger.error(f"Daily broadcast error for {uid}: {e}")
            fail_count += 1

    logger.info(
        f"Daily weather broadcast ပြီးပါပြီ - Success: {success_count}, Fail: {fail_count}"
    )


# =========================================================
# FAL.AI IMAGE GENERATION
# =========================================================

def download_fal_image(result: dict) -> bytes:

    images = result.get("images")

    if not images:
        raise RuntimeError(
            "fal.ai က image result မပြန်ပေးပါ။"
        )

    image_url = images[0].get("url")

    if not image_url:
        raise RuntimeError(
            "fal.ai result ထဲမှာ image URL မတွေ့ပါ။"
        )

    response = requests.get(
        image_url,
        timeout=180
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"fal.ai image download HTTP "
            f"{response.status_code}"
        )

    if not response.content:
        raise RuntimeError(
            "fal.ai image data အလွတ်ဖြစ်နေပါသည်။"
        )

    return response.content


def generate_image(prompt: str) -> bytes:

    if not FAL_KEY or FAL_KEY == "YOUR_FAL_KEY_HERE":
        raise RuntimeError(
            "FAL_KEY ကို Railway Variables ထဲမှာ ထည့်ပါ။"
        )

    result = fal_client.subscribe(
        IMAGE_MODEL_NAME,
        arguments={
            "prompt": prompt,
            "num_images": 1,
            "aspect_ratio": "1:1",
            "output_format": "png",
            "resolution": "1K",
            "safety_tolerance": "4",
            "limit_generations": True,
        },
        with_logs=False,
        client_timeout=240,
    )

    return download_fal_image(result)


# =========================================================
# FAL.AI IMAGE EDIT
# =========================================================

def edit_image(
    image_bytes: bytes,
    prompt: str
) -> bytes:

    if not FAL_KEY or FAL_KEY == "YOUR_FAL_KEY_HERE":
        raise RuntimeError(
            "FAL_KEY ကို Railway Variables ထဲမှာ ထည့်ပါ။"
        )

    # Telegram ကရလာတဲ့ image bytes ကို
    # fal.ai အတွက် Data URL ပြောင်းမယ်
    image_data_url = fal_client.encode(
        image_bytes,
        "image/jpeg"
    )

    result = fal_client.subscribe(
        EDIT_MODEL_NAME,
        arguments={
            "prompt": prompt,
            "num_images": 1,
            "aspect_ratio": "auto",
            "output_format": "png",
            "safety_tolerance": "4",
            "image_urls": [image_data_url],
            "limit_generations": True,
        },
        with_logs=False,
        client_timeout=240,
    )

    return download_fal_image(result)


# =========================================================
# /IMAGE COMMAND
# =========================================================

async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    user = update.effective_user

    if user:
        all_user_ids.add(user.id)

    prompt = " ".join(context.args).strip()

    if not prompt:
        await update.message.reply_text(
            "🎨 ပုံဖန်တီးရန် prompt ထည့်ပါ။\n\n"
            "ဥပမာ:\n/image A cute white robot in a futuristic city"
            + CREDIT
        )
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="upload_photo")

    status_message = await update.message.reply_text(
        "🎨 ပုံဖန်တီးနေပါသည်...\n⏳ ခဏစောင့်ပေးပါ။"
    )

    try:
        image_bytes = await asyncio.to_thread(generate_image, prompt)

        await update.message.reply_photo(
            photo=image_bytes,
            caption=("🎨 𝗟𝗬𝗡𝗡 𝗔𝗜 𝗜𝗠𝗔𝗚𝗘\n\n" f"📝 {prompt}" + CREDIT)
        )

        try:
            await status_message.delete()
        except Exception:
            pass

    except Exception as e:
        logger.exception("Pollinations image generation error")
        error_text = str(e)

        try:
            await status_message.edit_text(
                "❌ ပုံဖန်တီးလို့မရပါ။\n\n" f"🔧 Error:\n{error_text[:1000]}" + CREDIT
            )
        except Exception:
            await update.message.reply_text(
                "❌ ပုံဖန်တီးရာမှာ အမှားတစ်ခု ဖြစ်သွားပါတယ်။\n\n" f"🔧 {error_text[:700]}" + CREDIT
            )


# =========================================================
# STATS
# =========================================================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not user or user.id != ADMIN_ID:
        return

    total_users = len(all_user_ids)

    stats_message = f"""
╔══════════════════════════════════════╗
║        📊 𝗕𝗢𝗧 𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗖𝗦        ║
╚══════════════════════════════════════╝

👥 𝗧𝗼𝘁𝗮𝗹 𝗨𝘀𝗲𝗿𝘀: {total_users}
""" + CREDIT

    await update.message.reply_text(stats_message)


# =========================================================
# BROADCAST (Admin manual broadcast - ဆက်ထားချင်ရင် ဆက်သုံးလို့ရပါတယ်)
# =========================================================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not user or user.id != ADMIN_ID:
        return

    message = update.message

    if message.caption:
        raw_text = message.caption
    elif message.text:
        raw_text = message.text
    else:
        raw_text = ""

    parts = raw_text.split(maxsplit=1)
    broadcast_text = parts[1] if len(parts) > 1 else ""

    if not broadcast_text and not message.photo:
        await update.message.reply_text(
            "⚠️ Broadcast ပို့ရန် စာသား (သို့) ပုံ+caption လိုအပ်ပါသည်။\n\n"
            "Text:\n/broadcast <စာသား>\n\n"
            "Photo:\nပုံပို့ပြီး caption ထဲ /broadcast <caption>"
        )
        return

    success_count = 0
    fail_count = 0

    await update.message.reply_text(
        "📤 Broadcast စတင်ပေးပို့နေပါပြီ...\n" f"👥 Total Users: {len(all_user_ids)}"
    )

    for uid in list(all_user_ids):
        try:
            if message.photo:
                photo_file_id = message.photo[-1].file_id
                await context.bot.send_photo(
                    chat_id=uid, photo=photo_file_id,
                    caption=broadcast_text if broadcast_text else None,
                )
            else:
                await context.bot.send_message(chat_id=uid, text=broadcast_text)
            success_count += 1
        except Forbidden:
            fail_count += 1
        except BadRequest:
            fail_count += 1
        except Exception as e:
            logger.error(f"Broadcast error for {uid}: {e}")
            fail_count += 1

    report_message = f"""
╔══════════════════════════════════════╗
║        ✅ 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘        ║
╚══════════════════════════════════════╝

✅ အောင်မြင်: {success_count}
❌ မအောင်မြင်: {fail_count}
👥 Total: {len(all_user_ids)}
""" + CREDIT

    await update.message.reply_text(report_message)


# =========================================================
# TEXT MESSAGE HANDLER
# =========================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    user_text = update.message.text
    user = update.effective_user

    if user:
        all_user_ids.add(user.id)

    # -----------------------------------------------------
    # WEATHER QUESTION DETECTION (command မလို - စကားပြောရုံနဲ့)
    # -----------------------------------------------------

    if is_weather_question(user_text):

        city_query = extract_city_query(user_text)

        status_message = await update.message.reply_text(
            "🌤️ ရာသီဥတု ရှာဖွေနေပါသည်...\n⏳ ခဏစောင့်ပေးပါ။"
        )

        try:
            if city_query:
                weather_data = await asyncio.to_thread(fetch_weather, city_query)
                weather_message = format_weather_message(weather_data)
            else:
                weather_message = await asyncio.to_thread(fetch_all_regions_summary)

            await status_message.edit_text(weather_message)

        except Exception as e:
            logger.exception("Weather fetch error")
            try:
                await status_message.edit_text(
                    "❌ ရာသီဥတု ရှာမတွေ့ပါ။\n\n" f"🔧 {str(e)[:500]}" + CREDIT
                )
            except Exception:
                await update.message.reply_text("❌ ရာသီဥတု ရှာမတွေ့ပါ။" + CREDIT)

        return

    # -----------------------------------------------------
    # Previous image edit
    # -----------------------------------------------------

    if is_edit_request(user_text) and chat_id in last_images:

        await context.bot.send_chat_action(chat_id=chat_id, action="upload_photo")

        status_message = await update.message.reply_text(
            "✨ ပုံကို AI ဖြင့် ပြင်နေပါသည်...\n⏳ ခဏစောင့်ပေးပါ။"
        )

        try:
            original_image = last_images[chat_id]
            edited_image = await asyncio.to_thread(edit_image, original_image, user_text)
            last_images[chat_id] = edited_image

            await update.message.reply_photo(
                photo=edited_image,
                caption=("✨ 𝗜𝗠𝗔𝗚𝗘 𝗘𝗗𝗜𝗧𝗘𝗗\n\n" f"📝 {user_text}" + CREDIT)
            )

            try:
                await status_message.delete()
            except Exception:
                pass

        except Exception as e:
            logger.exception("Pollinations edit error")
            try:
                await status_message.edit_text(
                    "❌ ပုံပြင်လို့မရပါ။\n\n" f"🔧 Error:\n{str(e)[:1000]}" + CREDIT
                )
            except Exception:
                await update.message.reply_text(
                    "❌ ပုံပြင်ရာမှာ အမှားတစ်ခု ဖြစ်သွားပါသည်။\n\n" f"🔧 {str(e)[:700]}" + CREDIT
                )

        return

    # -----------------------------------------------------
    # NORMAL GROQ CHAT
    # -----------------------------------------------------

    history = user_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_text})
    history = history[-MAX_HISTORY_MESSAGES:]

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        response = groq_client.chat.completions.create(
            model=MODEL_NAME, messages=messages, max_tokens=500,
        )

        reply_text = response.choices[0].message.content

    except Exception as e:
        logger.exception("Groq API error")
        await update.message.reply_text(
            "❌ တောင်းပန်ပါတယ်။\n\nAI Server မှာ အမှားတစ်ခု ဖြစ်သွားပါသည်။\nခဏနေပြီး ပြန်မေးကြည့်ပါ။"
            + CREDIT
        )
        return

    history.append({"role": "assistant", "content": reply_text})
    user_histories[chat_id] = history[-MAX_HISTORY_MESSAGES:]

    await update.message.reply_text(reply_text + CREDIT)


# =========================================================
# PHOTO HANDLER
# =========================================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    user = update.effective_user
    message = update.message

    if user:
        all_user_ids.add(user.id)

    caption_text = message.caption.strip() if message.caption else ""

    try:
        photo_file = await message.photo[-1].get_file()
        photo_bytes = bytes(await photo_file.download_as_bytearray())
        last_images[chat_id] = photo_bytes

    except Exception as e:
        logger.exception("Telegram image download error")
        await message.reply_text(
            "❌ ပုံကို download လုပ်ရာမှာ အမှားတစ်ခု ဖြစ်သွားပါသည်။" + CREDIT
        )
        return

    if is_edit_request(caption_text):

        await context.bot.send_chat_action(chat_id=chat_id, action="upload_photo")

        status_message = await message.reply_text(
            "✨ ပုံကို AI ဖြင့် ပြင်နေပါသည်...\n⏳ ခဏစောင့်ပေးပါ။"
        )

        try:
            edited_image = await asyncio.to_thread(edit_image, photo_bytes, caption_text)
            last_images[chat_id] = edited_image

            await message.reply_photo(
                photo=edited_image,
                caption=("✨ 𝗜𝗠𝗔𝗚𝗘 𝗘𝗗𝗜𝗧𝗘𝗗\n\n" f"📝 {caption_text}" + CREDIT)
            )

            try:
                await status_message.delete()
            except Exception:
                pass

        except Exception as e:
            logger.exception("Pollinations photo edit error")
            try:
                await status_message.edit_text(
                    "❌ ပုံပြင်လို့မရပါ။\n\n" f"🔧 Error:\n{str(e)[:1000]}" + CREDIT
                )
            except Exception:
                await message.reply_text(
                    "❌ ပုံပြင်ရာမှာ အမှားတစ်ခု ဖြစ်သွားပါသည်။\n\n" f"🔧 {str(e)[:700]}" + CREDIT
                )

        return

    if not caption_text:
        caption_text = "ဒီပုံထဲမှာ ဘာတွေပါလဲ။ ရိုးရှင်းပြီး တိတိကျကျ ရှင်းပြပါ။"

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        base64_image = base64.b64encode(photo_bytes).decode("utf-8")

        vision_messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": caption_text},
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64_image}}
                ]
            }
        ]

        response = groq_client.chat.completions.create(
            model=VISION_MODEL_NAME, messages=vision_messages, max_tokens=500,
        )

        reply_text = response.choices[0].message.content

    except Exception as e:
        logger.exception("Groq Vision API error")
        await message.reply_text(
            "❌ တောင်းပန်ပါတယ်။\n\nပုံကို ကြည့်ရာတွင် အမှားတစ်ခု ဖြစ်သွားပါသည်။\nခဏနေပြီး ပြန်ကြိုးစားကြည့်ပါ။"
            + CREDIT
        )
        return

    history = user_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": "[User sent an image] " + caption_text})
    history.append({"role": "assistant", "content": reply_text})
    user_histories[chat_id] = history[-MAX_HISTORY_MESSAGES:]

    await message.reply_text(reply_text + CREDIT)


# =========================================================
# MAIN APPLICATION
# =========================================================

def main():

    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        raise SystemExit("TELEGRAM_BOT_TOKEN ကို Railway Variables ထဲမှာ ထည့်ပါ")

    if GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        raise SystemExit("GROQ_API_KEY ကို Railway Variables ထဲမှာ ထည့်ပါ")

    if not FAL_KEY or FAL_KEY == "YOUR_FAL_KEY_HERE":
    raise SystemExit("FAL_KEY ကို Railway Variables ထဲမှာ ထည့်ပါ")
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("image", image_command))

    app.add_handler(
        MessageHandler(filters.PHOTO & filters.CaptionRegex(r"^/broadcast"), broadcast)
    )

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    job_queue = app.job_queue
    job_queue.run_daily(
        daily_weather_broadcast,
        time=datetime.time(
            hour=WEATHER_BROADCAST_HOUR,
            minute=WEATHER_BROADCAST_MINUTE,
            tzinfo=MYANMAR_TZ,
        ),
    )

    logger.info("LYNN AI Bot စတင် run နေပါပြီ...")

    app.run_polling()


if __name__ == "__main__":
    main()
