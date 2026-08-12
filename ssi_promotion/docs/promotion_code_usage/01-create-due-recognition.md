# Create Due Promotion Recognition

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage` (wizard `create_due_promotion_recognition`)
>
> **Menu:** Promotion ‣ Create Due Recognition
>
> **Actor:** user in group _Usages — User_

## Pre-Condition

- **Data:** At least one `promotion_code_usage` whose own **Recognition Method** is
  **Deferred**, own **Recognition State** is **Pending**, and own **Recognition Date**
  is on or before the Date selected in the wizard.
- **Access:** User is in group _Usages — User_.

## Flow

1. Open the **Promotion ‣ Create Due Recognition** menu. A wizard opens.
2. The **Date** field is filled with today's date, and the **Usages** field is
   automatically populated with every deferred usage due for recognition as of that
   date. Change **Date** if needed — **Usages** refreshes automatically to match the new
   date. **Usages** cannot be edited manually.
3. Click the **Create Due Recognition** button.

## Post-Condition

- One new `promotion_code_usage_recognition` document, in **Draft** status, is created
  for each usage listed in **Usages**, releasing that usage's own full Amount Deferred.
- The list of newly created Usage Recognition documents is displayed.
