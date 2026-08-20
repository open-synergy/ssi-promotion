# Cancel Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** user in group _Usages — Validator_
>
> **State:** `draft` | `confirm` | `open` | `done` → `cancel`
>
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**, **Waiting for Approval**, **Open**, or **Done**.
- **Record:** If Status is **Done**, this usage does not yet have any **Recognitions**.
- **Config:** The shipped "Standard" `policy.template` grants `cancel_ok` for that state
  to group _Usages — Validator_.
- **Access:** User is in group _Usages — Validator_.

## Flow

1. Open the **Promotion ‣ Usages** menu.
2. If the record is **Done**, remove the default state filter (Draft / Waiting for
   Approval / Open) from the search bar — Done documents are hidden by default; Draft,
   Waiting for Approval, and Open documents are already shown.
3. Open the record to cancel.
4. Click the **Cancel** button.
5. In the wizard that appears, select the **Cancellation Reason**.
6. Click **Confirm**.
7. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Cancelled**.
- If any row on the **Allocation** tab was reconciled, that reconciliation is undone
  first — the allocated **Journal Item**'s own residual amount is restored, and the
  row's own **Partial Reconcile** is cleared back to empty.
- If this document had a **Customer Accounting Entry** and/or **Referrer Accounting
  Entry**, those journal entries are deleted and both fields, together with their own
  receivable journal item fields, are cleared back to empty.
- When cancelling from **Done**, this document always has a **Customer Accounting
  Entry** (and, when applicable, a **Referrer Accounting Entry**) at that point — a
  usage only reaches Done after its accounting entries have been posted — so the
  deletion above always happens.
