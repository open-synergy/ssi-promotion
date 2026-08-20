# Reopen Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** system (`base.automation` record `promotion_code_usage_done_2_open`, no
> user action) — in practice triggered by the user who cancels one of this usage's Done
> `promotion_code_usage_recognition` documents (see
> `docs/promotion_code_usage_recognition/10-cancel.md`)
>
> **State:** `done` → `open`
>
> **Requires:** `09-finish`

## Pre-Condition

- **Record:** Status is **Done**.
- **Record:** **Recognition State** is **Not Applicable** or **Recognized** — this usage
  had nothing left to release.

## Flow

This transition is triggered automatically by the system. No user action is performed on
this record itself.

The system automatically changes status back to **Open** when this usage's own
**Recognition State** drops back to **Pending** or **Partially Recognized** — that is,
when a Done `promotion_code_usage_recognition` document against this usage is cancelled
(see `docs/promotion_code_usage_recognition/10-cancel.md`) and **Amount Recognized** no
longer reaches **Amount To Recognize**. The usage reopens because it once again has a
deferred side waiting to be released.

## Post-Condition

- Status returns to **Open**.
