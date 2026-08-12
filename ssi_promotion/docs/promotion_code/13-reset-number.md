# Reset Document Number — Promotion Code

> **Module:** ssi_promotion
>
> **Model:** `promotion_code`
>
> **Menu:** Promotion ‣ Codes
>
> **Actor:** user in group _Codes — Validator_
>
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **Draft**.
- **Config:** An active `sequence.template` exists for this model.
- **Config:** The shipped "Standard" `policy.template` grants `manual_number_ok` for
  state `draft` to group _Codes — Validator_.
- **Access:** User is in group _Codes — Validator_.

## Flow

1. Open the **Promotion ‣ Codes** menu.
2. Open the record whose document number will be reset.
3. Click the **Reset Document Number** button (or edit the number field and change it
   to **/**).
4. Click **OK** on the confirmation dialog (only when the button was used).

## Post-Condition

- Document number returns to **/**.
- The record will receive an automatic number when it transitions to **Open** status,
  according to the sequence template configuration.
