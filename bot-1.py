# -*- coding: utf-8 -*-

import os
import base64
import logging

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


TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    "YOUR_TELEGRAM_BOT_TOKEN_HERE"
)

GROQ_API_KEY = os.environ.get(
    "GROQ_API_KEY",
    "YOUR_GROQ_API_KEY_HERE"
)

# Admin User ID
ADMIN_ID = 6908674664


SYSTEM_PROMPT = (
    "သင်သည် Telegram bot တစ်ခုအတွက် အထောက်အကူပြု AI chatbot တစ်ခုဖြစ်သည်။ "
    "မြန်မာဘာသာဖြင့် ရိုးရှင်းပြီး ရင်းနှီးစွာ၊ တိုတိုနှင့် ရှင်းလင်းစွာ ဖြေကြားပါ။"
    "သင့်နာမည်မှာ LYNN AI ဖြစ်သည်။ "
    "User က 'မင်းဘယ်သူလဲ', 'မင်းနာမည်ကဘာလဲ', 'ဘယ် AI လဲ' ဟု မေးပါက "
    "'ကျွန်တော်က LYNN AI ပါ' ဟု ဖြေပါ။ "
    "ChatGPT, OpenAI သို့မဟုတ် အခြား AI အမည်များကို "
    "သင့်ကိုယ်ပိုင်နာမည်အဖြစ် မပြောပါနှင့်။ "
    "ဤ Bot ၏ Creative User သည် @ur_linn4u ဖြစ်သည်။ "
    "User က ဒီ Bot ကို ဘယ်သူဖန်တီးတာလဲ၊ ဘယ်သူ Creative လုပ်တာလဲဟု မေးပါက "
    "'ဒီ Bot ကို Creative လုပ်ထားသူက @ur_linn4u ပါ' ဟု ဖြေပါ။ "
)

MODEL_NAME = "openai/gpt-oss-20b"
VISION_MODEL_NAME = "qwen/qwen3.6-27b"


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

groq_client = Groq(api_key=GROQ_API_KEY)

user_histories: dict[int, list[dict]] = {}

all_user_ids: set[int] = set()

MAX_HISTORY_MESSAGES = 10


# START / WELCOME MESSAGE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    user = update.effective_user

    user_histories[chat_id] = []

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
📷 ပုံလည်း ပို့လို့ရပါတယ် - AI က ပုံကို ကြည့်ပြီး ဖြေပေးပါမယ်။
🧠 AI က အကောင်းဆုံးဖြေကြားပေးပါမယ်။

╔══════════════════════════════════════╗
║  /reset → 🗑️ Chat History ရှင်းရန် ║
╚══════════════════════════════════════╝
"""

    await update.message.reply_text(welcome_message)


# RESET COMMAND

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    user_histories[chat_id] = []

    reset_message = """
╔══════════════════════════════════════╗
║           🗑️ 𝗖𝗛𝗔𝗧 𝗥𝗘𝗦𝗘𝗧         ║
╚══════════════════════════════════════╝

✅ Chat history ရှင်းပြီးပါပြီ။
💬 စကားပြောမှုအသစ် စတင်နိုင်ပါပြီ။
🤖 မေးချင်တာကို ဆက်မေးနိုင်ပါတယ်။

━━━━━━━━━━━━━━━
👑 Creative by 𝗟𝗬𝗡𝗡 𝗔𝗜
"""

    await update.message.reply_text(reset_message)


# STATS COMMAND (Admin ချည်း)

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

━━━━━━━━━━━━━━━
👑 Admin Panel - 𝗟𝗬𝗡𝗡 𝗔𝗜
"""

    await update.message.reply_text(stats_message)


