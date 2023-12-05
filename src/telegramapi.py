# %%
import os
from chat import ChatSession
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes
from dotenv import load_dotenv
import logging

load_dotenv()


sessions: dict[any, ChatSession] = {}


def getsession(ctx, chat_id):
    if chat_id not in sessions:
        sessions[chat_id] = ChatSession(ctx, chat_id)
    return sessions.get(chat_id)


async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    getsession(context, update.effective_chat.id).reset()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="<chat reset>")

async def debug_mode(update:Update, context: ContextTypes.DEFAULT_TYPE):
    sess = getsession(context, update.effective_chat.id)
    sess.toggle_debug_mode()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"<debug mode set {sess.debug_mode}>")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    getsession(context, update.effective_chat.id).add_message(
        "assistant", f"Konnichiwa {update.message.from_user.first_name}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Konnichiwa {update.message.from_user.first_name}")


async def chat_fn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    msg = update.message.text
    print("got message:", msg)

    sess = getsession(context, chat_id)
    await sess.answer_chat_message(msg)


def run_bot():
    app = ApplicationBuilder().token(os.getenv('TELEGRAM_TOKEN')).build()

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chat_fn)

    app.add_handler(CommandHandler("reset", reset_chat))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("debug", debug_mode))
    app.add_handler(echo_handler)


    app.run_polling()
