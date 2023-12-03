#%%
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes
from chat import ChatSession

key = "6948341501:AAGMiHgrgOhJXy0NC3bS1wYv7ph8vrKPcPI"

sessions:dict[any,ChatSession] = {}

def getsession(ctx,chat_id):
    if chat_id not in sessions: sessions[chat_id] = ChatSession(ctx, chat_id)
    return sessions.get(chat_id)

async def reset_chat(update: Update, context:ContextTypes.DEFAULT_TYPE):
    getsession(context, update.effective_chat.id).reset()
    await context.bot.send_message(chat_id = update.effective_chat.id,text="<chat reset>")

async def start(update:Update, context: ContextTypes.DEFAULT_TYPE):
    getsession(update.effective_chat.id).add_message("assistant",f"Konnichiwa {update.message.from_user.first_name}")
    await context.bot.send_message(chat_id = update.effective_chat.id,text=f"Konnichiwa {update.message.from_user.first_name}")

async def chat_fn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    msg = update.message.text
    print("got message:",msg)

    sess = getsession(context,chat_id)
    await sess.answer_chat_message(msg)

app = ApplicationBuilder().token(key).build()

echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chat_fn)


app.add_handler(CommandHandler("reset",reset_chat))
app.add_handler(CommandHandler("start",start))
app.add_handler(echo_handler)


app.run_polling()

