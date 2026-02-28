# 🚀 Deployment Instructions

## Деплой на Railway

### Вариант 1: Через GitHub (рекомендуется)

1. Зайдите на [Railway](https://railway.app)
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Выберите репозиторий `tokazov/ai-centers-demo-bot`
5. Railway автоматически обнаружит Python проект

### Настройка Environment Variables

Добавьте в Railway следующие переменные окружения:

```
BOT_TOKEN=8672975647:AAHpWG5xTxLRv0IKKy6tvl_VlAn_FfL99vM
GEMINI_API_KEY=AIzaSyDRJLp8JGpKid1pTJBRVgeumPdObveAXwY
```

### Или через Railway CLI

Если есть доступ к Railway Token:

```bash
railway link fe9eead2-e606-4dd8-8820-a45687dcb36e
railway up
railway variables set BOT_TOKEN=8672975647:AAHpWG5xTxLRv0IKKy6tvl_VlAn_FfL99vM
railway variables set GEMINI_API_KEY=AIzaSyDRJLp8JGpKid1pTJBRVgeumPdObveAXwY
```

## Вариант 2: Быстрый тест локально

```bash
export BOT_TOKEN=8672975647:AAHpWG5xTxLRv0IKKy6tvl_VlAn_FfL99vM
export GEMINI_API_KEY=AIzaSyDRJLp8JGpKid1pTJBRVgeumPdObveAXwY
python bot.py
```

## 📝 После деплоя

Бот доступен по адресу: [@TestCargoAsist_bot](https://t.me/TestCargoAsist_bot)

Проверьте работу:
1. Отправьте `/start`
2. Выберите любую нишу
3. Пообщайтесь с AI-ассистентом
4. После 5 сообщений появится CTA

## 🔍 Проверка логов

В Railway:
- Откройте проект
- Перейдите на вкладку "Deployments"
- Выберите текущий деплой
- Нажмите "View Logs"

## 📊 Мониторинг

Railway автоматически показывает:
- Статус деплоя
- Использование ресурсов
- Логи в реальном времени
- Метрики производительности

## 🛠️ Troubleshooting

### Бот не отвечает
- Проверьте логи на наличие ошибок
- Убедитесь что BOT_TOKEN правильный
- Проверьте что процесс запущен (не упал)

### Gemini API ошибки
- Проверьте GEMINI_API_KEY
- Убедитесь что ключ активен и не исчерпал квоту
- Проверьте логи на точное сообщение об ошибке

### Railway деплой падает
- Проверьте requirements.txt
- Убедитесь что Python version в runtime.txt корректный
- Проверьте логи сборки
