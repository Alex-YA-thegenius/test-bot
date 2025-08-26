from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from transformers import pipeline
import re

#токен
BOT_TOKEN = "8493588022:AAERXiuRXReqU__lX4Td4bZI0-L-UMK24qw"

#нейросеть
print("нейросеть для анализа тональности")
try:
    sentiment_analyzer = pipeline(
        "sentiment-analysis",
        model="Tinkoff/rubert-base-cased-sentiment-new",
        tokenizer="Tinkoff/rubert-base-cased-sentiment-new"
    )
    print("Нейросеть загружена")
except Exception as e:
    print(f"Ошибка загрузки нейросети: {e}")
    sentiment_analyzer = None


POLITE = {"пожалуйста", "извините", "спасибо"}
EMPATHY = {"понимаю", "сожалею", "жаль"}
NEXT_STEPS = {"сделаю", "перезвоню", "отправлю"}


def analyze_text(text: str) -> tuple[str, list[str]]:
    """Анализ тональности"""
    try:
        #если нейросеть работает используем ее
        if sentiment_analyzer:
            result = sentiment_analyzer(text[:256])[0]  # Еще короче текст
            tone_en = result['label']
            confidence = result['score']

            tone_ru = {
                'POSITIVE': 'положительный',
                'NEUTRAL': 'нейтральный',
                'NEGATIVE': 'негативный',
                'LABEL_0': 'негативный',
                'LABEL_1': 'нейтральный',
                'LABEL_2': 'положительный'
            }.get(tone_en, 'нейтральный')
        else:

            words = text.lower().split()
            pos_count = sum(1 for word in words if word in {"спасибо", "хорошо", "отлично"})
            neg_count = sum(1 for word in words if word in {"проблема", "плохо", "ошибка"})

            if pos_count > neg_count:
                tone_ru = "положительный"
            elif neg_count > pos_count:
                tone_ru = "негативный"
            else:
                tone_ru = "нейтральный"

       #рекомен
        words = text.lower().split()
        recs = []

        if tone_ru == "негативный" and not any(word in EMPATHY for word in words):
            recs.append("Добавьте эмпатии: 'Понимаю вашу ситуацию' ")

        if not any(word in POLITE for word in words):
            recs.append("Используйте вежливые слова:  'пожалуйста', 'спасибо'")

        if not any(word in NEXT_STEPS for word in words):
            recs.append("Предложите следующий шаг: 'Я перезвоню', 'Отправлю вам'")

        if not recs:
            recs.append("Отличное общение! Продолжайте в том же духе")

        return tone_ru, recs[:2]

    except Exception as e:
        print(f"Ошибка анализа: {e}")
        return "нейтральный", ["Ошибка анализа. Попробуйте другой текст"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я анализирую тональность разговоров.\n\n"
        "Отправь мне текст разговора, и я определю тон общения + дам рекомендации."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(update.message.text) < 10:
            await update.message.reply_text("📝 Напишите текст подлиннее для анализа")
            return

        tone, recs = analyze_text(update.message.text)

        reply = f" <b>Тон разговора:</b> {tone}\n\n"
        reply += " <b>Рекомендации:</b>\n"

        for i, rec in enumerate(recs, 1):
            reply += f"{i}. {rec}\n"


        await update.message.reply_text(reply, parse_mode='HTML')

    except Exception as e:
        await update.message.reply_text("❌ Ошибка анализа. Попробуйте ещё раз.")


def main():
    print("Запуск бота...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()