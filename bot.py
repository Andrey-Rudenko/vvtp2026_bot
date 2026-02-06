import logging
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# -------------------- Логи --------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# -------------------- Состояния диалога --------------------
ASK_WEEK_GOAL = 1

# -------------------- "Память" (просто в оперативке) --------------------
@dataclass
class UserProfile:
    week_goal: Optional[str] = None
    last_course: Optional[str] = None

USERS: Dict[int, UserProfile] = {}

def get_user(user_id: int) -> UserProfile:
    if user_id not in USERS:
        USERS[user_id] = UserProfile()
    return USERS[user_id]

# -------------------- Клавиатуры --------------------
MAIN_KB = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📊 Мой прогресс"), KeyboardButton("🎯 Цель на неделю")],
        [KeyboardButton("🧠 Рекомендации"), KeyboardButton("❓ FAQ / Поддержка")],
    ],
    resize_keyboard=True,
)

# -------------------- Хелперы --------------------
def human_name(update: Update) -> str:
    u = update.effective_user
    return (u.first_name or u.username or "пользователь").strip()

# -------------------- Хэндлеры --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = human_name(update)
    await update.message.reply_text(
        f"Привет, {name}! Я бот-помощник для обучения на IT-курсах.\n"
        "Могу показать прогресс, помочь поставить цель и дать рекомендации.\n\n"
        "Выбери пункт в меню 👇",
        reply_markup=MAIN_KB,
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Я помогаю школьникам и студентам сопровождать обучение:\n"
        "— напоминать про цель\n"
        "— подсказать следующий шаг\n"
        "— дать быстрые ответы по сервису\n\n"
        "Меню ниже 👇",
        reply_markup=MAIN_KB,
    )

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Здесь можно будет подключить веб-сервис (API). Пока — демо.
    profile = get_user(update.effective_user.id)
    goal = profile.week_goal or "не задана"
    await update.message.reply_text(
        "📊 Мой прогресс\n"
        "Сейчас у меня демо-режим (без подключения к сайту).\n"
        f"Твоя цель на неделю: {goal}\n\n"
        "Если хочешь — задай цель: нажми «🎯 Цель на неделю».",
        reply_markup=MAIN_KB,
    )

async def ask_week_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🎯 Напиши цель на неделю одним предложением.\n"
        "Например: «решить 20 задач по Python» или «пройти 3 урока по алгоритмам».",
        reply_markup=MAIN_KB,
    )
    return ASK_WEEK_GOAL

async def save_week_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    profile = get_user(update.effective_user.id)
    profile.week_goal = text if text else None

    await update.message.reply_text(
        f"Принято ✅ Цель на неделю записал: {profile.week_goal}\n"
        "Хочешь — могу дать рекомендации по плану: «🧠 Рекомендации».",
        reply_markup=MAIN_KB,
    )
    return ConversationHandler.END

async def recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = get_user(update.effective_user.id)
    goal = profile.week_goal

    if not goal:
        await update.message.reply_text(
            "🧠 Рекомендации\n"
            "Сначала задай цель на неделю — так рекомендации будут точнее.\n"
            "Нажми «🎯 Цель на неделю».",
            reply_markup=MAIN_KB,
        )
        return

    # Простые “человеческие” рекомендации
    await update.message.reply_text(
        "🧠 Рекомендации по твоей цели\n"
        f"Цель: {goal}\n\n"
        "1) Разбей цель на 3–5 маленьких шагов.\n"
        "2) Выдели 20–40 минут в день (лучше регулярно, чем редко и много).\n"
        "3) После каждого занятия фиксируй результат: что сделал и что осталось.\n"
        "4) Если застрял — задай вопрос и приложи пример/скрин.\n\n"
        "Если хочешь — напиши, что именно сейчас учишь (Python / алгоритмы / веб и т.п.).",
        reply_markup=MAIN_KB,
    )

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "❓ FAQ / Поддержка\n"
        "1) Как пользоваться сервисом? — Задай цель и отмечай прогресс.\n"
        "2) Что делать, если не понимаю тему? — Напиши, где именно застрял.\n"
        "3) Как связаться с поддержкой? — Напиши сюда: rudenko.aart@dvfu.ru.\n\n"
        "Если вопрос нестандартный — опиши проблему одним сообщением.",
        reply_markup=MAIN_KB,
    )

async def fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Реакция на неожиданные запросы
    await update.message.reply_text(
        "Я понял не всё 😅\n"
        "Выбери действие в меню или напиши вопрос более конкретно.\n"
        "Например: «как поставить цель», «покажи прогресс», «дай рекомендации».",
        reply_markup=MAIN_KB,
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Ок, отменил.", reply_markup=MAIN_KB)
    return ConversationHandler.END


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Не найден BOT_TOKEN. Установи переменную окружения BOT_TOKEN с токеном от BotFather.")

    app = Application.builder().token(token).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about))

    # Диалог постановки цели
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^🎯 Цель на неделю$"), ask_week_goal)],
        states={ASK_WEEK_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_week_goal)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)

    # Кнопки меню
    app.add_handler(MessageHandler(filters.Regex(r"^📊 Мой прогресс$"), progress))
    app.add_handler(MessageHandler(filters.Regex(r"^🧠 Рекомендации$"), recommendations))
    app.add_handler(MessageHandler(filters.Regex(r"^❓ FAQ / Поддержка$"), faq))

    # Любой другой текст
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()