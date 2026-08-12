# Create Promotion Code Usage Recognition

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage_recognition`
>
> **Menu:** Promotion ‣ Usage Recognitions
>
> **Actor:** user in group _Usage Recognitions — User_
>
> **State:** `—` → `draft`

## Pre-Condition

- **Data:** An existing `promotion_code_usage` whose own Status is **Open** and whose
  own **Recognition Method** is **Deferred**.
- **Access:** User is in group _Usage Recognitions — User_.

## Flow

1. Open the **Promotion ‣ Usage Recognitions** menu.
2. Click the **New** button. **(14.0: "Create")**
3. Fill in the required fields:
   - **# Usage** _(required)_: Select the deferred `promotion_code_usage` this document
     releases.
   - **Date** _(required)_: Accounting date of this recognition document. Defaults to
     today. May not be earlier than the usage's own Usage Date.
   - **Amount** _(required)_: Automatically filled from **# Usage**'s own Amount
     Deferred. Change if needed.
   - **Journal** _(required)_: Automatically filled from **# Usage**'s own Recognition
     Journal. Change if needed.
   - **Note**: Free-form note. Optional.
4. Click **Save**.

## Post-Condition

- A new record is created in **Draft** status.
