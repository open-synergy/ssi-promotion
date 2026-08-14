# Create Promotion Code

> **Module:** ssi_promotion
>
> **Model:** `promotion_code`
>
> **Menu:** Promotion ‣ Codes
>
> **Actor:** user in group _Codes — User_
>
> **State:** `—` → `draft`

## Pre-Condition

- **Data:** An existing `promotion_type` to select as this code's Promotion Type.
- **Access:** User is in group _Codes — User_.

## Flow

1. Open the **Promotion ‣ Codes** menu.
2. Click the **New** button. **(14.0: "Create")**
3. Fill in the required fields:
   - **Voucher Code** _(required)_: Enter the code the customer will redeem to use this
     promotion. Must be unique across all promotion codes.
   - **Promotion Type** _(required)_: Select the `promotion_type` that determines the
     discount rule, usage limit, validity period, and accounting entry configuration for
     this code.
   - **Referrer**: Optional. Select the partner this code is issued for as a referrer.
   - **Date Start**: Defaults to today. Change if needed.
   - **Date End**: Automatically filled if **Promotion Type** has a validity period,
     computed from **Date Start**. Left empty otherwise.
4. Open the **Discount & Usage** tab to review the values automatically filled from
   **Promotion Type**:
   - **Discount Type**: Automatically filled from **Promotion Type**.
   - **Discount Amount**: Automatically filled from **Promotion Type**. Shown only when
     **Discount Type** is Fixed. Change if needed.
   - **Discount Percentage (%)**: Automatically filled from **Promotion Type**. Shown
     only when **Discount Type** is Percentage. Change if needed.
   - **Usage Limit**: Automatically filled from **Promotion Type**. Change if needed. 0
     means unlimited.
5. Click **Save**.

## Post-Condition

- A new record is created in **Draft** status.
