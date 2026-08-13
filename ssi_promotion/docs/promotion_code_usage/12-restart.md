# Restart Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** user in group _Usages — Validator_
>
> **State:** `cancel` | `reject` → `draft`
>
> **Requires:** `10-cancel`

## Pre-Condition

- **Record:** Status is **Cancelled** or **Rejected**.
- **Config:** The shipped "Standard" `policy.template` grants `restart_ok` for that
  state to group _Usages — Validator_.
- **Access:** User is in group _Usages — Validator_.

## Flow

1. Open the **Promotion ‣ Usages** menu.
2. Remove the default state filter (Draft / Waiting for Approval / Open) from the
   search bar. The default view only shows those three states, so a Cancelled or
   Rejected document stays hidden until this filter is removed.
3. Open the record to restart.
4. Click the **Restart** button.
5. Click **OK** on the confirmation dialog.

## Post-Condition

- Status returns to **Draft**.
- If this document had already been confirmed, all its approval records are removed and
  its Approval Template is cleared. A later Confirm starts the approval process from the
  beginning.
