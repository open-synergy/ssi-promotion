# Restart Approval Process — Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** user in group _Usages — Validator_
>
> **Requires:** `04-confirm`

## Pre-Condition

- **Record:** Status is **Waiting for Approval**.
- **Config:** An active `policy.template` for this model grants `restart_approval_ok`
  for state `confirm` to the actor's group. See the note below — the shipped "Standard"
  `policy.template` does **not** ship a row for this policy field.
- **Access:** User is in group _Usages — Validator_.

## Flow

1. Open the **Promotion ‣ Usages** menu.
2. Open the record to restart the approval process for.
3. Click the **Restart Approval Process** button.
4. Click **OK** on the confirmation dialog.

## Post-Condition

- All existing approval records for this document are removed.
- New approval records are created from the record's current **Approval Template**,
  restarting the approval process from the first level.
- Status remains **Waiting for Approval**.

> **Note:** the shipped "Standard" `policy.template` for `promotion_code_usage`
> (`policy_template/promotion_code_usage.xml`) does not include a `policy.template_detail`
> row for `restart_approval_ok` at all — unlike `confirm_ok`, `approve_ok`, `reject_ok`,
> `done_ok`, `cancel_ok`, `restart_ok`, and `manual_number_ok`, which all have one.
> Because `_compute_policy` initializes every field in `_get_policy_field()` to `False`
> and only a matching `policy.template_detail` row overrides it, `restart_approval_ok`
> evaluates to **False** for every user under the default configuration, so the
> **Restart Approval Process** button is present in the form (gate G1/G2 both pass at
> the code level — see the class attribute
> `_automatically_insert_restart_approval_button` and `_policy_field_order`) but not
> clickable out of the box. An administrator must add a `policy.template_detail` row for
> `restart_approval_ok` (mirroring the shape of the existing rows) before this button
> becomes usable. This was found while writing this IK and is reported here rather than
> fixed, since shipping that row is a data/behavior change out of scope for this Work
> Instruction.
