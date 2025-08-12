# main.py
import os
import re
import asyncio
import threading
from flask import Flask

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

# ---------- мини-сервер для Render ----------
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Tails Wizard Bot is running!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask, daemon=True).start()
# ---------------------------------------------------------------

# ---------- состояния ----------
START, WAIT_COOKIE, WAIT_CODE, END_MENU = range(4)

# ---------- кнопки ----------
BTN_WHO = "Кто ты?"
BTN_YES_STORY = "Да, расскажешь мне что-то?"
BTN_NO = "Нет"

def kb_start():
    return ReplyKeyboardMarkup([[BTN_WHO]], resize_keyboard=True)

def kb_end():
    return ReplyKeyboardMarkup([[BTN_NO, BTN_YES_STORY]], resize_keyboard=True)

# ---------- настройки ----------
SECRET_CODE = "28082003"
MAX_CODE_ATTEMPTS = 3

# ---------- утилиты ----------
def norm(s: str) -> str:
    return (s or "").lower().strip()

def is_exact_cookie(text: str) -> bool:
    """Только ровно одно слово: 'печенье' или 'печенька'."""
    t = norm(text)
    if not re.fullmatch(r"[а-яё]+", t):
        return False
    return t in ("печенье", "печенька")

async def type_and_send(chat, text: str, delay: float = 1.6, remove_kb=False):
    await chat.send_action(ChatAction.TYPING)
    await asyncio.sleep(delay)
    if remove_kb:
        await chat.send_message(text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    else:
        await chat.send_message(text, parse_mode="HTML")

async def send_block(chat, lines, per_line_delay: float = 1.3, remove_kb=False):
    for i, line in enumerate(lines):
        if i == 0 and remove_kb:
            await type_and_send(chat, line, delay=per_line_delay, remove_kb=True)
        else:
            await type_and_send(chat, line, delay=per_line_delay)

# ---------- сюжетные куски ----------
async def start_quest(chat):
    await send_block(chat, [
        "Я так понимаю, ты на квест, раз пришёл ко мне",
        "Для того, чтобы я смог тебя направить на путь, должен произойти магический обмен 🌟",
        "Я бы и просто так помог, но такие условия для магии, ты прости. Даже выдающийся учёный тут бессилен, эх.",
        "Дай мне то, что я люблю всем сердцем! 🌌",
    ], per_line_delay=1.3, remove_kb=True)
    await chat.send_message("Подсказка: круглое, обычно к чаю 🍪",
                            reply_markup=ReplyKeyboardRemove())

# ---------- хендлеры ----------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    context.user_data["code_attempts"] = 0
    await type_and_send(chat, "Привет, странник! Тебе нужна моя помощь? 🪄", remove_kb=True)
    await chat.send_message("Выбери ниже:", reply_markup=kb_start())  # кнопка точно появится
    return START

async def on_start_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if norm(update.message.text) == norm(BTN_WHO):
        await send_block(chat, [
            "Я — волшебник! Тот самый, из сказок! 💫",
            "Правда…",
            "Я один день на этой должности: нужно заменить одного человека, а на самом деле я учёный…",
            "Но ладно! Я буду рад тебе помочь, сделаю всё возможное!",
        ], remove_kb=True)
        await start_quest(chat)
        return WAIT_COOKIE

    await type_and_send(chat, "Нажми кнопку «Кто ты?» ниже.")
    return START

async def wait_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if is_exact_cookie(update.message.text):
        await send_block(chat, [
            "Ух, угадал, молодец! 🌀",
            "Хорошо. Разгадаешь загадку — получишь подсказку! 🌠",
            "<i>Она изменилась. Но свет остался прежним…</i>",
            "<i>Найди её. Вчера она сияла. Сегодня — она закодирована…</i>",
            "<i>Ответ лежит у повелительницы Кота во Фраке…</i>",
        ], remove_kb=True)
        await chat.send_message("Когда найдёшь код — просто пришли его сюда числом.",
                                reply_markup=ReplyKeyboardRemove())
        context.user_data["code_attempts"] = 0
        return WAIT_CODE

    await type_and_send(chat, "Нужно одно слово без лишнего.")
    return WAIT_COOKIE

async def wait_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    code = norm(update.message.text).replace(" ", "")
    attempts = int(context.user_data.get("code_attempts", 0))

    # Проверка кода
    if code == SECRET_CODE:
        await send_block(chat, [
            "И снова угадал! 🎊",
            "Да прибудет тем, кто ищет 🍀",
            "Удачи, странник! Я с тобой мысленно ✨",
        ], per_line_delay=1.5, remove_kb=True)
        await send_block(chat, ["Могу ли я тебе ещё чем-то помочь?"], per_line_delay=1.2)
        await chat.send_message("Выбери:", reply_markup=kb_end())
        return END_MENU

    # Если код неверный
    attempts += 1
    context.user_data["code_attempts"] = attempts
    left = MAX_CODE_ATTEMPTS - attempts

    if left > 0:
        await type_and_send(chat, f"Не тот код. Осталось попыток: {left}. Попробуй ещё раз.")
        return WAIT_CODE
    else:
        await send_block(chat, [
            "Увы, попытки закончились.",
            "Пусть удача улыбнётся тебе в следующий раз.",
            "Прощай, путник.",
        ], remove_kb=True)
        return ConversationHandler.END

async def end_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    choice = norm(update.message.text)

    if choice == norm(BTN_NO):
        await type_and_send(chat, "Хорошо! Удачи, путник 🤗", delay=1.4, remove_kb=True)
        return ConversationHandler.END

    if choice == norm(BTN_YES_STORY):
        await send_block(chat, [
            "Рассказать?…",
            "Что именно?…",
            "Хммм…",
            "*задумчивый вид*",
            "Знаешь…",
            "У меня есть лучший друг.",
            "Мы не разлей вода!",
            "И…",
            "Мне запомнилась наша первая встреча.",
            "Увидев его впервые, я подумал: «Ого, какой крутой!»",
            "Он увидел, как я оторопел, и сказал одну простую вещь, что я запомнил навсегда:",
            "«Не волнуйся, Тейлз. Главное — быть собой».",
            "Это помогло мне стать тем, кого все знают как Тейлз!",
            "Теперь я ем вкуснейшее печенье и радуюсь жизни 😝",
            "Может… тебе это как-то поможет?",
            "Надеюсь, да…",
            "Ха-ха! Ну ладно, тебе пора, друг!",
            "Что-то я заболтался 😄",
            "Спасибо, что ушёл не сразу! Это необычно, и я так рад 😇",
            "Береги себя, да прибудет с тобой удача! 🏵️",
        ], per_line_delay=1.2, remove_kb=True)
        return ConversationHandler.END

    await send_block(chat, ["Могу ли я тебе ещё чем-то помочь?"], per_line_delay=1.2)
    await chat.send_message("Выбери:", reply_markup=kb_end())
    return END_MENU

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n/start — начать заново\n/help — помощь\n\nПодсказка: мне нравится круглое к чаю 🍪"
    )

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Диалог завершён. Напиши /start, чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def build_app():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана!")

    app = ApplicationBuilder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            START: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_start_choice)],
            WAIT_COOKIE: [MessageHandler(filters.TEXT & ~filters.COMMAND, wait_cookie)],
            WAIT_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, wait_code)],
            END_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_menu)],
        },
        fallbacks=[CommandHandler("help", cmd_help), CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    return app

if __name__ == "__main__":
    application = build_app()
    print("Bot is up. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
