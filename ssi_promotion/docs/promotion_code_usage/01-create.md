# Create Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** user in group _Usages — User_
>
> **State:** `—` → `draft`

## Pre-Condition

- **Data:** An existing `promotion_code` whose own Status is **Open**.
- **Data:** A posted `account.move.line` receivable journal item to allocate —
  reconcilable account, not yet fully reconciled, positive residual, in the company
  currency — if a row is to be added on the **Allocation** tab.
- **Access:** User is in group _Usages — User_.

## Flow

1. Open the **Promotion ‣ Usages** menu.
2. Click the **New** button. **(14.0: "Create")**
3. Fill in the required fields:
   - **Promotion Code** _(required)_: Select the `promotion_code` this usage redeems.
     Only codes whose own Status is **Open** can be selected.
   - **Voucher User** _(required)_: Select the partner who redeemed the promotion code.
   - **Usage Date** _(required)_: Defaults to today. Change if needed.
   - **Reference Document**: Optional. Select the document (e.g. a sale order or an
     invoice) this usage is attached to. The chosen document's model must be listed in
     **Promotion Code**'s own Promotion Type's Allowed Reference Models.
4. Open the **Discount & Credit Note** tab to review the values automatically computed
   once **Promotion Code** is selected:
   - **Discount Amount**: Automatically computed from **Promotion Code**'s own discount
     rule.
   - **Recognition Method**: Automatically filled from **Promotion Code**'s own
     Promotion Type. Change if needed.
   - **Recognition Date**: Automatically filled from **Usage Date**. Change if needed.
   - **Deferred Account** _(required if **Recognition Method** is **Deferred**)_: Shown
     only when **Recognition Method** is **Deferred**. Automatically filled from
     **Promotion Code**'s own Promotion Type once **Promotion Code** is selected. Change
     if needed.
   - **Recognition Journal**: Shown only when **Recognition Method** is **Deferred**.
     Automatically filled from **Promotion Code**'s own Promotion Type once **Promotion
     Code** is selected. Change if needed.
5. Optional: open the **Allocation** tab to list receivable journal items this usage's
   own credit note should be reconciled against once approved. Add a row and fill in:
   - **Source** _(required)_: **Voucher User** or **Referrer** — which of this usage's
     own two credit notes is consumed against this row. Defaults to **Voucher User**.
   - **Journal Item** _(required)_: Select the receivable `account.move.line` to reduce.
   - **Sequence**: Order this row is consumed in among rows sharing the same **Source**.
     Defaults to 5.
6. Click **Save**.

## Post-Condition

- A new record is created in **Draft** status.
