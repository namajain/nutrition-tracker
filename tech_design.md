**Version 1.0 — November 16, 2025**

**Goal:** Build an *accurate*, *reliable*, and *user-adaptive* nutrition tracking system supporting AI-assisted and manual food logging, dual recipe modeling (granular vs. direct), seamless bidirectional conversion, and precise portion-size control at the point of logging.

---

## 1. Introduction

### 1.1 Purpose

This document defines the end-to-end technical design for a nutrition tracking feature that empowers users to log food intake with flexibility and confidence — whether capturing a meal via photo, building custom recipes from scratch, or adjusting for real-world portion sizes (e.g., eating half a serving). The system prioritizes traceable accuracy while minimizing friction.

### 1.2 Core Capabilities

- ✅ **AI-Assisted Logging**: Upload photo → LLM suggests *granular* recipe → user edits or simplifies
- ✅ **Dual Recipe Types**:
    - **Granular**: Ingredient-level decomposition with additive nutrition computation
    - **Direct**: Top-level nutrition entry for speed and convenience
- ✅ **Lossless Conversion**: One-click switch between Granular and Direct, with full auditability
- ✅ **Portion-Aware Logging**: Scale any recipe by custom amount (grams, milliliters, fractions, pieces) at logging time
- ✅ **User Control**: Edit at any level — ingredients, recipe nutrition, or final logged entry
- ✅ **Core Nutrition Profile**: Energy (kcal), Protein (g), Carbohydrates (g) — extensible for future micronutrients

### 1.3 Out of Scope

- Micronutrient tracking (vitamins, minerals) — *Phase 2*
- Barcode scanning integration — *Phase 2*
- Integration with external health platforms (Apple Health, Google Fit)
- Automated meal planning or macro-goal enforcement

---

## 2. Core Concepts & Data Model

### 2.1 Recipe Types

| Type | Description | Nutrition Source | Best For |
| --- | --- | --- | --- |
| **Granular** | Full decomposition: recipe → ingredients → nutrition. Quantities and units per ingredient are stored and editable. | Computed additively from verified ingredient data (e.g., USDA FDC) | Home cooking, dietitian use, precision tracking, custom formulations |
| **Direct** | No ingredients. Final nutrition values are stored explicitly. | User-entered, lab-reported, or flattened from a Granular recipe | Packaged foods, quick logging, restaurant meals, AI-derived one-offs |
- All AI-generated suggestions *begin as Granular* to ensure traceability and auditability.
- Conversion between types is user-initiated, reversible, and versioned.

---

### 2.2 Portion Size Strategy

- **Recipes define one *standard serving*** (e.g., “1 bowl”, “1 bar”, “200g”).
- **Portion adjustment happens *only at food logging time*** via a flexible multiplier.
- Users can specify portion as:
    - Fraction (½, ⅔, 1, 1½)
    - Numeric multiplier (0.7, 1.3, 2.5)
    - Custom weight (e.g., *175 g*) or volume (e.g., *120 ml*)
    - Piece count (e.g., *½ apple*, *2 slices*)
- Final nutrition = base recipe nutrition × portion multiplier.

> ✅ Standard Serving Definition:
> 
> - *Granular recipes*: Automatically computed as total mass (grams) of all ingredients.
> - *Direct recipes*: Defined by the user during first use or editing (e.g., “1 serving = 50g” or “1 bar”).

---

### 2.3 Domain Entities

| Entity | Description |
| --- | --- |
| `User` | Authenticated app user with preferences |
| `Ingredient` | Canonical food item with verified nutrition per 100g, density, and typical piece weight. Sourced from USDA FDC or moderated user submissions. |
| `Recipe` | Reusable food template. Has a type (`Granular`/`Direct`), name, and nutritional strategy. Includes provenance metadata (source, confidence, verification status). |
| `RecipeIngredient` | Links an ingredient to a *Granular* recipe, with quantity and unit. |
| `NutritionProfile` | Structured nutrition object: `{ energy_kcal: number, protein_g: number, carbs_g: number }`. |
| `FoodEntry` | Logged instance in the user’s diary. References a recipe (or custom food), stores portion multiplier, and supports final nutrition overrides. |

---

### 2.4 Data Schema Highlights (PostgreSQL)

