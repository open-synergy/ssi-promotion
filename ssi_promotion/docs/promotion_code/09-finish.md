# Finish Promotion Code

> **Module:** ssi_promotion
>
> **Model:** `promotion_code`
>
> **Menu:** Promotion ‣ Codes
>
> **Actor:** user in group _Codes — User_
>
> **State:** `open` → `done`
>
> **Requires:** `05-approve`

## Pre-Condition

- **Record:** Status is **Open**.
- **Config:** The shipped "Standard" `policy.template` for this model grants `done_ok`
  for state `open` to group _Codes — User_.
- **Access:** User is in group _Codes — User_.

## Flow

1. Open the **Promotion ‣ Codes** menu.
2. Open the record to finish.
3. Click the **Done** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- Status changes to **Done**.
