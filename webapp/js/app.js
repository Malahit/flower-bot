// Telegram Web App initialization
let tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

// API configuration
const API_BASE_URL = window.location.origin;
const PLACEHOLDER_IMAGE = 'https://via.placeholder.com/300x300.png?text=Flower';

// Flowers data (loaded from API)
let flowers = [];

// Cart management
let cart = [];

// Loading state
let isLoading = false;

// Load catalog on page load
window.addEventListener('DOMContentLoaded', async () => {
    // Apply Telegram theme
    applyTelegramTheme();
    
    // Setup event listeners
    setupFilters();
    
    // Load flowers from API
    await loadFlowersFromAPI();
});

function applyTelegramTheme() {
    document.body.style.backgroundColor = tg.themeParams.bg_color || '#ffffff';
    document.body.style.color = tg.themeParams.text_color || '#222222';
}

async function loadFlowersFromAPI() {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/flowers`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch flowers');
        }
        
        flowers = await response.json();
        
        // Update flowers to use photo_url as photo for compatibility
        flowers = flowers.map(flower => ({
            ...flower,
            photo: flower.photo_url || PLACEHOLDER_IMAGE
        }));
        
        loadCatalog('all');
        showLoading(false);
    } catch (error) {
        console.error('Error loading flowers:', error);
        showError('Не удалось загрузить каталог. Попробуйте позже.');
        showLoading(false);
    }
}

function showLoading(show) {
    isLoading = show;
    const catalog = document.getElementById('catalog');
    
    if (show) {
        catalog.innerHTML = '<div class="loading-spinner">🌸 Загрузка...</div>';
    }
}

function showError(message) {
    const catalog = document.getElementById('catalog');
    catalog.innerHTML = `<div class="error-message">⚠️ ${message}</div>`;
}

function loadCatalog(category = 'all') {
    const catalog = document.getElementById('catalog');
    
    if (isLoading) return;
    
    if (!flowers || flowers.length === 0) {
        catalog.innerHTML = '<div class="empty-message">📦 Каталог пуст</div>';
        return;
    }
    
    catalog.innerHTML = '';
    
    const filteredFlowers = category === 'all' 
        ? flowers 
        : flowers.filter(f => f.category === category);
    
    if (filteredFlowers.length === 0) {
        catalog.innerHTML = '<div class="empty-message">🔍 Цветы в этой категории не найдены</div>';
        return;
    }
    
    filteredFlowers.forEach(flower => {
        const card = createFlowerCard(flower);
        catalog.appendChild(card);
    });
}

function createFlowerCard(flower) {
    const card = document.createElement('div');
    card.className = 'flower-card';
    
    // Create image element
    const img = document.createElement('img');
    img.src = flower.photo;
    img.alt = flower.name;
    img.onerror = function() { this.src = PLACEHOLDER_IMAGE; };
    
    // Create info container
    const info = document.createElement('div');
    info.className = 'flower-info';
    
    // Create name element
    const name = document.createElement('div');
    name.className = 'flower-name';
    name.textContent = flower.name;
    info.appendChild(name);
    
    // Create description element if exists
    if (flower.description) {
        const desc = document.createElement('div');
        desc.className = 'flower-description';
        desc.textContent = flower.description;  // Safe text content
        info.appendChild(desc);
    }
    
    // Create price element
    const price = document.createElement('div');
    price.className = 'flower-price';
    price.textContent = `${flower.price}₽`;
    info.appendChild(price);
    
    // Create add button
    const button = document.createElement('button');
    button.className = 'btn-add';
    button.textContent = 'Добавить';
    button.onclick = () => addToCart(flower.id);
    info.appendChild(button);
    
    // Assemble card
    card.appendChild(img);
    card.appendChild(info);
    
    return card;
}

function setupFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadCatalog(btn.dataset.category);
        });
    });
}

function addToCart(flowerId) {
    const flower = flowers.find(f => f.id === flowerId);
    if (flower) {
        cart.push(flower);
        updateCartCount();
        
        // Haptic feedback
        tg.HapticFeedback.impactOccurred('light');
        
        // Show notification
        tg.showPopup({
            message: `${flower.name} добавлен в корзину`,
            buttons: [{type: 'ok'}]
        });
    }
}

function updateCartCount() {
    document.getElementById('cart-count').textContent = cart.length;
}

function showCart() {
    const modal = document.getElementById('cart-modal');
    const cartItems = document.getElementById('cart-items');
    const totalPrice = document.getElementById('total-price');
    
    if (cart.length === 0) {
        cartItems.innerHTML = '<p style="text-align: center; padding: 20px;">Корзина пуста</p>';
        totalPrice.textContent = '0';
    } else {
        cartItems.innerHTML = '';
        let total = 0;
        
        cart.forEach((item, index) => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'cart-item';
            itemDiv.innerHTML = `
                <div>
                    <strong>${item.name}</strong><br>
                    <span>${item.price}₽</span>
                </div>
                <button onclick="removeFromCart(${index})" style="background: #ff4444; color: white; border: none; padding: 5px 10px; border-radius: 5px;">✕</button>
            `;
            cartItems.appendChild(itemDiv);
            total += item.price;
        });
        
        totalPrice.textContent = total;
    }
    
    modal.classList.add('show');
}

function closeCart() {
    document.getElementById('cart-modal').classList.remove('show');
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateCartCount();
    showCart();
    tg.HapticFeedback.impactOccurred('medium');
}

function checkout() {
    if (cart.length === 0) {
        tg.showAlert('Корзина пуста');
        return;
    }
    
    // Send cart data to bot
    const cartData = {
        items: cart,
        total: cart.reduce((sum, item) => sum + item.price, 0)
    };
    
    tg.sendData(JSON.stringify(cartData));
    tg.close();
}

// Builder functionality
let builderData = {
    color: null,
    quantity: null,
    addons: []
};

function showBuilder() {
    document.getElementById('builder-modal').classList.add('show');
    document.getElementById('step-color').classList.add('active');
}

function closeBuilder() {
    document.getElementById('builder-modal').classList.remove('show');
    builderData = { color: null, quantity: null, addons: [] };
}

// Color selection
document.addEventListener('DOMContentLoaded', () => {
    const colorBtns = document.querySelectorAll('.color-btn');
    colorBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            builderData.color = btn.dataset.color;
            document.getElementById('step-color').classList.remove('active');
            document.getElementById('step-quantity').classList.add('active');
            tg.HapticFeedback.impactOccurred('light');
        });
    });
    
    const qtyBtns = document.querySelectorAll('.qty-btn');
    qtyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            builderData.quantity = btn.dataset.qty;
            document.getElementById('step-quantity').classList.remove('active');
            document.getElementById('step-addons').classList.add('active');
            tg.HapticFeedback.impactOccurred('light');
        });
    });
});

function previewBouquet() {
    const checkboxes = document.querySelectorAll('.addon-options input[type="checkbox"]:checked');
    builderData.addons = Array.from(checkboxes).map(cb => cb.value);
    
    // Calculate price
    let basePrice = 2000;
    let addonPrice = 0;
    
    if (builderData.addons.includes('ribbon')) addonPrice += 100;
    if (builderData.addons.includes('luxury')) addonPrice += 300;
    if (builderData.addons.includes('toy')) addonPrice += 500;
    if (builderData.addons.includes('candy')) addonPrice += 400;
    
    const total = basePrice + addonPrice;
    
    // Add custom bouquet to cart
    const customBouquet = {
        id: 'custom_' + Date.now(),
        name: `Букет на заказ (${builderData.color}, ${builderData.quantity} шт)`,
        price: total,
        category: 'custom',
        custom: true,
        details: builderData
    };
    
    cart.push(customBouquet);
    updateCartCount();
    
    closeBuilder();
    
    tg.showPopup({
        message: `Букет добавлен в корзину за ${total}₽`,
        buttons: [{type: 'ok'}]
    });
}
