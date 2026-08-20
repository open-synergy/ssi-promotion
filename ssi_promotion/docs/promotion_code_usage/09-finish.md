# Finish Promotion Code Usage

> **Module:** ssi_promotion
>
> **Model:** `promotion_code_usage`
>
> **Menu:** Promotion ‣ Usages
>
> **Actor:** system (`base.automation` record `promotion_code_usage_open_2_done`, no
> user action) — in practice triggered by the user who completes this usage's last
> pending `promotion_code_usage_recognition` document (see
> `docs/promotion_code_usage_recognition/05-approve.md`)
>
> **State:** `open` → `done`
>
> **Requires:** `05-approve`

## Pre-Condition

- **Record:** Status is **Open**.
- **Record:** **Recognition State** is **Pending** or **Partially Recognized** — this
  usage still has a deferred side waiting to be released.

## Flow

This transition is triggered automatically by the system. No user action is performed on
this record itself.

The system automatically changes status to **Done** when this usage's own **Recognition
State** becomes **Recognized** — that is, once the last
`promotion_code_usage_recognition` document against this usage reaches Done and **Amount
Recognized** reaches **Amount To Recognize** (see
`docs/promotion_code_usage_recognition/05-approve.md`). At that point every deferred
side of this usage has been fully released, so there is nothing left to wait for and the
usage finishes on its own.

## Post-Condition

- Status changes to **Done**.
