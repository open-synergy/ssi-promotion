# Confirm Promotion Code

> **Module:** ssi_promotion
>
> **Model:** `promotion_code`
>
> **Menu:** Promotion ‣ Codes
>
> **Actor:** user in group _Codes — User_
>
> **State:** `draft` → `confirm`
>
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**.
- **Config:** The shipped "Standard" `policy.template` for this model grants
  `confirm_ok` for state `draft` to group _Codes — User_.
- **Config:** The shipped "Standard" `approval.template` for this model matches this
  record, with a single approval level whose approvers are drawn from group _Codes —
  Validator_.
- **Access:** User is in group _Codes — User_.

## Flow

1. Open the **Promotion ‣ Codes** menu.
2. Open the record to confirm.
3. Click the **Confirm** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Waiting for Approval**.
- An approval record is created for the pending approval level, drawn from the matching
  approval template.
