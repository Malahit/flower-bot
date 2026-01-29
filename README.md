# 🌸 flower-bot (@geography_flower_bot)

Advanced Telegram bot for flower delivery with AI-powered recommendations, custom bouquet builder, and TON Stars payment integration.

## ✨ Features

### 🌺 Core Features
- **Telegram Mini App Catalog**: Interactive web app for browsing flowers with photo gallery
- **AI Recommendations**: Perplexity-powered bouquet suggestions based on occasion and budget
- **Custom Bouquet Builder**: Step-by-step FSM for creating personalized bouquets with:
  - Color selection (red, yellow, blue, purple, white, mixed)
  - Quantity selection (5, 7, 11, 15, 21, 25 flowers)
  - Add-ons (ribbon, luxury packaging, teddy bear, chocolates)
  - AI-generated preview images (Stable Diffusion + Pillow fallback)
- **Smart Delivery**: Yandex Geocoder for address resolution from location
- **TON Stars Payment**: Integrated payment via Telegram Stars
- **Admin Panel**: Full CRUD operations for flowers with MinIO photo storage
- **Order Management**: SQLite/PostgreSQL backed order tracking

### 🤖 Bot Commands
- `/start` - Open main menu with Mini App catalog
- `/recommend` - Get AI-powered bouquet recommendation
- `/build` - Create custom bouquet (FSM conversation)
- `/cart` - View shopping cart and checkout
- `/admin` - Admin panel (requires admin privileges)

### 🎨 Technical Features
- **Async/Typed Code**: Full async implementation with type hints
- **Bot API 9.x**: Latest Telegram Bot API features (ReplyParameters, LinkPreviewOptions)
- **Webhook Support**: Production-ready webhook configuration
- **Robust Error Handling**: Comprehensive error handling and logging
- **Multi-stage Docker Build**: Optimized Docker images
- **Railway Deployment**: Ready-to-deploy configuration

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Telegram Bot Token (from @BotFather)
- Optional: MinIO, PostgreSQL for production

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Malahit/flower-bot.git
   cd flower-bot
   git checkout feat-super-flower-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and set TELEGRAM_BOT_TOKEN
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

5. **Test in Telegram**
   - Open your bot in Telegram
   - Send `/start` to begin
   - Try `/build` to create a custom bouquet
   - Send "повод:день рождения, бюджет:2000" for AI recommendation

## 📸 Demo Screenshots

### Main Menu
![Start Screen](docs/screenshots/start.png)
*Main menu with catalog access, AI recommendations, and bouquet builder*

### Telegram Mini App
![Catalog](docs/screenshots/catalog.png)
*Interactive flower catalog with categories and filters*

### Custom Bouquet Builder
![Builder](docs/screenshots/builder.png)
*Step-by-step bouquet creation with color, quantity, and add-ons*

### Shopping Cart
![Cart](docs/screenshots/cart.png)
*Cart management with TON Stars payment*

### Admin Panel
![Admin](docs/screenshots/admin.png)
*Admin interface for flower management and order tracking*

## 🏗️ Architecture

```
flower-bot/
├── bot.py                 # Main bot application
├── database.py            # SQLAlchemy models (User, Flower, Order)
├── requirements.txt       # Python dependencies
├── handlers/
│   ├── flowers.py        # /start, /recommend, /build handlers
│   ├── orders.py         # Cart and payment handlers
│   └── admin.py          # Admin CRUD operations
├── webapp/               # Telegram Mini App
│   ├── index.html       # Main app page
│   ├── css/style.css    # Styling
│   └── js/app.js        # TWA SDK integration
├── Dockerfile           # Multi-stage Docker build
├── docker-compose.yml   # Local development setup
└── railway.yaml         # Railway deployment config
```

## 🗄️ Database Schema

### Users Table
- `user_id`: Telegram user ID
- `username`, `first_name`, `last_name`: User info
- `preferred_colors`, `preferred_budget`: Preferences
- `reminder_enabled`, `reminder_dates`: Reminder settings

### Flowers Table
- `name`, `description`: Flower details
- `price`: Price in rubles
- `photo_url`: MinIO storage URL
- `category`: roses, tulips, peonies, mixed
- `available`: Availability flag

