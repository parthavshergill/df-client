# Dwarf Fortress Gameplay Guide

Reference: [DF Wiki Quickstart](https://dwarffortresswiki.org/Quickstart_guide)

## Early Game Priority

1. **Dig shelter** — `dig x1 y1 z x2 y2` then `dig-now` for instant
2. **Stockpile inside** — `stockpile x y z 5 5 all`
3. **Build workshops** — `build carpenter x y z` then `build still x y z`
4. **Enable labors** — `labor <name> BREWER on`, `labor <name> PLANT on`
5. **Order production** — `order brew 10`, `order MakeBarrel 5`

## Food & Drink

**Critical:** Dwarves NEED alcohol or they work slower and get unhappy.

```bash
# Set up brewing
build still x y z
labor <name> BREWER on
order brew 10
```

Food sources: plump helmets (sustainable farming), meat (butchery), fish.

## Labor Types

| Labor | Purpose |
|-------|---------|
| MINE | Mining (needs pick) |
| PLANT | Farming |
| BREWER | Brewing alcohol |
| CARPENTER | Woodworking |
| MASON | Stoneworking |
| COOK | Cooking meals |
| HAUL_FOOD, HAUL_STONE, etc. | Moving items |

## Workshop Types

| Type | Products |
|------|----------|
| carpenter | Beds, barrels, bins, furniture |
| still | Alcohol from plants |
| mason | Stone furniture, blocks |
| kitchen | Cooked meals |
| craftsdwarf | Crafts, totems |
| butcher | Meat from animals |

## Stockpile Presets

| Preset | Contents |
|--------|----------|
| all | Everything (best for general use) |
| food | Food and prepared meals |
| booze | Alcohol only |
| stone | Stone and ore |
| wood | Logs |
| weapons, armor | Military equipment |

## Why Are Dwarves Idle?

Check in order:
1. **Labor not enabled** — `labor <name> <LABOR> on`
2. **No tools** — Miners need picks, woodcutters need axes
3. **Needs not met** — Hungry/thirsty/tired dwarves prioritize self-care
4. **No path** — Blocked by walls, locked doors, or water

## Cheats (Recovery)

```bash
run "full-heal -all"           # Heal all dwarves
run "full-heal -unit ID -r"    # Resurrect specific dwarf
dig-now                         # Instant dig completion
run "exterminate RACE"         # Remove creatures
```
