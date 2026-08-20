# Delete Promotion Code

> **Module:** ssi_promotion
>
> **Model:** `promotion_code`
>
> **Menu:** Promotion ‣ Codes
>
> **Actor:** user in group _Codes — User_
>
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**.
- **Record:** Document number is still **/** (not yet generated).
- **Record:** Referrer is set, so the record can be located in the list while its
  document number is still **/**.
- **Access:** User is in group _Codes — User_.

## Flow

1. Open the **Promotion ‣ Codes** menu.
2. Find the record by its **Referrer**, then open it.
3. Click **Action** > **Delete**.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- The record is permanently removed from the system.
