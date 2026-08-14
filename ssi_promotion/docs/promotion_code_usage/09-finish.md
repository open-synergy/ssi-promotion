# Finish Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** user in group _Usages — User_
>
> **State:** `open` → `done`
>
> **Requires:** `05-approve`

## Pre-Condition

- **Record:** Status is **Open**.
- **Config:** The shipped "Standard" `policy.template` for this model grants `done_ok`
  for state `open` to group _Usages — User_.
- **Access:** User is in group _Usages — User_.

## Flow

1. Open the **Promotion ‣ Usages** menu.
2. Open the record to finish.
3. Click the **Done** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Done**.
