# Delete Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** user in group _Usages — User_
>
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**.
- **Record:** Document number is still **/** (not yet generated).
- **Access:** User is in group _Usages — User_.

## Flow

1. Open the **Promotion ‣ Usages** menu.
2. Open the record to delete.
3. Click **Action** > **Delete**.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- The record is permanently removed from the system.
