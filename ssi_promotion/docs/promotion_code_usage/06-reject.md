# Reject Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** approver on the pending approval level (drawn from group _Usages —
> Validator_)
>
> **State:** `confirm` → `reject`
>
> **Requires:** `04-confirm`

## Pre-Condition

- **Record:** Status is **Waiting for Approval**.
- **Config:** The shipped "Standard" `policy.template` grants `reject_ok` to the actor
  while they are registered as an active approver on the record.
- **Access:** User is registered as an approver on the approval level that is currently
  pending.

## Flow

1. Open the **Promotion ‣ Usages** menu.
2. Open the record to reject.
3. Click the **Reject** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Rejected**.
