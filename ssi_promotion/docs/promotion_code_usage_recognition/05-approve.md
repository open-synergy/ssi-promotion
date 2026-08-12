# Approve Promotion Code Usage Recognition

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage_recognition`
>
> **Menu:** Promotion ‣ Usage Recognitions
>
> **Actor:** approver on the pending approval level (drawn from group _Usage
> Recognitions — Validator_)
>
> **State:** `confirm` → `done`
>
> **Requires:** `04-confirm`

## Pre-Condition

- **Record:** Status is **Waiting for Approval**.
- **Config:** An active `policy.template` grants `approve_ok` to the actor while they
  are registered as an active approver on the record.
- **Config:** An active `sequence.template` exists for this model — required for the
  document number that is generated automatically once this document reaches Done.
- **Access:** User is registered as an approver on the approval level that is currently
  **pending**.

## Flow

1. Open the **Promotion ‣ Usage Recognitions** menu.
2. Open the record to approve.
3. Click the **Approve** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- If there are still pending approval levels, status remains **Waiting for Approval**
  and the next level becomes pending.
- If all approval levels are fulfilled, this document is automatically finished: status
  changes straight to **Done**, its accounting entry (`account.move`) is created and
  posted, and its Recognition Lines are generated. There is no separate manual "Done"
  step — the transition happens as soon as the last approval level is fulfilled.