### Orders Table
- `user_id`: Foreign key to users
- `bouquet_json`: JSON with bouquet details
- `total_price`: Order total
- `delivery_address`, `geo_latitude`, `geo_longitude`: Delivery info
- `status`: pending, paid, processing, delivered, cancelled
- `payment_status`: unpaid, paid, refunded

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | ✅ Yes |
| `WEBHOOK_URL` | Webhook URL for production | For webhook mode |
| `DATABASE_URL` | Database connection string | Defaults to SQLite |
| `ADMIN_IDS` | Comma-separated admin user IDs | For admin features |
| `MINIO_ENDPOINT` | MinIO server endpoint | For photo storage |
| `MINIO_ACCESS_KEY` | MinIO access key | For photo storage |
| `MINIO_SECRET_KEY` | MinIO secret key | For photo storage |
| `PERPLEXITY_API_KEY` | Perplexity API key | For AI recommendations |
| `YANDEX_GEOCODE_API_KEY` | Yandex Geocoder API key | For address resolution |
| `STABLE_DIFFUSION_API_URL` | Stable Diffusion WebUI API | For image generation |

## 🐳 Docker Deployment

### Using Docker Compose (Development)
```bash
# Configure .env file
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f bot
```

### Using Railway (Production)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init

# Deploy
railway up
```

## 🎯 Usage Examples

### AI Recommendation
```
User: повод:свадьба, бюджет:5000, цвет:белый
Bot: 🌸 Рекомендация на основе ваших пожеланий:

Повод: свадьба
Бюджет: 5000₽

💐 Рекомендуем: Пионы нежные
Букет из розовых и белых пионов - идеально для свадьбы!
Цена: 3200₽
```

### Custom Bouquet Flow
```
1. User: /build
2. Bot: "Шаг 1/3: Выберите основной цвет"
3. User: [Selects 🔴 Красный]
4. Bot: "Шаг 2/3: Выберите количество цветов"
5. User: [Selects 15 цветов]
6. Bot: "Шаг 3/3: Выберите дополнения"
7. User: [Selects 🎀 Лента]
8. Bot: [Generates preview image with reactions 🌸❤️👍]
```

### Order Flow
```
1. User adds items to cart
2. User shares location
3. Bot resolves address via Yandex Geocoder
4. User clicks "Оплатить TON Stars"
5. Bot creates invoice
6. User pays
7. Order status: pending → paid → processing → delivered
```

## 🧪 Testing

### Manual Testing Checklist
- [ ] `/start` opens menu with catalog button
- [ ] Catalog loads in Mini App
- [ ] `/build` starts bouquet builder FSM
- [ ] Color → Quantity → Addons flow works
- [ ] Preview image generates
- [ ] Items add to cart
- [ ] Location sharing works
- [ ] Address resolution (or mock)
- [ ] Payment flow initiates
- [ ] Admin panel accessible with admin ID
- [ ] Flower CRUD operations work
- [ ] Photo upload to MinIO

## 🔐 Security

- Environment variables for sensitive data
- Admin ID validation
- Input validation for prices and quantities
- SQL injection prevention via SQLAlchemy ORM
- Secure webhook endpoints
- MinIO access control

## 📦 Dependencies

### Core
- `python-telegram-bot==21.0` - Telegram Bot API
- `sqlalchemy==2.0.25` - ORM
- `aiosqlite==0.19.0` - Async SQLite

### AI & Images
- `stable-diffusion-webui-api==0.1.1` - AI image generation
- `Pillow==10.2.0` - Image processing

### Services
- `yandex-geocode==2.0.0` - Geocoding
- `ton-connect==0.1.0` - TON payment
- `minio==7.2.3` - Object storage

### Utilities
- `httpx==0.26.0` - Async HTTP client
- `python-dotenv==1.0.0` - Environment management
- `pydantic==2.5.3` - Data validation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 👥 Credits

Inspired by top flower delivery services:
- Cvetov.ru
- Floritale
- Noelle Fleur

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Malahit/flower-bot/issues)
- **Telegram**: @geography_flower_bot

---

Made with 🌸 and ❤️ using Telegram Bot API 9.x