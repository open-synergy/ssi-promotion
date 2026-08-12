# Confirm Promotion Code Usage Recognition

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage_recognition`
>
> **Menu:** Promotion ‣ Usage Recognitions
>
> **Actor:** user in group _Usage Recognitions — User_
>
> **State:** `draft` → `confirm`
>
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**.
- **Config:** An active `policy.template` for this model grants `confirm_ok` for state
  `draft` to group _Usage Recognitions — User_.
- **Config:** An active `approval.template` for this model matches this record, with
  approvers drawn from group _Usage Recognitions — Validator_.
- **Access:** User is in group _Usage Recognitions — User_.

## Flow

1. Open the **Promotion ‣ Usage Recognitions** menu.
2. Open the record to confirm.
3. Click the **Confirm** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Waiting for Approval**.
- Approval records are created for each approver level defined by the approval template.
