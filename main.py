import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

# -------- Состояния диалога --------
(
    START,
    AFTER_WHO,
    WAIT_COOKIE,
    WAIT_CODE,
    OFFSCRIPT_MENU,
    END,
) = range(6)

# -------- Кнопки --------
BTN_QUEST = "Да, я на квест"
BTN_WHO = "Кто ты?"
BTN_YES_STORY = "Да, расскажешь мне что-то?"
BTN_NO = "Нет"

def kb_start():
    return ReplyKeyboardMarkup([[BTN_QUEST, BTN_WHO]], resize_keyboard=True)

def kb_after_who():
    return ReplyKeyboardMarkup([[BTN_QUEST]], resize_keyboard=True)

def kb_offscript():
    return ReplyKeyboardMarkup([[BTN_NO, BTN_YES_STORY]], resize_keyboard=True)

# -------- Параметры игры --------
COOKIE_WORDS = {"печенье", "печенька", "печеньки", "печенюшка", "cookie", "cookies", "🍪"}
SECRET_CODE = "28082003"

# -------- Вспомогалки --------
def norm(s: str) -> str:
    return (s or "").strip().lower()

async def type_and_send(chat, text, delay=0.8):
    await chat.send_action(ChatAction.TYPING)
    await asyncio.sleep(delay)
    await chat.send_message(text)

# -------- Хендлеры --------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await type_and_send(chat, "Бот: Привет, странник! Тебе нужна моя помощь?🪄")
    await chat.send_message("Выбери вариант ниже:", reply_markup=kb_start())
    return START

async def on_start_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    choice = norm(update.message.text)

    if choice == norm(BTN_WHO) or choice == "[кто ты?]":
        await type_and_send(chat, "Бот: Я - волшебник! Тот самый, из сказок! 💫")
        await type_and_send(chat, "Бот: Правда…")
        await type_and_send(chat, "Бот: Я один день на этой должности, мне нужно одного человека заменить, на самом деле я учёный…")
        await type_and_send(chat, "Бот: Но ладно! Я буду рад тебе помочь, сделаю всё возможное!")
        await chat.send_message("Продолжим?", reply_markup=kb_after_who())
        return AFTER_WHO

    if choice == norm(BTN_QUEST) or choice in {"я на квест", "[я на квест/да, я на квест]"}:
        await type_and_send(chat, "Бот: Квест? Ох, чудесно! Нелегко начинать, но ты справишься!")
        await type_and_send(chat, "Бот: Для того, что бы я смог тебя направить на путь - должен произойти магический обмен🌟")
        await type_and_send(chat, "Бот: Я бы и просто так помог, но такие условия для магии, ты прости. Даже выдающийся учёный тут бессилен, эх.")
        await type_and_send(chat, "Бот: Дай мне то, что я люблю всем сердцем!🌌")
        await chat.send_message("Подсказка: круглое, обычно к чаю 🍪", reply_markup=ReplyKeyboardRemove())
        return WAIT_COOKIE

    # не по скрипту
    await type_and_send(chat, "Бот: Хм?😲")
    await type_and_send(chat, "Бот: Что-то ещё?🤔")
    await chat.send_message("Выбери:", reply_markup=kb_offscript())
    return OFFSCRIPT_MENU