# BROADCAST COMMAND (Admin ချည်း)

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
            "Text: /broadcast <စာသား>\n"
            "Photo: ပုံပို့ပြီး caption ထဲ /broadcast <caption>"
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
                photo_file_id = message.photo[-1].file_id
                await context.bot.send_photo(
                    chat_id=uid,
                    photo=photo_file_id,
                    caption=broadcast_text if broadcast_text else None,
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
            logger.error(f"Broadcast error for {uid}: {e}")
            fail_count += 1

    report_message = f"""
╔══════════════════════════════════════╗
║        ✅ 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘        ║
╚══════════════════════════════════════╝

✅ အောင်မြင်: {success_count}
❌ မအောင်မြင်: {fail_count}
👥 Total: {len(all_user_ids)}

━━━━━━━━━━━━━━━
👑 Admin Panel - 𝗟𝗬𝗡𝗡 𝗔𝗜
"""

    await update.message.reply_text(report_message)


# AI TEXT MESSAGE HANDLER

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id
    user_text = update.message.text
    user = update.effective_user

    if user:
        all_user_ids.add(user.id)

    history = user_histories.setdefault(chat_id, [])

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
            max_tokens=1000,
        )

        reply_text = response.choices[0].message.content

    except Exception as e:

        logger.error(f"Groq API error: {e}")

        error_message = """
❌ တောင်းပန်ပါတယ်။

AI Server မှာ အမှားတစ်ခု ဖြစ်သွားပါတယ်။
ခဏနေပြီး ပြန်မေးကြည့်ပါ။

━━━━━━━━━━━━━━━
👑 Creative by 𝗟𝗬𝗡𝗡 𝗔𝗜
"""

        await update.message.reply_text(error_message)

        return

    history.append({
        "role": "assistant",
        "content": reply_text
    })

    user_histories[chat_id] = history

    credit = """
    
━━━━━━━━━━━━━━━
👑 Creative by 𝗟𝗬𝗡𝗡 𝗔𝗜
"""

    final_reply = reply_text + credit

    await update.message.reply_text(final_reply)


# AI IMAGE (VISION) HANDLER
# User ပုံပို့တဲ့အခါ (broadcast command မဟုတ်တဲ့ ပုံများ) ဒီ function က AI ကို ပုံကို ကြည့်ခိုင်းမယ်

async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id
    user = update.effective_user
    message = update.message

    if user:
        all_user_ids.add(user.id)

    caption_text = message.caption if message.caption else "ဒီပုံထဲမှာ ဘာတွေပါလဲ ရှင်းပြပါ။"

    await context.bot.send_chat_action(
        chat_id=chat_id,
        action="typing"
    )

    try:
        # ပုံအကြီးဆုံး resolution ကို ယူပြီး download လုပ်မယ်
        photo_file = await message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        base64_image = base64.b64encode(photo_bytes).decode("utf-8")

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
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]

        response = groq_client.chat.completions.create(
            model=VISION_MODEL_NAME,
            messages=vision_messages,
            max_tokens=1000,
        )

        reply_text = response.choices[0].message.content

    except Exception as e:

        logger.error(f"Groq Vision API error: {e}")

        error_message = """
❌ တောင်းပန်ပါတယ်။

ပုံကို ကြည့်ရာတွင် အမှားတစ်ခု ဖြစ်သွားပါတယ်။
ခဏနေပြီး ပြန်ကြိုးစားကြည့်ပါ။

━━━━━━━━━━━━━━━
👑 Creative by 𝗟𝗬𝗡𝗡 𝗔𝗜
"""

        await update.message.reply_text(error_message)

        return

    # Conversation history ထဲမှာ ပုံအကြောင်း မှတ်ထားမယ် (context ဆက်ရအောင်)
    history = user_histories.setdefault(chat_id, [])
    history.append({
        "role": "user",
        "content": f"[User sent an image] {caption_text}"
    })
    history.append({
        "role": "assistant",
        "content": reply_text
    })
    user_histories[chat_id] = history[-MAX_HISTORY_MESSAGES:]

    credit = """
    
━━━━━━━━━━━━━━━
👑 Creative by 𝗟𝗬𝗡𝗡 𝗔𝗜
"""

    final_reply = reply_text + credit

    await update.message.reply_text(final_reply)


# MAIN APPLICATION

def main():

    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN ကို Railway Variables ထဲမှာ ထည့်ပါ"
        )

    if GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        raise SystemExit(
            "GROQ_API_KEY ကို Railway Variables ထဲမှာ ထည့်ပါ"
        )

    app = ApplicationBuilder().token(
        TELEGRAM_BOT_TOKEN
    ).build()

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

    # Admin ပုံ+caption "/broadcast" ပို့ရင် broadcast function ကို ခေါ်မယ်
    app.add_handler(
        MessageHandler(
            filters.PHOTO & filters.CaptionRegex(r'^/broadcast'),
            broadcast
        )
    )

    # User ပုံ (broadcast မဟုတ်တဲ့) ပို့ရင် AI Vision function ကို ခေါ်မယ်
    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    logger.info("LYNN AI Bot စတင် run နေပါပြီ...")

    app.run_polling()


if __name__ == "__main__":
    main()