- `recipes.type`: Enforced enum (`'GRANULAR'`, `'DIRECT'`)
- `recipes.nutrition_direct`: JSONB field (required *only* for `DIRECT` type)
- `recipe_ingredients`: Used *only* for `GRANULAR` recipes
- `food_entries.serving_multiplier`: Positive float (default `1.0`), representing portion scale
- `recipe_versions`: Immutable snapshots for audit and undo of type conversions
- Constraints ensure data consistency:
    - A `DIRECT` recipe cannot have ingredients
    - A `GRANULAR` recipe cannot store top-level nutrition
    - Portion multipliers must be > 0

> 🔒 All nutrition overrides (recipe- or entry-level) are stored separately to preserve auditability and allow reversion.
> 

---

## 3. System Architecture

```
┌──────────────────────────────┐
│        Frontend              │
│ (Cross-platform: iOS, Android, Web)
└───────────────┬──────────────┘
                │ HTTPS
                ▼
┌───────────────────────────────────────────────────────┐
│                   API Gateway                         │
│ - Authentication & authorization                      │
│ - Request validation & rate limiting                  │
└───────────────────────┬───────────────────────────────┘
                        ▼
      ┌───────────────────────────────────────────────────────────┐
      │                    Core Microservices                       │
      ├───────────────────────────────────────────────────────────┤
      │ • ImageProcessingService     • RecipeConversionService     │
      │ • NutritionService           • IngredientService           │
      │ • RecipeService              • EntryService                 │
      └───────────────────────┬───────────────────────────────────┘
                              ▼
      ┌───────────────────────────────────────────────────────────┐
      │                      Data Layer                            │
      ├───────────────────────────────────────────────────────────┤
      │ • PostgreSQL (relational store, ACID compliance)           │
      │ • Redis (caching: computed nutrition, FDC lookups)         │
      │ • Object Storage (user-uploaded images, encrypted)         │
      └───────────────────────────────────────────────────────────┘

```

### 3.1 Key Services

| Service | Responsibility |
| --- | --- |
| **ImageProcessingService** | Orchestrates secure image upload, OCR, and LLM inference to produce *Granular* recipe drafts. Enforces traceability by never skipping to Direct. |
| **NutritionService** | Computes nutrition for Granular recipes; applies portion scaling and overrides; validates unit conversions; calculates diffs for Expand workflows. |
| **RecipeService** | Manages recipe lifecycle, enforces type constraints, and coordinates with Conversion Service. |
| **RecipeConversionService** | Handles atomic, versioned transitions between Granular and Direct types. |
| **EntryService** | Processes food logs: resolves base nutrition, applies portion scaling, stores final entry. |
| **IngredientService** | Provides fuzzy search, FDC integration, and robust unit/density resolution. |

---

## 4. Key Workflows

### 4.1 AI-Assisted Food Logging (Photo → Log)

1. User uploads a photo of their meal.
2. System processes the image and uses an LLM to extract a *Granular* recipe draft (name + ingredients with estimated quantities and units).
3. Nutrition is resolved using authoritative ingredient data (e.g., USDA FDC), and a confidence score is assigned.
4. User reviews the draft in the app:
    - Edits ingredients, quantities, or units
    - Sees real-time computed nutrition
    - Chooses to **Save as Granular** or **Use Final Values Only** (flattens to Direct)
5. Upon confirmation, the recipe is saved and optionally logged immediately with portion input.

> ✅ Accuracy Guardrails:
> 
> - Low-confidence ingredients are highlighted for review.
> - Unresolved items require manual selection from ingredient database.
> - Flattening is an explicit, one-click action — never automatic.

![image.png](attachment:ea55da64-4538-407b-90a4-f604f7bfca22:image.png)

---

### 4.2 Recipe Type Conversion

### Granular → Direct (“Simplify”)

- Triggered by user action (e.g., “Use Final Values Only”).
- System computes current nutrition from ingredients.
- A version snapshot is archived for audit and potential undo.
- The recipe is converted: type set to `Direct`, ingredients removed, nutrition stored directly.
- User verification status is updated.

### Direct → Granular (“Edit Ingredients”)

- User initiates expansion to refine or verify nutrition.
- A snapshot is saved.
- Recipe type changes to `Granular`; nutrition field is cleared.
- UI presents the original nutrition as a *target* while user builds ingredient list.
- Real-time diff shows deviation from target (e.g., “+3g carbs”).

> 🔄 Reversibility: Users can undo conversions within 90 days using version history.
> 

---

### 4.3 Food Logging with Portion Control

