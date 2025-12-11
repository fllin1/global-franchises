# Territory Availability Logic

This document describes the hierarchical availability system used to determine territory availability status in the franchise territory map.

## Data Sources

### 1. `unavailable_states` (Franchise Level Default)

An array of state codes from the `franchises` table indicating which states are **unavailable by default**.

```typescript
// Example: ["CA", "CT", "HI", "IL", "IN", "MD", "MN", "NY", "RI", "UT", "VA", "WA"]
data.unavailable_states: string[]
```

### 2. Territory Checks (Specific Location Checks)

Individual territory checks from the `territory_checks` table, organized hierarchically:

```typescript
// Structure: State -> County -> City -> [Checks]
data.states[stateCode][county][city]: TerritoryCheck[]

interface TerritoryCheck {
  availability_status: 'Available' | 'Not Available';
  city: string;
  county: string | null;
  zip_code: string | null;
  // ... other fields
}
```

## Availability Status Types

| Status | Color | Meaning |
|--------|-------|---------|
| `available` | 🟢 Green | Territory is open for franchising |
| `unavailable` | 🔴 Red | Territory is not available |
| `mixed` | 🟡 Yellow | Some areas available, some not |

## Hierarchical Logic

### State Level (`getStateAvailability`)

The state-level availability uses a **default + override** pattern:

```
IF state is in unavailable_states (default UNAVAILABLE):
    IF state has ANY territory check with "Available" status:
        → RETURN "mixed" (some areas available despite default)
    ELSE:
        → RETURN "unavailable"

ELSE (state is NOT in unavailable_states, default AVAILABLE):
    IF state has ANY territory check with "Not Available" status:
        → RETURN "mixed" (some areas unavailable despite default)
    ELSE:
        → RETURN "available"
```

**Note:** State-level blanket checks (territory checks without county/city) take precedence.

### County Level (`getCountyAvailability`)

Counties inherit from their parent state's default when no check data exists:

```
IF county has blanket territory check:
    → Use that check's status directly

ELSE IF county has city-level territory checks:
    → Aggregate from city statuses:
        - All available → "available"
        - All unavailable → "unavailable"
        - Mixed → "mixed"

ELSE (no territory check data):
    → INHERIT from state default:
        - State in unavailable_states → "unavailable"
        - State NOT in unavailable_states → "available"
```

### City Level (`getCityAvailability`)

Cities follow the same inheritance pattern:

```
IF city has blanket territory check (no zip):
    → Use that check's status directly

ELSE IF city has zip-level territory checks:
    → Aggregate from zip statuses

ELSE (no territory check data):
    → INHERIT from state default
```

### Zip Level (`getZipAvailability`)

Zips use direct data aggregation (no inheritance needed):

```
IF all checks for zip are "Available":
    → "available"
ELSE IF all checks for zip are "Not Available":
    → "unavailable"
ELSE:
    → "mixed"
```

## Example: Franchise 626

### Initial State

- **Unavailable States:** CA, CT, HI, IL, IN, MD, MN, NY, RI, UT, VA, WA
- **Territory Checks:**
  - IL → Chicago: Not Available
  - IL → Naperville: Available
  - VA → Haymarket: Not Available
  - VA → Glen Allen: Not Available

### Resulting Availability

| State | Default | Has Available Check? | Has Unavailable Check? | Result |
|-------|---------|---------------------|----------------------|--------|
| IL | Unavailable | Yes (Naperville) | Yes (Chicago) | **Mixed** 🟡 |
| VA | Unavailable | No | Yes | **Unavailable** 🔴 |
| TX | Available | - | No | **Available** 🟢 |
| NC | Available | - | No | **Available** 🟢 |
| CA | Unavailable | No | No | **Unavailable** 🔴 |

### Drilling into Illinois

When viewing IL counties:

| County | Has Territory Check? | Inherited Status |
|--------|---------------------|------------------|
| Cook (Chicago) | Yes (Not Available) | Red 🔴 |
| DuPage (Naperville) | Yes (Available) | Green 🟢 |
| Other Counties | No | Red 🔴 (inherit IL default) |

## Key Implementation Details

### Helper Functions

```typescript
// Check if state is default unavailable
isStateDefaultUnavailable(stateCode: string): boolean

// Get all territory checks in a state (flattened)
getAllChecksInState(stateCode: string): TerritoryCheck[]

// Check for any Available check in state
stateHasAnyAvailableCheck(stateCode: string): boolean

// Check for any Not Available check in state
stateHasAnyUnavailableCheck(stateCode: string): boolean
```

### Data Structure Handling

The API returns a 4-level hierarchy, but some states may have flattened data. The `getAllChecksInState` function handles both:

- **4-level:** `states[state][county][city] = [checks]`
- **3-level:** `states[state][city] = [checks]` (when county is null)

## Visual Representation

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRANCHISE 626                             │
│                                                                  │
│  unavailable_states: [CA, CT, HI, IL, IN, MD, MN, NY, RI, ...]  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │   IL    │          │   VA    │          │   TX    │
   │ DEFAULT │          │ DEFAULT │          │ DEFAULT │
   │ UNAVAIL │          │ UNAVAIL │          │ AVAIL   │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                    │                    │
   Has Available?       Has Available?       Has Unavail?
   ┌────┴────┐          ┌────┴────┐          ┌────┴────┐
   │ YES     │          │ NO      │          │ NO      │
   │(Naper.) │          │         │          │         │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ MIXED   │          │ UNAVAIL │          │ AVAIL   │
   │   🟡    │          │   🔴    │          │   🟢    │
   └─────────┘          └─────────┘          └─────────┘
```

## Files Modified

- `frontend/src/components/FranchiseTerritoryMap.client.tsx`
  - `isStateDefaultUnavailable()` - New helper function
  - `getAllChecksInState()` - New helper function  
  - `stateHasAnyAvailableCheck()` - New helper function
  - `stateHasAnyUnavailableCheck()` - New helper function
  - `getStateAvailability()` - Updated with override logic
  - `getCountyAvailability()` - Updated with inheritance
  - `getCityAvailability()` - Updated with inheritance

## Testing Scenarios

1. ✅ State in `unavailable_states` with Available check → Mixed (yellow)
2. ✅ State in `unavailable_states` with only Unavailable checks → Unavailable (red)
3. ✅ State NOT in `unavailable_states` with only Available checks → Available (green)
4. ✅ State NOT in `unavailable_states` with Unavailable check → Mixed (yellow)
5. ✅ Drill-down: Counties without checks inherit state default














