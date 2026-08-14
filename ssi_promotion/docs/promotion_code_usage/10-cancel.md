# Cancel Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** user in group _Usages — Validator_
>
> **State:** `draft` | `confirm` | `open` → `cancel`
>
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**, **Waiting for Approval**, or **Open**.
- **Config:** The shipped "Standard" `policy.template` grants `cancel_ok` for that state
  to group _Usages — Validator_.
- **Access:** User is in group _Usages — Validator_.

## Flow

1. Open the **Promotion ‣ Usages** menu.
2. Open the record to cancel.
3. Click the **Cancel** button.
4. In the wizard that appears, select the **Cancellation Reason**.
5. Click **Confirm**.
6. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Cancelled**.
- If any row on the **Allocation** tab was reconciled, that reconciliation is undone
  first — the allocated **Journal Item**'s own residual amount is restored, and the row's
  own **Partial Reconcile** is cleared back to empty.
- If this document had a **Customer Credit Note** and/or **Referrer Credit Note**, those
  credit notes are deleted and both fields, together with their own receivable journal
  item fields, are cleared back to empty.
