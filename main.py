from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from transformers import pipeline
import re

#токен
BOT_TOKEN = "XXXXXXXXXX"


print("Загружаю нейросеть для анализа тональности...")
try:
    sentiment_analyzer = pipeline(
        "sentiment-analysis",
        model="blanchefort/rubert-base-cased-sentiment",
        tokenizer="blanchefort/rubert-base-cased-sentiment"
    )
    print("Нейросеть загружена!")
except Exception as e:
    print(f"Ошибка загрузки нейросети: {e}")
    sentiment_analyzer = None

#словарь рекомендаций
POLITE = {"пожалуйста", "извините", "спасибо", "благодарю", "будьте добры"}
EMPATHY = {"понимаю", "сожалею", "жаль", "знаю, как бывает", "это неприятно", "учту вашу ситуацию"}
NEXT_STEPS = {"сделаю", "перезвоню", "отправлю", "уже проверяю", "решу", "свяжусь", "подскажу"}

def analyze_text(text: str) -> tuple[str, list[str]]:
    """Анализ тональности"""
    try:
        if sentiment_analyzer:
            
            result = sentiment_analyzer(text[:512])[0]
            label = result['label']
            confidence = result['score']

            
            tone_ru = {
                'POSITIVE': 'положительный',
                'NEUTRAL': 'нейтральный',
                'NEGATIVE': 'негативный'
            }.get(label, 'нейтральный')
        else:
          
            words = text.lower().split()
            pos_count = sum(1 for word in words if word in {"спасибо", "хорошо", "отлично", "круто", "понравилось"})
            neg_count = sum(1 for word in words if word in {"плохо", "проблема", "ошибка", "ужасно", "раздражает"})

            if pos_count > neg_count:
                tone_ru = "положительный"
            elif neg_count > pos_count:
                tone_ru = "негативный"
            else:
                tone_ru = "нейтральный"

        
        words = set(re.findall(r'\b\w+\b', text.lower()))
        recs = []

        if tone_ru == "негативный" and not (words & EMPATHY):
            recs.append("Добавьте эмпатии: *«Понимаю вашу ситуацию»*, *«Сожалею, что возникла такая ситуация»*")

        if not (words & POLITE):
            recs.append("Используйте вежливые слова: *«пожалуйста»*, *«спасибо»*, *«благодарю»*")

        if not (words & NEXT_STEPS):
            recs.append("Укажите следующий шаг: *«Я перезвоню»*, *«Отправлю файл»*, *«Решу сегодня»*")

        if not recs:
            recs.append("Отличное общение! Продолжайте в том же духе.")

        return tone_ru, recs[:2]

    except Exception as e:
        print(f"Ошибка анализа: {e}")
        return "нейтральный", ["Ошибка анализа. Попробуйте другой текст."]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я анализирую тональность разговоров!\n\n"
        "Отправь мне текст диалога, и я определю тон общения и дам рекомендации."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        if len(text) < 10:
            await update.message.reply_text("📝 Напишите текст подлиннее для анализа (минимум 10 символов)")
            return

        tone, recs = analyze_text(text)

        reply = f" <b>Тон разговора:</b> {tone}\n\n"
        reply += " <b>Рекомендации:</b>\n"

        for rec in recs:
            reply += f"{rec}\n"

        if sentiment_analyzer:
            reply += "\n <i>Анализ выполнен с помощью нейросети <code>blanchefort/rubert-base-cased-sentiment</code></i>"
        else:
            reply += "\n<i>Анализ выполнен по ключевым словам (нейросеть недоступна)</i>"

        await update.message.reply_text(reply, parse_mode='HTML', disable_web_page_preview=True)

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