async def after_who(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.text = BTN_QUEST
    return await on_start_choice(update, context)

async def wait_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    text = update.message.text or ""
    answer = "🍪" if "🍪" in text else norm(text)

    if any(w in answer for w in COOKIE_WORDS):
        await type_and_send(chat, "Бот: Ух, угадал, молодец! 🌀")
        await type_and_send(chat, "Бот: Хорошо. Разгадаешь загадку - получишь подсказку! 🌠")
        await type_and_send(chat, "Бот: Она изменилась. Но свет остался прежним….")
        await type_and_send(chat, "Бот: Найди её. Вчера она сияла. Сегодня - она закодирована…")
        await type_and_send(chat, "Бот: ответ лежит у повелительницы Кота во Фраке…")
        await chat.send_message("Когда найдёшь код — просто пришли его сюда числом.")
        return WAIT_CODE

    await type_and_send(chat, "Бот: Хм?😲")
    await type_and_send(chat, "Бот: Что-то ещё?🤔")
    await chat.send_message("Выбери:", reply_markup=kb_offscript())
    return OFFSCRIPT_MENU

async def wait_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    code = norm(update.message.text).replace(" ", "")
    if code == SECRET_CODE:
        await type_and_send(chat, "Бот: И снова угадал! 🎊")
        await type_and_send(chat, "Бот: Да прибудет тем, кто ищет🍀")
        await type_and_send(chat, "Бот: Удачи, странник! Я с тобой мысленно✨")
        return END

    await type_and_send(chat, "Бот: Хм?😲")
    await type_and_send(chat, "Бот: Что-то ещё?🤔")
    await chat.send_message("Выбери:", reply_markup=kb_offscript())
    return OFFSCRIPT_MENU

async def offscript_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    choice = norm(update.message.text)

    if choice == norm(BTN_NO):
        await type_and_send(chat, "Бот: Хорошо! Удачи, путник🤗", delay=0.5)
        return END

    if choice == norm(BTN_YES_STORY):
        lines = [
            "Бот: Рассказать?…",
            "Бот: Что именно?…",
            "Бот: Хммм…",
            "Бот: *задумчивый вид*",
            "Бот: Знаешь…",
            "Бот: У меня есть лучший друг.",
            "Бот: Мы не разлей вода!",
            "Бот: И…",
            "Бот: Мне запомнилась наша первая встреча.",
            "Бот: Увидев его в-первые, я подумал: «Ого, какой крутой!»",
            "Бот: Он увидел, как я оторопел и сказал одну простую вещь, что я запомнил навсегда:",
            "Бот: «Не волнуйся, Тейлз. Главное - быть собой».",
            "Бот: Это помогло мне стать тем, кого все знают как Тейлз!",
            "Бот: Теперь я ем вкуснейшее печенье и радуюсь жизни😝",
            "Бот: Может…тебе это как-то поможет?",
            "Бот: Надеюсь, да…",
            "Бот: Ха-ха! Ну ладно, тебе пора, друг!",
            "Бот: Что-то я заболтался😄",
            "Бот: Спасибо, что ушёл не сразу! Это необычно и я так рад😇",
            "Береги себя, да прибудет с тобой удача!🏵️",
        ]
        for line in lines:
            await type_and_send(chat, line, delay=0.6)
        return END

    await type_and_send(chat, "Бот: Хм?😲")
    await type_and_send(chat, "Бот: Что-то ещё?🤔")
    await chat.send_message("Выбери:", reply_markup=kb_offscript())
    return OFFSCRIPT_MENU

async def fallback_any(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await type_and_send(chat, "Бот: Хм?😲")
    await type_and_send(chat, "Бот: Что-то ещё?🤔")
    await chat.send_message("Выбери:", reply_markup=kb_offscript())
    return OFFSCRIPT_MENU

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n/start — начать\n/help — помощь\n\nПодсказка: волшебнику нравится круглое к чаю 🍪"
    )

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён. Напиши /start, чтобы начать заново.",
                                    reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана!")

    app = ApplicationBuilder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            START: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_start_choice)],
            AFTER_WHO: [MessageHandler(filters.TEXT & ~filters.COMMAND, after_who)],
            WAIT_COOKIE: [MessageHandler(filters.TEXT & ~filters.COMMAND, wait_cookie)],
            WAIT_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, wait_code)],
            OFFSCRIPT_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, offscript_menu)],
            END: [MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_any)],
        },
        fallbacks=[
            CommandHandler("help", cmd_help),
            CommandHandler("cancel", cmd_cancel),
            MessageHandler(filters.ALL, fallback_any),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("cancel", cmd_cancel))

    print("Bot is up. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
