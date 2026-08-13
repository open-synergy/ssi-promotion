# Cancel Promotion Code

> **Module:** ssi_promotion
>
> **Model:** `promotion_code`
>
> **Menu:** Promotion ‣ Codes
>
> **Actor:** user in group _Codes — Validator_
>
> **State:** `draft` | `confirm` | `open` → `cancel`
>
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**, **Waiting for Approval**, or **Open**.
- **Config:** The shipped "Standard" `policy.template` grants `cancel_ok` for that state
  to group _Codes — Validator_.
- **Access:** User is in group _Codes — Validator_.

## Flow

1. Open the **Promotion ‣ Codes** menu.
2. Open the record to cancel.
3. Click the **Cancel** button.
4. In the wizard that appears, select the **Cancellation Reason**.
5. Click **Confirm**.
6. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Cancelled**.
