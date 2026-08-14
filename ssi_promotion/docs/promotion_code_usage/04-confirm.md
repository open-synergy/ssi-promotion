# Confirm Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** user in group _Usages — User_
>
> **State:** `draft` → `confirm`
>
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**.
- **Config:** The shipped "Standard" `policy.template` for this model grants
  `confirm_ok` for state `draft` to group _Usages — User_.
- **Config:** The shipped "Standard" `approval.template` for this model matches this
  record, with approvers drawn from group _Usages — Validator_.
- **Access:** User is in group _Usages — User_.

## Flow

1. Open the **Promotion ‣ Usages** menu.
2. Open the record to confirm.
3. Click the **Confirm** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Waiting for Approval**.
- Approval records are created for each approver level defined by the approval template.
