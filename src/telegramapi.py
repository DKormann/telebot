import os
from chat import ChatSession
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes
from dotenv import load_dotenv
# import logging
import asyncio
import database

load_dotenv()

sessions: dict[any, ChatSession] = {}

admin_key: str = os.environ.get("ADMIN_KEY")

def getsession(ctx, chat_id):
    if chat_id not in sessions: sessions[chat_id] = ChatSession(ctx, chat_id)
    return sessions.get(chat_id)

def run_bot():

    app = ApplicationBuilder().token(os.getenv('TELEGRAM_TOKEN')).build()
    def handle(fn):
        async def wrapper(update:Update, context: ContextTypes.DEFAULT_TYPE): await fn (getsession(context, update.effective_chat.id),update)
        return wrapper

    @handle
    async def chat_fn(sess:ChatSession, update: Update):
        msg = update.message.text
        print("got message:", msg)
        await sess.answer_chat_message(msg)
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_fn))

    async def attachmentHandler(update:Update, context:ContextTypes.DEFAULT_TYPE):print(update)
    app.add_handler(MessageHandler(filters.ATTACHMENT, attachmentHandler))

    def commandHandle (fn): app.add_handler(CommandHandler(fn.__name__, handle(fn)))

    @commandHandle
    async def start(sess:ChatSession, update: Update):
        chat_id = update.effective_chat.id
        username = " ".join(filter(lambda x: x is not None,[
            update.message.from_user.first_name,
            update.message.from_user.last_name,
            update.message.from_user.username,
        ]))
        try: database.insert_chat(chat_id, username)
        except:pass
        await sess.send_message(f"Konichiwa, {username}")

    @commandHandle
    async def reset(sess:ChatSession, update: Update):
        await sess.send_message("<resetting chat>")
        sess.reset()

    @commandHandle
    async def debug(sess:ChatSession, update:Update):
        sess.toggle_debug_mode()
        await sess.send_message(f"<debug mode set {sess.debug_mode}>")

    @commandHandle
    async def getadmin(sess:ChatSession, update:Update):
        print(f"getadmin {update}")
        args = update.message.text.split()[1:]
        if not args: return await sess.send_message("<usage: /getadmin \"password\">")
        pwd = args[0]
        if pwd == admin_key: 
            sess.is_admin = True
            await sess.send_message("<you are now admin.>")
        else: await sess.send_message("<wrong password.>")

    @commandHandle
    async def messagefriend(sess:ChatSession, update:Update):
        args = update.message.text.split()[1:]
        if len(args) < 2:return await sess.send_message("<usage: /message_friend friendname hello there")
        target = args[0]
        message = " ".join(args[1:])
        print(f"sending {message} to {target}")
        target_user_id = database.get_chat_by_username(target)
        if len(target_user_id) == 0: await sess.send_message(f"cant find {target}")
        target_user_id = target_user_id[0]['id']
        await sess.ctx.bot.send_message(chat_id = target_user_id, text = message)
        
        print(target_user_id)

    app.run_polling()