1. User selects a saved recipe (Granular or Direct).
2. App displays the **standard serving** (e.g., *“1 bowl (350g)”* or *“1 bar (50g)”*).
3. User specifies portion using one of four intuitive methods:
    - **Fraction buttons**: ½, ⅔, ¾, 1, 1½, 2
    - **Slider**: Continuous range (0.1x to 3.0x)
    - **Custom amount**: Numeric input + unit (e.g., `175` `g`, `120` `ml`, `½` `piece`)
    - **Visual aid**: Interactive plate/portion diagram
4. System computes `serving_multiplier`:
    - For fractional/slider: direct value
    - For custom amount: `entered_amount / standard_serving_amount`
5. Final nutrition is previewed in real time (e.g., *“175g (50%): 210 kcal • 6g P • 32.5g C”*).
6. User confirms → entry is saved with `serving_multiplier` and optional override.

> 🛡️ Edge Handling:
> 
> - If standard serving is undefined (e.g., new Direct recipe), user is prompted to define it once.
> - Volume-to-mass conversions use ingredient density; missing density triggers a safe estimate or user input.

---

## 5. Nutrition Computation & Accuracy

### 5.1 Granular Nutrition Calculation

- Nutrition is computed as the sum of each ingredient’s contribution:`(nutrient per 100g) × (quantity in grams / 100)`
- All nutrients (energy, protein, carbs) are calculated independently.
- Results are rounded consistently: energy to nearest kcal, macros to 1 decimal.

### 5.2 Unit Conversion Framework

- **Mass units** (g, kg, oz, lb) and **volume units** (ml, l, cup, tbsp, tsp) are supported.
- Conversion to base units (g for mass, ml for volume) occurs at storage time.
- **Volume → Mass** requires ingredient density:
    - USDA defaults are used where available
    - User is alerted and guided if density is unknown
- **Piece-based entries** use average piece weight (e.g., apple = 182g).

### 5.3 Portion Scaling

- Final nutrition = (base recipe nutrition) × `serving_multiplier`
- Multiplier is derived from user’s portion input relative to the recipe’s standard serving.
- Overrides at the food entry level apply *after* portion scaling.

---

## 6. Reliability & Validation

### 6.1 Data Quality Safeguards

| Risk | Mitigation |
| --- | --- |
| **LLM inaccuracy** | LLM provides structure only — nutrition sourced post-hoc from verified databases. Confidence scoring and manual review required for low-confidence items. |
| **Unit/density errors** | Strict validation; blocks saves with missing critical data. Uses USDA defaults where possible. |
| **Portion confusion** | Clear labeling of standard serving; real-time preview of scaled nutrition. |
| **Override misuse** | Overrides are visible, auditable, and reversible. High override rates trigger product review. |
| **Stale ingredient data** | Weekly sync with USDA FDC; historic entries retain original nutrition snapshot. |

### 6.2 Validation Plan

| Test | Method | Success Criteria |
| --- | --- | --- |
| **Nutrition Accuracy** | Compute 100 USDA-standard recipes | ≤2% error vs. official values |
| **Portion Scaling** | Log 50 entries with custom amounts (g/ml) | Final nutrition matches manual calculation |
| **Conversion Integrity** | Round-trip 100 recipes (Granular ↔ Direct ↔ Granular) | Final computed nutrition within 5% of original |
| **AI Draft Quality** | Human evaluation of 500 image-derived drafts | ≥85% ingredient names correct; ≥70% quantities within ±25% |
| **Concurrency Safety** | Simulate simultaneous edits | No data loss; conflict warnings when needed |

---

## 7. APIs (Key Endpoints)

| Endpoint | Method | Description |
| --- | --- | --- |
| `POST /upload/food-image` | `multipart/form-data` | Upload image → returns *Granular* recipe draft with computed nutrition and confidence |
| `POST /recipes` | `JSON` | Create new recipe (Granular or Direct); validates type/data consistency |
| `POST /recipes/{id}/flatten` | — | Convert Granular → Direct; archives version |
| `POST /recipes/{id}/expand` | — | Convert Direct → Granular; provides target nutrition |
| `GET /recipes/{id}` | — | Returns full recipe + standard serving info + computed/direct nutrition |
| `POST /food-entries` | `JSON` | Log food: accepts `recipe_id`, `serving_multiplier`, optional `nutrition_override` |
| `GET /food-entries/{id}/preview` | — | Preview final nutrition for given portion and overrides |

> 📡 All endpoints include standard serving metadata to enable accurate portion calculation in the frontend.
> 

---

## 8. UI/UX Specifications

### 8.1 Recipe Editor

