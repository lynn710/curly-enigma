# -*- coding: utf-8 -*-

import os
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from groq import Groq


TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    "YOUR_TELEGRAM_BOT_TOKEN_HERE"
)

GROQ_API_KEY = os.environ.get(
    "GROQ_API_KEY",
    "YOUR_GROQ_API_KEY_HERE"
)


SYSTEM_PROMPT = (
    "သင်သည် Telegram bot တစ်ခုအတွက် အထောက်အကူပြု AI chatbot တစ်ခုဖြစ်သည်။ "
    "မြန်မာဘာသာဖြင့် ရိုးရှင်းပြီး ရင်းနှီးစွာ၊ တိုတိုနှင့် တိကျရှင်းလင်းစွာ ဖြေကြားပါ။"
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


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

groq_client = Groq(api_key=GROQ_API_KEY)

user_histories: dict[int, list[dict]] = {}

MAX_HISTORY_MESSAGES = 10


# START / WELCOME MESSAGE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    user = update.effective_user

    user_histories[chat_id] = []

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


# AI MESSAGE HANDLER

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id
    user_text = update.message.text

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
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    logger.info("LYNN AI Bot စတင် run နေပါပြီ...")

    app.run_polling()


if __name__ == "__main__":
    main()
