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
import anthropic

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY_HERE")

SYSTEM_PROMPT = (
    "သင်သည် Telegram bot တစ်ခုအတွက် အထောက်အကူပြု AI chatbot တစ်ခုဖြစ်သည်။ "
    "မြန်မာဘာသာဖြင့် ရိုးရှင်းပြီး ရင်းနှီးစွာ၊ တိုတိုနှင့် ရှင်းလင်းစွာ ဖြေကြားပါ။"
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

user_histories: dict[int, list[dict]] = {}
MAX_HISTORY_MESSAGES = 10


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_chat.id] = []
    await update.message.reply_text(
        "မင်္ဂလာပါ! ကျွန်တော် AI chatbot ဖြစ်ပါတယ်။ ဘာမေးချင်လဲ မေးလို့ရပါတယ်။\n\n"
        "/reset - စကားပြော history ကို ပြန်ရှင်းရန်"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_chat.id] = []
    await update.message.reply_text("Conversation history ကို ရှင်းလိုက်ပါပြီ။")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text

    history = user_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_text})
    history = history[-MAX_HISTORY_MESSAGES:]

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        response = claude_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply_text = response.content[0].text
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        await update.message.reply_text(
            "တောင်းပန်ပါတယ်၊ အမှားတစ်ခုဖြစ်သွားပါတယ်။ နောက်တစ်ခါ ထပ်ကြိုးစားကြည့်ပါ။"
        )
        return

    history.append({"role": "assistant", "content": reply_text})
    user_histories[chat_id] = history

    await update.message.reply_text(reply_text)


def main():
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        raise SystemExit("TELEGRAM_BOT_TOKEN ကို Railway Variables ထဲမှာ ထည့်ပါ")
    if ANTHROPIC_API_KEY == "YOUR_ANTHROPIC_API_KEY_HERE":
        raise SystemExit("ANTHROPIC_API_KEY ကို Railway Variables ထဲမှာ ထည့်ပါ")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot စတင် run နေပါပြီ...")
    app.run_polling()


if __name__ == "__main__":
    main()
