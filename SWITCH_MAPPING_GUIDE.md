# Switch Mapping Guide

## Overview

This guide explains the new switch mapping abstraction layer that allows you to control relays using logical names (CH1, CH1A, etc.) instead of raw stack/relay numbers.

## Mapping Layout

The system uses a **sequential mapping** approach to minimize wiring complexity:

### Prototype Setup (2 Boards - Currently Available)

| Stack | Relay | Switch Name | Description |
|-------|-------|-------------|-------------|
| 0 | 1 | **CH1** | Chassis 1 |
| 0 | 2 | CH1A | Backboard A |
| 0 | 3 | CH1B | Backboard B |
| 0 | 4 | CH1C | Backboard C |
| 0 | 5 | CH1D | Backboard D |
| 0 | 6 | CH1E | Backboard E |
| 0 | 7 | CH1F | Backboard F |
| 0 | 8 | CH1G | Backboard G |
| 1 | 1 | CH1H | Backboard H |
| 1 | 2 | CH1I | Backboard I |
| 1 | 3 | CH1J | Backboard J |
| 1 | 4 | CH1K | Backboard K |
| 1 | 5 | **CH2** | Chassis 2 |
| 1 | 6 | CH2A | Backboard A |
| 1 | 7 | CH2B | Backboard B |
| 1 | 8 | CH2C | Backboard C |

### Full System (6 Boards - Future)

- **Total Switches**: 47
  - 4 Chassis: CH1, CH2, CH3, CH4
  - 43 Backboards: CH1A-K (11), CH2A-K (11), CH3A-K (11), CH4A-J (10)

**Complete Mapping**:
- **Stack 0**: CH1, CH1A-G
- **Stack 1**: CH1H-K, CH2, CH2A-C
- **Stack 2**: CH2D-K, CH3
- **Stack 3**: CH3A-G, CH4
- **Stack 4**: CH3H-K, CH4A-C
- **Stack 5**: CH4D-J, SPARE

## API Endpoints

### New Switch-Based API (Recommended)

#### Control Individual Switches

**Turn a switch ON:**
```bash
curl -X POST http://localhost:5001/api/switch/CH1 \
  -H "Content-Type: application/json" \
  -d '{"state": 1}'
```

**Turn a switch OFF:**
```bash
curl -X POST http://localhost:5001/api/switch/CH1A \
  -H "Content-Type: application/json" \
  -d '{"state": 0}'
```

**Get switch status:**
```bash
curl http://localhost:5001/api/switch/CH1
```

#### Chassis-Level Control

**Get all switches for a chassis:**
```bash
# Returns CH1 + CH1A-K with their states
curl http://localhost:5001/api/switch/chassis/1

# Returns CH2 + CH2A-K with their states
curl http://localhost:5001/api/switch/chassis/2
```

#### List All Switches

```bash
curl http://localhost:5001/api/switch/list
```

### Legacy API (Still Supported)

The original stack/relay API still works for backward compatibility:

```bash
# Turn Stack 0, Relay 1 ON (equivalent to CH1)
curl -X POST http://localhost:5001/api/relay/0/1 \
  -H "Content-Type: application/json" \
  -d '{"state": 1}'
```

## Web Interface

The updated web interface now displays:

- **Chassis Control Section**: Shows the main chassis switch (CH1)
- **Backboard Controls Section**: Shows all 11 backboards (CH1A-K)
- **API Examples**: curl command examples at the bottom of the page

Each switch button displays its logical name (CH1, CH1A, etc.) instead of relay numbers.

## Python Usage

### Using the SwitchMapper Class

```python
from hardware import switch_mapper

# Convert switch name to relay position
position = switch_mapper.get_relay_position('CH1')
print(position)  # (0, 1)

# Convert relay position to switch name
name = switch_mapper.get_switch_name(0, 1)
print(name)  # 'CH1'

# Get all valid switch names
all_switches = switch_mapper.get_all_switches()
print(all_switches)  # ['CH1', 'CH1A', 'CH1B', ...]

# Check if a switch name is valid
is_valid = switch_mapper.is_valid_switch('CH1')
print(is_valid)  # True
```

### Case Insensitivity

The API and mapper are case-insensitive:
- `CH1`, `ch1`, `Ch1` all work the same way
- `CH1A`, `ch1a`, `Ch1A` all work the same way

## Wiring Guide (Prototype)

For the current 2-board prototype, wire in this order:

1. **Board 1 (Stack 0)**:
   - Relay 1: CH1 (Chassis 1 power)
   - Relays 2-8: CH1A-G (First 7 backboards)

2. **Board 2 (Stack 1)**:
   - Relays 1-4: CH1H-K (Last 4 backboards for chassis 1)
   - Relay 5: CH2 (Chassis 2 power) - Optional for now
   - Relays 6-8: CH2A-C (First 3 backboards for chassis 2) - Optional for now

## Benefits

✅ **Intuitive naming**: Control switches by what they operate, not relay numbers  
✅ **Easier troubleshooting**: Immediately know which hardware is affected  
✅ **Scalable**: Easy to add more chassis/backboards  
✅ **Backward compatible**: Legacy API still works  
✅ **Type-safe**: Invalid switch names are rejected with clear error messages  

## Testing

Run the test suite to verify the mapping:

```bash
python3 test_switch_mapping.py
```

This will validate all 47 switch mappings and ensure the bidirectional conversion works correctly.

