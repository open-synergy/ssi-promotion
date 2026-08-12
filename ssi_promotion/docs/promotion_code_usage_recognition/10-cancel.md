# Cancel Promotion Code Usage Recognition

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage_recognition`
>
> **Menu:** Promotion ‣ Usage Recognitions
>
> **Actor:** user in group _Usage Recognitions — Validator_
>
> **State:** `draft` | `confirm` | `done` → `cancel`
>
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**, **Waiting for Approval**, or **Done**.
- **Config:** An active `policy.template` grants `cancel_ok` for that state to group
  _Usage Recognitions — Validator_.
- **Access:** User is in group _Usage Recognitions — Validator_.

## Flow

1. Open the **Promotion ‣ Usage Recognitions** menu.
2. Open the record to cancel.
3. Click the **Cancel** button.
4. In the wizard that appears, select the **Cancellation Reason**.
5. Click **Confirm**.
6. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Cancelled**.
- If this document had already been Done, its accounting entry (`account.move`) is
  deleted and its Recognition Lines are removed.
