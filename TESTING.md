# Testing Guide

## Quick Test

Run the automated test suite:

```bash
python test_bot.py
```

This will verify:
- ✓ Database initialization
- ✓ Sample data creation
- ✓ All handlers are properly structured
- ✓ Bot configuration is valid

## Manual Testing with Telegram

### Prerequisites
1. Get a bot token from [@BotFather](https://t.me/BotFather)
2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env and set TELEGRAM_BOT_TOKEN
   ```

### Start the Bot

#### Development Mode (Polling)
```bash
python bot.py
```

#### Production Mode (Webhook)
```bash
# Set WEBHOOK_URL in .env
export WEBHOOK_URL=https://your-app.railway.app
python bot.py
```

### Test Scenarios

#### 1. Basic Commands
- Send `/start` - Should show main menu with:
  - 🌸 Открыть каталог (WebApp button)
  - 🤖 AI рекомендация
  - 🎨 Создать букет

#### 2. Custom Bouquet Builder
- Send `/build` or click "Создать букет"
- Follow the FSM conversation:
  1. Select color (e.g., 🔴 Красный)
  2. Select quantity (e.g., 15 цветов)
  3. Select add-ons (e.g., 🎀 Лента)
  4. Preview is generated with reaction buttons

#### 3. AI Recommendation
- Send `/recommend` or click "AI рекомендация"
- Enter: `повод:день рождения, бюджет:2000`
- Should receive AI-generated recommendation

#### 4. Shopping Cart
- Add items to cart
- Send `/cart` to view
- Should show items and total price
- Test "Указать адрес доставки"
- Share location or send text address
- Test payment flow

#### 5. Admin Panel (requires admin ID)
- Set your Telegram user ID in ADMIN_IDS in .env
- Send `/admin`
- Test:
  - View flowers list
  - Add new flower (with photo upload to MinIO)
  - View orders
  - View users

### Expected Behavior

✅ **All commands should respond**
✅ **FSM conversations should track state**
✅ **Cart should persist items**
✅ **Database should save orders**
✅ **Admin panel should show data**

### Troubleshooting

#### Bot doesn't respond
- Check token is correct
- Check bot.py is running
- Check logs for errors

#### WebApp doesn't open
- Check WEBAPP_URL in .env
- Ensure webapp/ files are accessible
- Test index.html directly in browser

#### Database errors
- Check DATABASE_URL is correct
- Ensure write permissions
- Try deleting flower_bot.db and restart

#### Photo upload fails
- Check MinIO is running (docker-compose up -d)
- Check MINIO_* environment variables
- Test MinIO console at http://localhost:9001

## CI/CD Testing

### Docker Build Test
```bash
docker build -t flower-bot .
docker run --rm -e TELEGRAM_BOT_TOKEN=your_token flower-bot
```

### Docker Compose Test
```bash
docker-compose up -d
docker-compose logs -f bot
```

## Performance Testing

### Load Test (optional)
```bash
# Install locust
pip install locust

# Create locustfile.py with bot API calls
# Run load test
locust -f locustfile.py
```

## Security Testing

- [ ] No secrets in logs
- [ ] Admin commands require authorization
- [ ] SQL injection prevention (using ORM)
- [ ] Input validation for prices/quantities
- [ ] Secure webhook endpoints

## Test Coverage

Current test coverage:
- ✅ Database models and initialization
- ✅ Handler imports and structure
- ✅ Bot configuration
- ⏳ Integration tests (manual)
- ⏳ E2E tests with real Telegram API

## Next Steps

1. Add integration tests with pytest
2. Add E2E tests with python-telegram-bot test utilities
3. Set up CI/CD pipeline with GitHub Actions
4. Add performance benchmarks
