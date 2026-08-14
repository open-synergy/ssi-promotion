# Create Promotion Code Usage

> **Module:** ssi_promotion_operating_unit
>
> **Extends:** ssi_promotion — model `promotion_code_usage`, aksi `01-create`

## Additional Fields

When this module is installed, the create form gains one additional field, visible only
to users in the **Multiple Operating Unit** group
(`operating_unit.group_multi_operating_unit`):

- **Operating Unit**: The operating unit this promotion code usage belongs to. Not
  required. Automatically filled from the current user's default operating unit. Change
  if needed.

## Modified — Record Visibility

- The **Promotion ‣ Usages** list is filtered by operating unit (record rule). A user
  only sees promotion code usage records whose Operating Unit is one of the operating
  units assigned to them. This is not a Flow step.