- Toggle between **Granular** and **Direct** modes
- Visual badges: `🧂 Granular`, `📊 Direct`, `🤖 AI-Suggested`, `✅ Verified`
- In Granular mode: real-time nutrition preview as ingredients are edited
- In Direct mode: source attribution (e.g., “User”, “Lab Report”, “Package”)
- One-click conversion buttons with confirmation dialogs

### 8.2 Food Logging Screen

1. **Recipe Selection**: List of saved recipes with type and standard serving
2. **Portion Input**:
    - Primary: Fraction buttons (½, 1, 1½)
    - Secondary: Slider, custom amount input, visual portion guide
3. **Live Preview**:
    
    > “175 g (50% of 350g serving)
    > 
    > 
    > *210 kcal • 6.0g Protein • 32.5g Carbs”*
    > 
4. **Optional Override**: “Adjust final values” toggle

### 8.3 Transparency Features

- Tap any nutrient value to trace its origin (e.g., *“Carbs: 32.5g = 0.5 × (65g from recipe)”*)
- “Show ingredients” link for Direct recipes that were flattened
- “Revert to computed” option for overridden entries

---

## 9. Operational Considerations

### 9.1 Performance

- **Nutrition computation** is cached per-recipe (invalidated on edit).
- **Ingredient search** uses trigram indexing for fast fuzzy matching.
- **Image processing** is asynchronous; users receive draft within 3–5 seconds.

### 9.2 Security & Privacy

- User images are encrypted at rest and auto-deleted after 7 days (or after recipe save).
- LLM inference runs in isolated, short-lived environments with no persistent storage.
- Nutrition overrides and custom ingredients are never exposed in public recipe sharing.

### 9.3 Monitoring

- Track:
    - Ratio of Granular vs. Direct recipes
    - Flatten/Expand conversion rates
    - Average portion multipliers (identify mis-sized defaults)
    - Override frequency and reasons
- Alert on: FDC sync failures, compute error spikes, LLM latency >5s.

---

## 10. Future Extensions

| Feature | Description |
| --- | --- |
| **Micronutrient Support** | Expand `NutritionProfile` to include vitamins/minerals; toggle visibility |
| **Barcode Scanning** | Scan packaged foods → auto-create Direct recipes from Open Food Facts |
| **Auto-Balance (Expand Mode)** | Suggest ingredient adjustments to match target nutrition |
| **Recipe Serving Size Editor** | Let users redefine standard serving (e.g., “1 serving = 2 cookies”) |
| **Shared Recipe Marketplace** | Curated, moderated public recipes with versioning and ratings |

---

## 11. Appendix

### A. Standard Serving Definitions

| Recipe Type | How Standard Serving Is Determined |
| --- | --- |
| **Granular** | Sum of all ingredient masses in grams (volume ingredients converted via density) |
| **Direct** | User-defined during first log or edit (e.g., “50g”, “1 bar”, “1 cup”) — stored in recipe metadata |

### B. Portion Input Methods Summary

| Method | Use Case | Precision |
| --- | --- | --- |
| Fraction buttons | Quick, common portions (½, 1, 1½) | High (predefined) |
| Slider | Fine-tuned adjustments (e.g., 1.3x) | Medium (0.1-step) |
| Custom amount | Exact weight/volume (e.g., 175g) | Highest |
| Visual aid | Intuitive for non-technical users | Low–Medium |

### C. LLM Prompt and Guidelines

- Outputs *only* recipe structure (name + ingredients with qty/unit) — **never nutrition values**
- Conservative quantity estimates; low confidence for ambiguous items
- Must flag uncertainty (e.g., dressings, garnishes)
- Strict JSON schema enforcement

```jsx
You are a precise food analyst. Given a meal photo, output JSON only:

{
  "name": "Descriptive meal name",
  "ingredients": [
    {
      "name": "ingredient name (generic, e.g., 'chicken breast')",
      "quantity": 150,
      "unit": "g",  // preferred: g, ml, piece; avoid cup/tbsp unless obvious
      "confidence": 0.85  // 0.0–1.0; low if ambiguous
    }
  ]
}

Rules:
- Be conservative: under-estimate quantities if unsure.
- Skip garnishes/dressings unless prominent.
- If meal is unidentifiable, return empty ingredients + low confidence.
- NEVER invent nutrition values.
```

### D. **Sample `NutritionProfile`**

```json
{
  "energy_kcal": 420,
  "protein_g": 12.5,
  "carbs_g": 65.0,
  "fat_g": 10.2   // extensible — included here for completeness
}
```

---