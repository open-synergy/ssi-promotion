# Approve Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** approver on the pending approval level (drawn from group _Usages —
> Validator_)
>
> **State:** `confirm` → `open`
>
> **Requires:** `04-confirm`

## Pre-Condition

- **Record:** Status is **Waiting for Approval**.
- **Config:** The shipped "Standard" `policy.template` grants `approve_ok` to the actor
  while they are registered as an active approver on the record.
- **Config:** The Promotion Type of this usage's own **Promotion Code** has a complete
  credit note configuration (Credit Note Journal and Credit Note Product) — required for
  the customer credit note created automatically once this document reaches Open.
- **Record:** Every row on the **Allocation** tab, if any, targets a posted,
  reconcilable, not-yet-fully-reconciled, company-currency **Journal Item** whose own
  partner and account match the row's own **Source** (the voucher user for **Voucher
  User**, the promotion code's own referrer for **Referrer** — which also requires the
  promotion code to actually have a referrer). Opening is rejected otherwise.
- **Access:** User is registered as an approver on the approval level that is currently
  **pending**.

## Flow

1. Open the **Promotion ‣ Usages** menu.
2. Open the record to approve.
3. Click the **Approve** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- If there are still pending approval levels, status remains **Waiting for Approval**
  and the next level becomes pending.
- If all approval levels are fulfilled, this document is automatically opened: status
  changes straight to **Open**. There is no separate manual "Start" step — the
  transition happens as soon as the last approval level is fulfilled. A customer credit
  note is created and posted for **Voucher User** at the same time (and a referrer
  credit note as well, if **Promotion Code** has a referrer), so **Customer Credit
  Note** already shows status **Posted** and its own receivable journal item is stored
  on this document. Each row on the **Allocation** tab is then reconciled against its
  own **Source**'s credit note, in **Sequence** order, until that credit note runs out
  of residual — rows reached afterwards keep an empty **Partial Reconcile**.
