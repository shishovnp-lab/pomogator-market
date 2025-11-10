import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# -------------------------------
# 🔹 Здесь будет храниться список подписок
subscriptions = {}  # user_id: [{"query": "телевизор LG OLED", "price": 69999, "url": "..."}]
# -------------------------------

# 🔹 Приветственное сообщение
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔎 Найти товар", "🛍 Распродажи", "📬 Мои подписки")
    await message.answer(
        "👋 Привет! Я — *Помогатор Маркет*.\n\n"
        "🛒 Я помогу тебе найти самые выгодные товары на Ozon и Wildberries.\n"
        "📉 А ещё я могу уведомить, когда цена упадёт больше чем на 10%.\n\n"
        "Выбери действие ниже 👇",
        parse_mode="Markdown",
        reply_markup=kb
    )

# -------------------------------
# 🔹 Обработка запросов поиска
@dp.message_handler(lambda m: m.text == "🔎 Найти товар")
async def ask_product(message: types.Message):
    await message.answer("Введите название товара (например: *телевизор LG OLED 55*)", parse_mode="Markdown")

@dp.message_handler(lambda m: m.text not in ["🔎 Найти товар", "🛍 Распродажи", "📬 Мои подписки"])
async def search_product(message: types.Message):
    query = message.text

    await message.answer(f"🔍 Ищу выгодные предложения для: *{query}* ...", parse_mode="Markdown")

    # 🔸 ЗАГЛУШКА: здесь нужно вставить твой парсер Ozon/WB
    # Пример:
    # results = await get_products(query)
    results = [
        {"title": "Телевизор LG OLED 55C3", "price": 78999, "url": "https://www.ozon.ru/example"},
        {"title": "Телевизор LG OLED 55B3", "price": 76999, "url": "https://www.wildberries.ru/example"}
    ]

    text = "\n\n".join([f"📦 *{r['title']}*\n💰 {r['price']} ₽\n🔗 [Смотреть товар]({r['url']})" for r in results])
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

    await message.answer("Хочешь, чтобы я уведомил, если цена снизится более чем на 10%? Напиши: `/subscribe`")

# -------------------------------
# 🔹 Управление подписками
@dp.message_handler(commands=["subscribe"])
async def subscribe(message: types.Message):
    query = message.get_args()
    if not query:
        await message.answer("Чтобы подписаться, напиши: `/subscribe телевизор LG OLED 55`")
        return

    user_id = message.from_user.id
    if user_id not in subscriptions:
        subscriptions[user_id] = []

    subscriptions[user_id].append({"query": query, "price": 70000, "url": "https://example.com"})
    await message.answer(f"✅ Подписка на *{query}* оформлена!\nЯ пришлю уведомление, если цена упадёт на 10% или больше.", parse_mode="Markdown")

@dp.message_handler(lambda m: m.text == "📬 Мои подписки")
async def my_subs(message: types.Message):
    user_id = message.from_user.id
    if user_id not in subscriptions or not subscriptions[user_id]:
        await message.answer("У тебя пока нет активных подписок 📭")
    else:
        text = "\n\n".join([f"🔔 *{s['query']}*\nТекущая цена: {s['price']} ₽" for s in subscriptions[user_id]])
        await message.answer(f"Твои подписки:\n\n{text}", parse_mode="Markdown")

# -------------------------------
# 🔹 Распродажи
@dp.message_handler(lambda m: m.text == "🛍 Распродажи")
async def sales(message: types.Message):
    await message.answer("🛒 Показываю горячие предложения!\n(Пример данных)")
    sales = [
        {"title": "Смартфон Samsung S23 Ultra", "price": 89999, "url": "https://www.ozon.ru/example-sale"},
        {"title": "Пылесос Dyson V12", "price": 39999, "url": "https://www.wildberries.ru/example-sale"}
    ]
    text = "\n\n".join([f"🔥 *{s['title']}*\n💰 {s['price']} ₽\n🔗 [Купить]({s['url']})" for s in sales])
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

# -------------------------------
# 🔹 Проверка цен каждые 5 часов
async def check_prices():
    for user_id, subs in subscriptions.items():
        for sub in subs:
            # ЗАГЛУШКА: тут должна быть проверка текущей цены через парсер
            current_price = sub["price"] * 0.88  # пример падения цены
            if current_price <= sub["price"] * 0.9:
                await bot.send_message(
                    user_id,
                    f"📉 Цена на *{sub['query']}* снизилась!\n"
                    f"Было: {sub['price']} ₽ → Стало: {int(current_price)} ₽\n"
                    f"🔗 [Смотреть товар]({sub['url']})",
                    parse_mode="Markdown"
                )
                sub["price"] = current_price

# Добавляем задачу в планировщик
scheduler.add_job(check_prices, "interval", hours=5)

# -------------------------------
# 🔹 Запуск
if __name__ == "__main__":
    scheduler.start()
    executor.start_polling(dp)
