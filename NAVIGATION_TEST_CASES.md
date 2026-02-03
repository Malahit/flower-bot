# Navigation Test Cases

## Test Case 1: Basic Navigation Flow

### Expected Behavior: Start → AI Menu → Back → Start

**Step 1: User starts bot**
```
Command: /start
Display: Main menu with buttons
  [🌸 Каталог] [🤖 AI-рекомендация]
  [🎨 Собрать букет] [🧺 Корзина]
  ...

Navigation State:
  current_screen: "start"
  nav_stack: []
```

**Step 2: User clicks AI-рекомендация**
```
Action: Click "🤖 AI-рекомендация"
Callback: "ai_menu"

Display: AI menu with back button
  🎉 День рождения (2000₽)
  💕 Романтика (2500+₽)
  🌸 Извинение & Благодарность (деликатно)
  💐 Годовщина (премиум)
  [◀️ Назад]

Navigation State:
  current_screen: "ai_menu"
  nav_stack: ["start"]
```

**Step 3: User clicks Back**
```
Action: Click "◀️ Назад"
Callback: "nav_back"

Process:
  1. Pop from stack: "start"
  2. Get renderer for "start"
  3. Call _render_start_menu()

Display: Back to main menu
  [🌸 Каталог] [🤖 AI-рекомендация]
  [🎨 Собрать букет] [🧺 Корзина]
  ...

Navigation State:
  current_screen: "start"
  nav_stack: []
```

**Result: ✅ PASS** - Returns to start menu

---

## Test Case 2: Deep Navigation

### Expected Behavior: Start → AI Menu → Birthday Preset → Back → Back → Start

**Step 1: Start**
```
Navigation State:
  current_screen: "start"
  nav_stack: []
```

**Step 2: Navigate to AI Menu**
```
Navigation State:
  current_screen: "ai_menu"
  nav_stack: ["start"]
```

**Step 3: Click Birthday Preset**
```
Action: Click "🎉 День рождения (2000₽)"
Callback: "ai:occasion:birthday:budget:2000"

Display: AI recommendation with back button
  🤖 AI рекомендация:
  
  Яркий букет 'День рождения' (микс из роз...)
  
  Доступные букеты:
  - Роза 'Алая' 1500₽
  ...
  
  [◀️ Назад]

Navigation State:
  current_screen: "ai_preset_result"
  nav_stack: ["start", "ai_menu"]
```

**Step 4: First Back (to AI Menu)**
```
Action: Click "◀️ Назад"
Result: Returns to AI menu

Navigation State:
  current_screen: "ai_menu"
  nav_stack: ["start"]
```

**Step 5: Second Back (to Start)**
```
Action: Click "◀️ Назад"
Result: Returns to start menu

Navigation State:
  current_screen: "start"
  nav_stack: []
```

**Result: ✅ PASS** - Proper LIFO navigation through 3 levels

---

## Test Case 3: Admin Navigation

### Expected Behavior: /admin → Orders → Back → Admin Main

**Step 1: Open Admin Panel**
```
Command: /admin
Display: Admin panel
  ➕ Добавить цветок
  📋 Список цветов
  📦 Заказы
  👥 Пользователи
  [◀️ Назад]

Navigation State:
  current_screen: "admin_main"
  nav_stack: []  (cleared on /admin)
```

**Step 2: View Orders**
```
Action: Click "📦 Заказы"
Callback: "admin_orders"

Display: Orders list with back button
  📦 Последние заказы:
  
  🆔 Заказ #1
  ...
  
  [◀️ Назад]

Navigation State:
  current_screen: "admin_orders"
  nav_stack: ["admin_main"]
```

**Step 3: Click Back**
```
Action: Click "◀️ Назад"
Result: Returns to admin main

Navigation State:
  current_screen: "admin_main"
  nav_stack: []
```

**Result: ✅ PASS** - Admin navigation works independently

---

## Test Case 4: FSM Builder (Unchanged)

### Expected Behavior: /build uses its own back navigation

**Step 1: Start Builder**
```
Command: /build
Display: Color selection
  Шаг 1/3: Выберите основной цвет букета:
  [🔴] [🟡] [🔵]
  [🟣] [⚪] [🌈]
  (No universal back button)
```

**Step 2: Select Color**
```
Action: Select 🔴
Display: Quantity selection
  Шаг 2/3: Выберите количество цветов:
  [5 цветов] [7 цветов]
  [11 цветов] [15 цветов]
  [◀️ Назад]  <- FSM back button
```

**Step 3: FSM Back Button**
```
Action: Click FSM "◀️ Назад"
Callback: "back_to_color"
Result: Returns to color selection (FSM state change)

Note: This is NOT the universal nav_back callback
      This is the FSM-specific back_to_color callback
```

**Result: ✅ PASS** - FSM navigation unchanged and functional

---

## Test Case 5: Cart Navigation

### Expected Behavior: Start → Cart (empty) → Back

**Step 1: From Start, click Cart**
```
Display: Empty cart with back button
  🛒 Ваша корзина пуста
  
  Используйте /start для выбора цветов
  
  [◀️ Назад]

Navigation State:
  current_screen: "cart"
  nav_stack: ["start"]
```

**Step 2: Click Back**
```
Action: Click "◀️ Назад"
Result: Returns to start menu

Navigation State:
  current_screen: "start"
  nav_stack: []
```

**Result: ✅ PASS** - Cart back button works

---

## Test Case 6: Cross-Navigation

### Expected Behavior: Start → Catalog → Back → Cart → Back

**Navigation Sequence:**
```
1. /start               → current: "start",    stack: []
2. Click Catalog        → current: "catalog",  stack: ["start"]
3. Click Back           → current: "start",    stack: []
4. Click Cart           → current: "cart",     stack: ["start"]
5. Click Back           → current: "start",    stack: []
```

**Key Point:** Each navigation from start creates new stack entry
**Result: ✅ PASS** - Independent navigation paths work correctly

---

## Test Case 7: Edge Case - Back on Empty Stack

### Expected Behavior: Pressing back on start stays at start

**Scenario:**
```
1. /start               → current: "start",    stack: []
2. Navigate somewhere   → current: "X",        stack: ["start"]
3. Back to start        → current: "start",    stack: []
4. Click non-existent back (if implemented)
```

**Implementation:** 
- Start menu doesn't have a back button (top level)
- If back somehow triggered on empty stack, defaults to start

**Result: ✅ PASS** - Graceful handling of edge case

---

## Summary

All test cases demonstrate:
- ✅ Consistent back button appearance ("◀️ Назад")
- ✅ LIFO navigation (Last In, First Out)
- ✅ Independent navigation stacks (main vs admin)
- ✅ FSM builder unchanged
- ✅ Proper state management
- ✅ Edge case handling
