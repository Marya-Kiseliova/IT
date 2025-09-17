#Бот в Telegram для поиска рецептов по ингредиентам)))

import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from 

import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

BASE_URL = "https://api.spoonacular.com/recipes/complexSearch"

# Логирование
logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Суп", "Гарнир"], ["Мясо", "Второе"], ["Пирог", "Десерт"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я твой кулинарный помощник 🤖🍳\nВыбери тип блюда:",
        reply_markup=reply_markup
    )
    context.user_data.clear()


async def choose_dish_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dish_type = update.message.text.lower()
    context.user_data["dish_type"] = dish_type
    context.user_data["offset"] = 0
    await update.message.reply_text(f"Ок, введи список продуктов для {dish_type} (через запятую):")


async def handle_ingredients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in ["Ещё варианты", "Начать сначала"]:
        return await handle_navigation(update, context)

    ingredients = [i.strip() for i in update.message.text.split(",")]
    context.user_data["ingredients"] = ingredients
    context.user_data["offset"] = 0
    await send_recipes(update, context)


async def send_recipes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ingredients = context.user_data.get("ingredients", [])
    dish_type = context.user_data.get("dish_type", "main course")
    offset = context.user_data.get("offset", 0)

    params = {
        "apiKey": RECIPE_KEY,
        "includeIngredients": ",".join(ingredients),
        "type": dish_type,
        "number": 3,
        "offset": offset,
        "addRecipeInformation": True,
        "instructionsRequired": True,
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logging.error("Ошибка API: %s", e)
        await update.message.reply_text("⚠️ Ошибка при обращении к API. Попробуй снова.")
        return

    results = data.get("results", [])
    if not results:
        await update.message.reply_text("😔 Больше вариантов нет. Нажми «Начать сначала».")
        return

    for recipe in results:
        title = recipe.get("title")
        link = recipe.get("sourceUrl")
        await update.message.reply_text(f"🍴 {title}\n{link}")

    # Кнопки для навигации
    keyboard = [["Ещё варианты", "Начать сначала"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Что дальше?", reply_markup=reply_markup)


async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "Ещё варианты":
        context.user_data["offset"] = context.user_data.get("offset", 0) + 3
        await send_recipes(update, context)
    elif choice == "Начать сначала":
        await start(update, context)


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^(Суп|Гарнир|Мясо|Второе|Пирог|Десерт)$"), choose_dish_type))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ingredients))

    app.run_polling()


if __name__ == "__main__":
    main()
