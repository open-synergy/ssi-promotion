# Apply Promotion Code

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage` (wizard `apply_promotion_code`, action
> `action_apply_promotion_code`)
>
> **Menu:** Financial Accounting ‣ Account Receivable ‣ Invoices ‣ (open an invoice) ‣
> Action ‣ Apply Promotion Code
>
> **Actor:** user in group _Usages — User_ and _Invoice — User_
>
> **State:** `—` → `draft` (new `promotion_code_usage`)

## Pre-Condition

- **Data:** A posted `account.move` (e.g. a customer invoice) with an outstanding
  receivable journal item — reconcilable account, not yet fully reconciled, positive
  residual, in the company currency.
- **Data:** An existing `promotion_code` whose own Status is **Open**, whose own
  Promotion Type's own Allowed Reference Models includes `account.move`.
- **Access:** User is in group _Usages — User_ (`ssi_promotion`) and _Invoice — User_
  (`ssi_financial_accounting`, to reach the invoice from its own menu).

## Flow

1. Open the **Financial Accounting ‣ Account Receivable ‣ Invoices** menu.
2. Open the posted invoice this promotion is being applied to.
3. Click the **Action** (⚙️) button, then **Apply Promotion Code**. A wizard opens.
4. Fill in the wizard:
   - **Promotion Code** _(required)_: Select the `promotion_code` to redeem. Only codes
     whose own Status is **Open** can be selected.
   - **Voucher User**: Automatically filled from the invoice's own customer. Read-only.
   - **Date** _(required)_: Defaults to today. Copied to the new usage's own Usage Date.
5. Click **Apply**.

## Post-Condition

- A new `promotion_code_usage` record is created in **Draft** status, and its own form
  is displayed.
- Its own Reference Document points to the invoice; its own Voucher User matches the
  invoice's own customer; its own Allocations is already filled with the invoice's own
  eligible receivable journal item.
