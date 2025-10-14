# Wiring Diagram - Switch Mapping

## Complete System Map (6 Boards - 47 Switches)

```
┌─────────────────────────────────────────────────────────────────┐
│                        STACK 0 (Board 1)                         │
├────────┬───────────────────────────────────────────────────────┤
│ Relay  │ Switch Name                                            │
├────────┼───────────────────────────────────────────────────────┤
│   1    │ CH1 ← CHASSIS 1                                        │
│   2    │ CH1A                                                   │
│   3    │ CH1B                                                   │
│   4    │ CH1C                                                   │
│   5    │ CH1D                                                   │
│   6    │ CH1E                                                   │
│   7    │ CH1F                                                   │
│   8    │ CH1G                                                   │
└────────┴───────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        STACK 1 (Board 2)                         │
├────────┬───────────────────────────────────────────────────────┤
│ Relay  │ Switch Name                                            │
├────────┼───────────────────────────────────────────────────────┤
│   1    │ CH1H                                                   │
│   2    │ CH1I                                                   │
│   3    │ CH1J                                                   │
│   4    │ CH1K ← End of Chassis 1 Backboards                     │
│   5    │ CH2 ← CHASSIS 2                                        │
│   6    │ CH2A                                                   │
│   7    │ CH2B                                                   │
│   8    │ CH2C                                                   │
└────────┴───────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        STACK 2 (Board 3)                         │
├────────┬───────────────────────────────────────────────────────┤
│ Relay  │ Switch Name                                            │
├────────┼───────────────────────────────────────────────────────┤
│   1    │ CH2D                                                   │
│   2    │ CH2E                                                   │
│   3    │ CH2F                                                   │
│   4    │ CH2G                                                   │
│   5    │ CH2H                                                   │
│   6    │ CH2I                                                   │
│   7    │ CH2J                                                   │
│   8    │ CH2K ← End of Chassis 2 Backboards                     │
└────────┴───────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        STACK 3 (Board 4)                         │
├────────┬───────────────────────────────────────────────────────┤
│ Relay  │ Switch Name                                            │
├────────┼───────────────────────────────────────────────────────┤
│   1    │ CH3 ← CHASSIS 3                                        │
│   2    │ CH3A                                                   │
│   3    │ CH3B                                                   │
│   4    │ CH3C                                                   │
│   5    │ CH3D                                                   │
│   6    │ CH3E                                                   │
│   7    │ CH3F                                                   │
│   8    │ CH3G                                                   │
└────────┴───────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        STACK 4 (Board 5)                         │
├────────┬───────────────────────────────────────────────────────┤
│ Relay  │ Switch Name                                            │
├────────┼───────────────────────────────────────────────────────┤
│   1    │ CH3H                                                   │
│   2    │ CH3I                                                   │
│   3    │ CH3J                                                   │
│   4    │ CH3K ← End of Chassis 3 Backboards                     │
│   5    │ CH4 ← CHASSIS 4                                        │
│   6    │ CH4A                                                   │
│   7    │ CH4B                                                   │
│   8    │ CH4C                                                   │
└────────┴───────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        STACK 5 (Board 6)                         │
├────────┬───────────────────────────────────────────────────────┤
│ Relay  │ Switch Name                                            │
├────────┼───────────────────────────────────────────────────────┤
│   1    │ CH4D                                                   │
│   2    │ CH4E                                                   │
│   3    │ CH4F                                                   │
│   4    │ CH4G                                                   │
│   5    │ CH4H                                                   │
│   6    │ CH4I                                                   │
│   7    │ CH4J ← End of Chassis 4 Backboards (10 total)          │
│   8    │ SPARE (Not mapped)                                     │
└────────┴───────────────────────────────────────────────────────┘
```

## Summary by Chassis

### CH1 (12 switches)
- **Chassis**: CH1 → Stack 0, Relay 1
- **Backboards**: CH1A-K → Stacks 0-1, Relays 2-8, 1-4

### CH2 (12 switches)
- **Chassis**: CH2 → Stack 1, Relay 5
- **Backboards**: CH2A-K → Stacks 1-2, Relays 6-8, 1-8

### CH3 (12 switches)
- **Chassis**: CH3 → Stack 3, Relay 1
- **Backboards**: CH3A-K → Stacks 3-4, Relays 2-8, 1-4

### CH4 (11 switches)
- **Chassis**: CH4 → Stack 4, Relay 5
- **Backboards**: CH4A-J → Stacks 4-5, Relays 6-8, 1-7

## Current Prototype (Boards 1-2 Only)

```
✅ AVAILABLE NOW (2 boards = 16 relays):
   - CH1 (chassis)
   - CH1A through CH1K (all 11 backboards)
   - CH2 (chassis)
   - CH2A through CH2C (first 3 backboards)

⏳ COMING LATER (when you get 4 more boards):
   - CH2D through CH2K
   - CH3, CH3A-K
   - CH4, CH4A-J
```

## Quick Reference

| What | Switches | Total |
|------|----------|-------|
| Chassis | CH1, CH2, CH3, CH4 | 4 |
| CH1 Backboards | CH1A-K | 11 |
| CH2 Backboards | CH2A-K | 11 |
| CH3 Backboards | CH3A-K | 11 |
| CH4 Backboards | CH4A-J | 10 |
| **TOTAL** | | **47** |

