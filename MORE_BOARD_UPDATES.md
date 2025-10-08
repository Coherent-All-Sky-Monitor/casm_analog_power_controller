# 📋 When You Get More Boards (Upgrade from 1 to 6)

Currently configured for **1 board (16 relays)**. When you receive the other 5 boards, follow these steps:

---

## 🔧 Step 1: Update `hardware/__init__.py`

**Line 10:**
```python
# Change this:
NUM_STACKS = 1  # Change to 6 when you have all boards

# To this:
NUM_STACKS = 6  # All 6 boards installed
```

---

## 🎨 Step 2: Update `hardware/templates/index.html`

**Line 13 (subtitle):**
```html
<!-- Change this: -->
<p class="subtitle">1 Board × 16 Relays (16 Total) - Hardware Control</p>

<!-- To this: -->
<p class="subtitle">6 Stacks × 16 Relays (96 Total) - Hardware Control</p>
```

**Line 73 (JavaScript):**
```javascript
// Change this:
const NUM_STACKS = 1;  // Change to 6 when you have all boards

// To this:
const NUM_STACKS = 6;  // All 6 boards installed
```

---

## 🚀 Step 3: Update `run_hardware.py`

**Line 18:**
```python
# Change this:
print("🔌 Controlling 1 board × 16 relays = 16 total relays")

# To this:
print("🔌 Controlling 6 stacks × 16 relays = 96 total relays")
```

**Line 20 (remove this line):**
```python
# Delete this line:
print("⚠️  Change NUM_STACKS to 6 when you have all boards")
```

---

## ⚙️ Step 4: Configure Hardware Jumpers

Set each board to a different stack level using the jumpers:
- Board 1 → Stack 0 (no jumpers)
- Board 2 → Stack 1
- Board 3 → Stack 2
- Board 4 → Stack 3
- Board 5 → Stack 4
- Board 6 → Stack 5

Refer to the Sequent Microsystems documentation for jumper settings.

---

## ✅ Step 5: Test

```bash
python3 run_hardware.py
```

Then check:
- All 6 stacks should show in the web UI
- Health check should show all stacks as "connected"
- Each stack should have 16 independently controllable relays

---

## 📍 Quick Reference

**3 files to update:**
1. `hardware/__init__.py` → Line 10: `NUM_STACKS = 6`
2. `hardware/templates/index.html` → Lines 13 & 73
3. `run_hardware.py` → Line 18

**That's it!** All the code already supports 6 boards - just uncomment/update those numbers.

