// Telegram Web App initialization
let tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

// Sample flowers data (in production, this would come from the bot)
const flowers = [
    {
        id: 1,
        name: "Розы классические",
        description: "Букет из 15 красных роз",
        price: 2500,
        category: "roses",
        photo: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=300&h=300&fit=crop"
    },
    {
        id: 2,
        name: "Тюльпаны микс",
        description: "Букет из 25 разноцветных тюльпанов",
        price: 1800,
        category: "tulips",
        photo: "https://images.unsplash.com/photo-1520763185298-1b434c919102?w=300&h=300&fit=crop"
    },
    {
        id: 3,
        name: "Пионы нежные",
        description: "Букет из 7 розовых пионов",
        price: 3200,
        category: "peonies",
        photo: "https://images.unsplash.com/photo-1588699111448-4e6c7a155a47?w=300&h=300&fit=crop"
    },
    {
        id: 4,
        name: "Букет 'День рождения'",
        description: "Яркий микс из роз, хризантем",
        price: 2000,
        category: "mixed",
        photo: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=300&h=300&fit=crop"
    },
    {
        id: 5,
        name: "Монобукет хризантем",
        description: "Букет из белых хризантем",
        price: 1500,
        category: "mixed",
        photo: "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=300&h=300&fit=crop"
    }
];

// Cart management
let cart = [];

// Load catalog on page load
window.addEventListener('DOMContentLoaded', () => {
    loadCatalog();
    setupFilters();
    
    // Apply Telegram theme
    document.body.style.backgroundColor = tg.themeParams.bg_color || '#ffffff';
    document.body.style.color = tg.themeParams.text_color || '#222222';
});

function loadCatalog(category = 'all') {
    const catalog = document.getElementById('catalog');
    catalog.innerHTML = '';
    
    const filteredFlowers = category === 'all' 
        ? flowers 
        : flowers.filter(f => f.category === category);
    
    filteredFlowers.forEach(flower => {
        const card = createFlowerCard(flower);
        catalog.appendChild(card);
    });
}

function createFlowerCard(flower) {
    const card = document.createElement('div');
    card.className = 'flower-card';
    card.innerHTML = `
        <img src="${flower.photo}" alt="${flower.name}" onerror="this.src='https://via.placeholder.com/300x300.png?text=Flower'">
        <div class="flower-info">
            <div class="flower-name">${flower.name}</div>
            <div class="flower-price">${flower.price}₽</div>
            <button class="btn-add" onclick="addToCart(${flower.id})">Добавить</button>
        </div>
    `;
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
