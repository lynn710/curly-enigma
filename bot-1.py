# -*- coding: utf-8 -*-

import os
import base64
import logging
import requests

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
    "TELEGRAM_BOT_TOKEN",
    "YOUR_TELEGRAM_BOT_TOKEN_HERE"
)

GROQ_API_KEY = os.environ.get(
    "GROQ_API_KEY",
    "YOUR_GROQ_API_KEY_HERE"
)

POLLINATIONS_API_KEY = os.environ.get(
    "POLLINATIONS_API_KEY",
    "YOUR_POLLINATIONS_API_KEY_HERE"
)


# =========================================================
# ADMIN
# =========================================================

ADMIN_ID = 6908674664


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
    "'ဒီ Bot ကို Creative လုပ်ထားသူက @ur_linn4u ပါ 👑' "
    "ဟု ဖြေပါ။ "

)


# =========================================================
# MODELS
# =========================================================

MODEL_NAME = "openai/gpt-oss-20b"

VISION_MODEL_NAME = "qwen/qwen3.6-27b"

# Pollinations image model
IMAGE_MODEL_NAME = "flux"

# Pollinations editing model
EDIT_MODEL_NAME = "p-image-edit"


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# CLIENT
# =========================================================

groq_client = Groq(api_key=GROQ_API_KEY)


# =========================================================
# MEMORY
# =========================================================

user_histories: dict[int, list[dict]] = {}

all_user_ids: set[int] = set()

# User တစ်ယောက်စီရဲ့ နောက်ဆုံးပုံ
last_images: dict[int, bytes] = {}

MAX_HISTORY_MESSAGES = 10


# =========================================================
# FOOTER
# =========================================================

CREDIT = """

━━━━━━━━━━━━━━━
👑 Creative by 𝗟𝗬𝗡𝗡 𝗔𝗜
"""


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id
    user = update.effective_user

    user_histories[chat_id] = []

    # Start လုပ်တဲ့အချိန် old image ကိုရှင်း
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

💬 စာပို့ပြီး မေးနိုင်ပါတယ်။
📷 ပုံပို့ပြီး AI ကို မေးနိုင်ပါတယ်။
🎨 /image <prompt> နဲ့ ပုံအသစ်ဖန်တီးနိုင်ပါတယ်။
✨ ပုံပို့ပြီး "ပြင်ပေး" လို့ပြောရင် ပုံကို AI နဲ့ ပြင်ပေးပါမယ်။

🧠 LYNN AI က အကောင်းဆုံးဖြေကြားပေးပါမယ်။

╔══════════════════════════════════════╗
║  /reset → 🗑️ Chat History ရှင်းရန် ║
╚══════════════════════════════════════╝
"""

    await update.message.reply_text(welcome_message)


# =========================================================
# RESET
# =========================================================

async def reset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    user_histories[chat_id] = []

    # နောက်ဆုံးမှတ်ထားတဲ့ပုံပါ ရှင်း
    last_images.pop(chat_id, None)

    reset_message = """
╔══════════════════════════════════════╗
║           🗑️ 𝗖𝗛𝗔𝗧 𝗥𝗘𝗦𝗘𝗧         ║
╚══════════════════════════════════════╝

