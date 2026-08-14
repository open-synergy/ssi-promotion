# Create Promotion Code

> **Module:** ssi_promotion_operating_unit
>
> **Extends:** ssi_promotion — model `promotion_code`, aksi `01-create`

## Additional Fields

When this module is installed, the create form gains one additional field, visible only
to users in the **Multiple Operating Unit** group
(`operating_unit.group_multi_operating_unit`):

- **Operating Unit**: The operating unit this promotion code belongs to. Not required.
  Automatically filled from the current user's default operating unit. Change if needed.

## Modified — Record Visibility

- The **Promotion ‣ Codes** list is filtered by operating unit (record rule). A user
  only sees promotion code records whose Operating Unit is one of the operating units
  assigned to them. This is not a Flow step.
