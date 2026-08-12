# Restart Promotion Code

> **Module:** ssi_promotion
>
> **Model:** `promotion_code`
>
> **Menu:** Promotion ‣ Codes
>
> **Actor:** user in group _Codes — Validator_
>
> **State:** `cancel` | `reject` → `draft`
>
> **Requires:** `10-cancel`

## Pre-Condition

- **Record:** Status is **Cancelled** or **Rejected**.
- **Config:** The shipped "Standard" `policy.template` grants `restart_ok` for that
  state to group _Codes — Validator_.
- **Access:** User is in group _Codes — Validator_.

## Flow

1. Open the **Promotion ‣ Codes** menu.
2. Open the record to restart.
3. Click the **Restart** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- Status returns to **Draft**.
- If this document had already been confirmed, all its approval records are removed and
  its Approval Template is cleared. A later Confirm starts the approval process from the
  beginning.