✅ Chat history ရှင်းပြီးပါပြီ။
🖼️ မှတ်ထားတဲ့နောက်ဆုံးပုံလည်း ရှင်းပြီးပါပြီ။
💬 စကားပြောမှုအသစ် စတင်နိုင်ပါပြီ။
🤖 မေးချင်တာကို ဆက်မေးနိုင်ပါတယ်။
""" + CREDIT

    await update.message.reply_text(reset_message)


# =========================================================
# IMAGE GENERATION
# =========================================================

async def generate_image(prompt: str) -> bytes:

    url = "https://gen.pollinations.ai/v1/images/generations"

    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": IMAGE_MODEL_NAME,
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1,
        "response_format": "b64_json",
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=180,
    )

    response.raise_for_status()

    data = response.json()

    image_data = data["data"][0]

    if image_data.get("b64_json"):
        return base64.b64decode(image_data["b64_json"])

    # URL response ဖြစ်ရင်လည်း support
    if image_data.get("url"):
        image_response = requests.get(
            image_data["url"],
            timeout=180,
        )

        image_response.raise_for_status()

        return image_response.content

    raise RuntimeError("Pollinations က image data မပြန်ပေးပါ။")


# =========================================================
# IMAGE EDITING
# =========================================================

async def edit_image(
    image_bytes: bytes,
    prompt: str
) -> bytes:

    url = "https://gen.pollinations.ai/v1/images/edits"

    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json",
    }

    # Telegram ကရတဲ့ image ကို base64 data URI ပြောင်း
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    image_data_uri = (
        f"data:image/jpeg;base64,{base64_image}"
    )

    payload = {
        "model": EDIT_MODEL_NAME,
        "prompt": prompt,
        "image": image_data_uri,
        "n": 1,
        "response_format": "b64_json",
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=180,
    )

    response.raise_for_status()

    data = response.json()

    image_data = data["data"][0]

    if image_data.get("b64_json"):
        return base64.b64decode(
            image_data["b64_json"]
        )

    if image_data.get("url"):

        image_response = requests.get(
            image_data["url"],
            timeout=180,
        )

        image_response.raise_for_status()

        return image_response.content

    raise RuntimeError(
        "Pollinations က edited image data မပြန်ပေးပါ။"
    )


# =========================================================
# /IMAGE COMMAND
# =========================================================

async def image_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id
    user = update.effective_user

    if user:
        all_user_ids.add(user.id)

    prompt = " ".join(context.args).strip()

    if not prompt:

        await update.message.reply_text(
            "🎨 ပုံဖန်တီးရန် prompt ထည့်ပါ။\n\n"
            "ဥပမာ:\n"
            "/image A cute robot in a futuristic city"
            + CREDIT
        )

        return

    await context.bot.send_chat_action(
        chat_id=chat_id,
        action="upload_photo"
    )

    status_message = await update.message.reply_text(
        "🎨 ပုံဖန်တီးနေပါသည်...\n"
        "⏳ ခဏစောင့်ပေးပါ။"
    )

    try:

        image_bytes = await __import__(
            "asyncio"
        ).to_thread(
            generate_image,
            prompt
        )

        await status_message.delete()

        await update.message.reply_photo(
            photo=image_bytes,
            caption=(
                "🎨 𝗟𝗬𝗡𝗡 𝗔𝗜 𝗜𝗠𝗔𝗚𝗘\n\n"
                f"📝 {prompt}"
                + CREDIT
            )
        )

    except Exception as e:

        logger.error(
            f"Pollinations image error: {e}"
        )

        await status_message.edit_text(
            "❌ ပုံဖန်တီးရာမှာ အမှားတစ်ခု ဖြစ်သွားပါသည်။\n\n"
            "ခဏနေပြီး ပြန်ကြိုးစားကြည့်ပါ။"
            + CREDIT
        )


# =========================================================
# STATS
# =========================================================

async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
# BROADCAST
# =========================================================

async def broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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

    broadcast_text = (
        parts[1]
        if len(parts) > 1
        else ""
    )

    if not broadcast_text and not message.photo:

        await update.message.reply_text(
            "⚠️ Broadcast ပို့ရန် စာသား "
            "(သို့) ပုံ+caption လိုအပ်ပါသည်။\n\n"
            "Text: /broadcast <စာသား>\n"
            "Photo: ပုံပို့ပြီး caption ထဲ "
            "/broadcast <caption>"
        )

        return

    success_count = 0
    fail_count = 0

    await update.message.reply_text(
        f"📤 Broadcast စတင်ပေးပို့နေပါပြီ...\n"
        f"👥 Total Users: {len(all_user_ids)}"
    )

    for uid in list(all_user_ids):

        try:

            if message.photo:

                photo_file_id = (
                    message.photo[-1].file_id
                )

                await context.bot.send_photo(
                    chat_id=uid,
                    photo=photo_file_id,
                    caption=(
                        broadcast_text
                        if broadcast_text
                        else None
                    ),
                )

            else:

                await context.bot.send_message(
                    chat_id=uid,
                    text=broadcast_text,
                )

            success_count += 1

        except Forbidden:

            fail_count += 1

        except BadRequest:

            fail_count += 1

        except Exception as e:

            logger.error(
                f"Broadcast error for {uid}: {e}"
            )

            fail_count += 1

    report_message = f"""
╔══════════════════════════════════════╗
║        ✅ 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘        ║
╚══════════════════════════════════════╝

