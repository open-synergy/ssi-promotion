# Edit Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** user in group _Usages — User_
>
> **Requires:** `01-create`
>
> **Inline Actions:** `action_populate_allocation` (Populate Allocation)

## Pre-Condition

- **Record:** Status is **Draft**.
- **Data:** A posted `account.move.line` receivable journal item to allocate —
  reconcilable account, not yet fully reconciled, positive residual, in the company
  currency — if **Populate Allocation** is to be exercised.
- **Access:** User is in group _Usages — User_.

## Flow

1. Open the **Promotion ‣ Usages** menu.
2. Find and open the record to edit.
3. Click the **Edit** button.
4. Change the fields to update — **Promotion Code**, **Voucher User**, **Usage Date**,
   or **Reference Document**.
5. Optional: on the **Allocation** tab, click **Populate Allocation** to fill
   **Allocations** from **Reference Document**'s own outstanding receivable journal
   item(s), skipping any journal item already listed. Only works while **Reference
   Document** is set to a document whose own model supports it (e.g. a posted
   `account.move`); otherwise it fails with an error explaining why. Without it,
   **Allocations** keeps whatever rows are already present.
6. Click **Save**.

## Post-Condition

- The record is updated with the new values.
