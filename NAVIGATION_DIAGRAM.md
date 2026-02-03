# Navigation Structure Diagram

```
                                    /start
                                      │
                            ┌─────────┴─────────┐
                            │   START MENU      │
                            │   (Main Screen)   │
                            └─────────┬─────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
              ┌─────▼──────┐   ┌─────▼──────┐   ┌─────▼──────┐
              │ AI Menu    │   │  Catalog   │   │   Cart     │
              │            │   │            │   │            │
              └─────┬──────┘   └────────────┘   └────────────┘
                    │                 
         ┌──────────┼──────────┐
         │          │          │
    ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
    │Birthday│ │Romance │ │Wedding │
    │(Preset)│ │(Preset)│ │(Preset)│
    └────────┘ └────────┘ └────────┘

                    /admin
                      │
              ┌───────┴────────┐
              │  ADMIN PANEL   │
              │  (Main Screen) │
              └───────┬────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
    ┌───▼────┐   ┌───▼────┐   ┌───▼────┐
    │Flowers │   │Orders  │   │Users   │
    │List    │   │List    │   │List    │
    └────────┘   └────────┘   └────────┘

    /recommend
        │
    ┌───▼─────────────┐
    │Recommend Presets│
    └───┬─────────────┘
        │
    ┌───▼────┐
    │Result  │
    │(with   │
    │Back)   │
    └────────┘
```

## Navigation Flow Legend

- `│` - Navigation path
- `▼` - User can navigate to
- Each box represents a screen with a "◀️ Назад" button
- Pressing Back follows the navigation stack (LIFO)
- All leaf nodes (end screens) have Back button to return

## Navigation Stack Examples

### Example 1: AI Menu Flow
```
User action:       Stack state:
/start            → []
Click "AI Menu"   → [START]
Click "Birthday"  → [START, AI_MENU]
Click "◀️ Назад"   → [START]          (returns to AI_MENU)
Click "◀️ Назад"   → []               (returns to START)
```

### Example 2: Admin Flow
```
User action:         Stack state:
/start              → []
/admin              → []               (resets stack)
Click "Orders"      → [ADMIN_MAIN]
Click "◀️ Назад"     → []               (returns to ADMIN_MAIN)
```

### Example 3: Complex Flow
```
User action:           Stack state:
/start                → []
Click "Catalog"       → [START]
Click "◀️ Назад"       → []               (back to START)
Click "Cart"          → [START]
Click "◀️ Назад"       → []               (back to START)
Click "History"       → [START]
Click "◀️ Назад"       → []               (back to START)
```

## Special Cases

### /build (FSM Builder)
The `/build` command uses its own FSM navigation system:
- `back_to_color` - Returns to color selection
- `back_to_quantity` - Returns to quantity selection
- These are NOT part of the universal navigation stack
- They work independently within the conversation handler

### Fallback to START
If the navigation stack is empty and user presses Back:
- The system defaults to START screen
- This ensures users always have a way to navigate

### Clearing Stack
The stack is cleared when:
- User runs `/start` command
- User runs `/admin` command
- User explicitly navigates to START via `back_to_start` callback