✅ အောင်မြင်: {success_count}
❌ မအောင်မြင်: {fail_count}
👥 Total: {len(all_user_ids)}
""" + CREDIT

    await update.message.reply_text(
        report_message
    )


# =========================================================
# TEXT MESSAGE HANDLER
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id
    user_text = update.message.text
    user = update.effective_user

    if user:
        all_user_ids.add(user.id)

    # -----------------------------------------------------
    # Previous image ကို edit လုပ်ချင်တာလား စစ်မယ်
    # -----------------------------------------------------

    edit_keywords = [
        "ပြင်ပေး",
        "ပြောင်းပေး",
        "ပြင်ပေးပါ",
        "ပြောင်းပေးပါ",
        "edit",
        "modify",
        "change this",
        "make this",
        "turn this",
        "transform",
    ]

    is_edit_request = any(
        keyword in user_text.lower()
        for keyword in edit_keywords
    )

    if is_edit_request and chat_id in last_images:

        await context.bot.send_chat_action(
            chat_id=chat_id,
            action="upload_photo"
        )

        status_message = await update.message.reply_text(
            "✨ ပုံကို AI နဲ့ ပြင်နေပါသည်...\n"
            "⏳ ခဏစောင့်ပေးပါ။"
        )

        try:

            original_image = last_images[chat_id]

            edited_image = await __import__(
                "asyncio"
            ).to_thread(
                edit_image,
                original_image,
                user_text
            )

            # edited image ကို latest image အဖြစ်သိမ်း
            last_images[chat_id] = edited_image

            await status_message.delete()

            await update.message.reply_photo(
                photo=edited_image,
                caption=(
                    "✨ 𝗜𝗠𝗔𝗚𝗘 𝗘𝗗𝗜𝗧𝗘𝗗\n\n"
                    f"📝 {user_text}"
                    + CREDIT
                )
            )

        except Exception as e:

            logger.error(
                f"Pollinations edit error: {e}"
            )

            await status_message.edit_text(
                "❌ ပုံပြင်ရာမှာ အမှားတစ်ခု ဖြစ်သွားပါသည်။\n\n"
                "ခဏနေပြီး ပြန်ကြိုးစားကြည့်ပါ။"
                + CREDIT
            )

        return

    # -----------------------------------------------------
    # Normal AI Chat
    # -----------------------------------------------------

    history = user_histories.setdefault(
        chat_id,
        []
    )

    history.append({
        "role": "user",
        "content": user_text
    })

    history = history[-MAX_HISTORY_MESSAGES:]

    await context.bot.send_chat_action(
        chat_id=chat_id,
        action="typing"
    )

    try:

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ] + history

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=500,
        )

        reply_text = (
            response.choices[0]
            .message.content
        )

    except Exception as e:

        logger.error(
            f"Groq API error: {e}"
        )

        await update.message.reply_text(
            "❌ တောင်းပန်ပါတယ်။\n\n"
            "AI Server မှာ အမှားတစ်ခု ဖြစ်သွားပါသည်။\n"
            "ခဏနေပြီး ပြန်မေးကြည့်ပါ။"
            + CREDIT
        )

        return

    history.append({
        "role": "assistant",
        "content": reply_text
    })

    user_histories[chat_id] = (
        history[-MAX_HISTORY_MESSAGES:]
    )

    await update.message.reply_text(
        reply_text + CREDIT
    )


# =========================================================
# PHOTO HANDLER
# =========================================================

async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id
    user = update.effective_user
    message = update.message

    if user:
        all_user_ids.add(user.id)

    caption_text = (
        message.caption.strip()
        if message.caption
        else ""
    )

    # -----------------------------------------------------
    # Download image
    # -----------------------------------------------------

    try:

        photo_file = await message.photo[-1].get_file()

        photo_bytes = bytes(
            await photo_file.download_as_bytearray()
        )

        # နောက်ဆုံးပုံအဖြစ် သိမ်းထားမယ်
        last_images[chat_id] = photo_bytes

    except Exception as e:

        logger.error(
            f"Telegram image download error: {e}"
        )

        await message.reply_text(
            "❌ ပုံကို download လုပ်ရာမှာ "
            "အမှားတစ်ခု ဖြစ်သွားပါသည်။"
            + CREDIT
        )

        return

    # -----------------------------------------------------
    # Caption က image edit request လား?
    # -----------------------------------------------------

    edit_keywords = [
        "ပြင်ပေး",
        "ပြောင်းပေး",
        "ပြင်ပေးပါ",
        "ပြောင်းပေးပါ",
        "edit",
        "modify",
        "change this",
        "make this",
        "turn this",
        "transform",
    ]

    is_edit_request = (
        any(
            keyword in caption_text.lower()
            for keyword in edit_keywords
        )
        if caption_text
        else False
    )

    # -----------------------------------------------------
    # IMAGE EDIT
    # -----------------------------------------------------

    if is_edit_request:

        await context.bot.send_chat_action(
            chat_id=chat_id,
            action="upload_photo"
        )

        status_message = await message.reply_text(
            "✨ ပုံကို AI နဲ့ ပြင်နေပါသည်...\n"
            "⏳ ခဏစောင့်ပေးပါ။"
        )

        try:

            edited_image = await __import__(
                "asyncio"
            ).to_thread(
                edit_image,
                photo_bytes,
                caption_text
            )

            last_images[chat_id] = edited_image

            await status_message.delete()

            await message.reply_photo(
                photo=edited_image,
                caption=(
                    "✨ 𝗜𝗠𝗔𝗚𝗘 𝗘𝗗𝗜𝗧𝗘𝗗\n\n"
                    f"📝 {caption_text}"
                    + CREDIT
                )
            )

        except Exception as e:

            logger.error(
                f"Pollinations edit error: {e}"
            )

            await status_message.edit_text(
                "❌ ပုံပြင်ရာမှာ အမှားတစ်ခု ဖြစ်သွားပါသည်။\n\n"
                "ခဏနေပြီး ပြန်ကြိုးစားကြည့်ပါ။"
                + CREDIT
            )

        return

    # -----------------------------------------------------
    # IMAGE VISION ANALYSIS
    # -----------------------------------------------------

    if not caption_text:

        caption_text = (
            "ဒီပုံထဲမှာ ဘာတွေပါလဲ "
            "ရိုးရှင်းပြီး တိတိကျကျ ရှင်းပြပါ။"
        )

    await context.bot.send_chat_action(
        chat_id=chat_id,
        action="typing"
    )

    try:

        base64_image = (
            base64.b64encode(photo_bytes)
            .decode("utf-8")
        )

        vision_messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": caption_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                "data:image/jpeg;base64,"
                                + base64_image
                            )
                        }
                    }
                ]
            }
        ]

        response = groq_client.chat.completions.create(
            model=VISION_MODEL_NAME,
            messages=vision_messages,
            max_tokens=500,
        )

        reply_text = (
            response.choices[0]
            .message.content
        )

    except Exception as e:

        logger.error(
            f"Groq Vision API error: {e}"
        )

        await message.reply_text(
            "❌ တောင်းပန်ပါတယ်။\n\n"
            "ပုံကို ကြည့်ရာတွင် အမှားတစ်ခု ဖြစ်သွားပါသည်။\n"
            "ခဏနေပြီး ပြန်ကြိုးစားကြည့်ပါ။"
            + CREDIT
        )

        return

    # -----------------------------------------------------
    # History
    # -----------------------------------------------------

    history = user_histories.setdefault(
        chat_id,
        []
    )

    history.append({
        "role": "user",
        "content": (
            f"[User sent an image] "
            f"{caption_text}"
        )
    })

    history.append({
        "role": "assistant",
        "content": reply_text
    })

    user_histories[chat_id] = (
        history[-MAX_HISTORY_MESSAGES:]
    )

    await message.reply_text(
        reply_text + CREDIT
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if (
        TELEGRAM_BOT_TOKEN
        == "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    ):

        raise SystemExit(
            "TELEGRAM_BOT_TOKEN ကို "
            "Railway Variables ထဲမှာ ထည့်ပါ"
        )

    if (
        GROQ_API_KEY
        == "YOUR_GROQ_API_KEY_HERE"
    ):

        raise SystemExit(
            "GROQ_API_KEY ကို "
            "Railway Variables ထဲမှာ ထည့်ပါ"
        )

    if (
        POLLINATIONS_API_KEY
        == "YOUR_POLLINATIONS_API_KEY_HERE"
    ):

        raise SystemExit(
            "POLLINATIONS_API_KEY ကို "
            "Railway Variables ထဲမှာ ထည့်ပါ"
        )

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # -----------------------------------------------------
    # COMMANDS
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("reset", reset)
    )

    app.add_handler(
        CommandHandler("stats", stats)
    )

    app.add_handler(
        CommandHandler("broadcast", broadcast)
    )

    app.add_handler(
        CommandHandler("image", image_command)
    )

    # -----------------------------------------------------
    # ADMIN BROADCAST PHOTO
    # -----------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.PHOTO
            & filters.CaptionRegex(
                r"^/broadcast"
            ),
            broadcast
        )
    )

    # -----------------------------------------------------
    # PHOTO
    # -----------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo
        )
    )

    # -----------------------------------------------------
    # TEXT
    # -----------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            handle_message
        )
    )

    logger.info(
        "LYNN AI Bot စတင် run နေပါပြီ..."
    )

    app.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
