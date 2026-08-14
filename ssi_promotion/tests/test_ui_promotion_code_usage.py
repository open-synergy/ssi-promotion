# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# HttpSavepointCase -- NOT HttpCase. In 14.0, plain HttpCase does not set
# up ``cls.env`` in ``setUpClass`` (see odoo-development-ui-test skill,
# structure-and-runner.md "Base class").
from odoo.tests import HttpSavepointCase, tagged


@tagged("post_install", "-at_install")
class TestUiPromotionCodeUsage(HttpSavepointCase):
    """Tour tests for the ``promotion_code_usage`` work instructions,
    plus the "Create Due Recognition" and "Apply Promotion Code"
    wizards whose own work instructions live under
    ``docs/promotion_code_usage/`` since each one creates
    ``promotion_code_usage`` records rather than standing on its own.
    """

    @classmethod
    def setUpClass(cls):
        """Create every ``promotion_code_usage`` fixture the tours
        need, each already in the state its own IK Pre-Condition
        requires.

        Every fixture is owned by ``admin`` (``user_id``) since the
        tours run as ``admin`` and the model's own record rule
        (``promotion_code_usage_internal_user_rule``) is scoped to
        ``user_id == user.id`` -- without this, ``admin``'s tour
        session would see an empty list.
        """
        super().setUpClass()
        cls.admin = cls.env.ref("base.user_admin")

        # ── Fixtures for the "Create Due Recognition" wizard tour
        # (docs/promotion_code_usage/15-create-due-recognition.md).
        account_type_income = cls.env.ref("account.data_account_type_revenue")
        account_type_asset = cls.env.ref("account.data_account_type_current_assets")
        income_account = cls.env["account.account"].create(
            {
                "code": "TOURCDPR-INC",
                "name": "TOUR CDPR Income",
                "user_type_id": account_type_income.id,
            }
        )
        deferred_account = cls.env["account.account"].create(
            {
                "code": "TOURCDPR-DEF",
                "name": "TOUR CDPR Deferred",
                "user_type_id": account_type_asset.id,
            }
        )
        journal = cls.env["account.journal"].create(
            {
                "name": "TOUR CDPR Journal",
                "code": "TCDPR",
                "type": "sale",
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        product = cls.env["product.product"].create(
            {
                "name": "TOUR CDPR Product",
                "type": "service",
                "property_account_income_id": income_account.id,
            }
        )
        promotion_type = cls.env["promotion_type"].create(
            {
                "name": "TOUR CDPR Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 500.0,
                "journal_id": journal.id,
                "product_id": product.id,
                "account_id": income_account.id,
                "recognition_method": "deferred",
                "deferred_account_id": deferred_account.id,
                "recognition_journal_id": journal.id,
            }
        )
        code = cls.env["promotion_code"].create(
            {
                "voucher_code": "TOUR-CDPR-CODE",
                "type_id": promotion_type.id,
            }
        )
        cls._run_workflow(code)
        customer = cls.env["res.partner"].create({"name": "TOUR CDPR Customer"})
        cls.usage = cls.env["promotion_code_usage"].create(
            {
                "name": "TOUR-CDPR-USAGE",
                "promotion_code_id": code.id,
                "partner_id": customer.id,
                "user_id": cls.admin.id,
                "deferred_account_id": deferred_account.id,
                "recognition_journal_id": journal.id,
            }
        )
        # Date and Recognition Date both default to today, so the usage
        # is already due for recognition as of the wizard's own default
        # Date (also today) -- no explicit date override needed.
        cls._run_workflow(cls.usage)

        # ── Fixtures for the promotion_code_usage CRUD / workflow
        # tours (docs/promotion_code_usage/01-create.md through
        # 14-restart-approval.md).
        pcu_income_account = cls.env["account.account"].create(
            {
                "code": "TOURPCUW-INC",
                "name": "TOUR PCUW Income",
                "user_type_id": account_type_income.id,
            }
        )
        pcu_journal = cls.env["account.journal"].create(
            {
                "name": "TOUR PCUW Journal",
                "code": "TPCUW",
                "type": "sale",
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        pcu_product = cls.env["product.product"].create(
            {
                "name": "TOUR PCUW Product",
                "type": "service",
                "property_account_income_id": pcu_income_account.id,
            }
        )
        # Allowed Reference Models must list account.move: the
        # 01-create/02-edit tours set Reference Document to a posted
        # account.move so they can exercise the "Populate Allocation"
        # inline action (mixin.promotion_object,
        # open-synergy/ssi-promotion#30) -- without it, saving the
        # usage with that Reference Document would fail
        # ``_check_document_reference_model``.
        account_move_model = cls.env["ir.model"].search(
            [("model", "=", "account.move")], limit=1
        )
        cls.promotion_type_pcu = cls.env["promotion_type"].create(
            {
                "name": "TOUR PCUW Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 250.0,
                "journal_id": pcu_journal.id,
                "product_id": pcu_product.id,
                "account_id": pcu_income_account.id,
                "allowed_model_ids": [(6, 0, account_move_model.ids)],
            }
        )

        # ``Promotion Code`` fixture selected by hand in the 01-create
        # tour -- must be Open (the field's own domain), and its own
        # document number is overwritten to a fixed, typeable string
        # since the sequence-generated one is not predictable at
        # test-authoring time.
        cls.code_pcu = cls.env["promotion_code"].create(
            {
                "voucher_code": "TOUR-PCU-CODE",
                "type_id": cls.promotion_type_pcu.id,
                "user_id": cls.admin.id,
            }
        )
        cls._run_workflow(cls.code_pcu)
        cls.code_pcu.sudo().write({"name": "TOUR-PCU-CODE"})

        cls.customer_pcu = cls.env["res.partner"].create(
            {"name": "TOUR PCU Create Customer"}
        )

        # Fixture for the Allocation tab step of the 01-create/02-edit
        # tours: a posted receivable invoice for cls.customer_pcu,
        # given a fixed document number since the sequence-generated
        # one is not predictable at test-authoring time (same
        # rationale as cls.code_pcu's own number override below). The
        # tours pick this invoice as the usage's own Reference
        # Document, then click "Populate Allocation" -- the auto-
        # created receivable term line's own 'name'/'product_id' are
        # both empty, so its own display name resolves to just the
        # move's own number (account.move.line name_get,
        # account_move.py), which is what the tour looks for in the
        # resulting allocation row.
        alloc_invoice = cls.env["account.move"].create(
            {
                "name": "TOUR-PCU-ALLOC-INV",
                "move_type": "out_invoice",
                "partner_id": cls.customer_pcu.id,
                "journal_id": pcu_journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": pcu_product.id,
                            "quantity": 1,
                            "price_unit": 1000000.0,
                            "name": "TOUR PCU Allocation Invoice Line",
                            "account_id": pcu_income_account.id,
                        },
                    )
                ],
            }
        )
        alloc_invoice.action_post()
        cls.move_line_pcu = alloc_invoice.line_ids.filtered(
            lambda line: line.account_id.internal_type == "receivable"
        )

        # IK Pre-Condition of 02-edit / 04-confirm: Status is Draft.
        cls.usage_edit = cls._create_usage("TOUR-PCU-EDIT")
        # IK Pre-Condition of 03-delete: Status is Draft and the
        # document number is still "/" -- do NOT give this one an
        # explicit name (see docs/promotion_code_usage/03-delete.md).
        cls.usage_delete = cls._create_usage(False)
        cls.usage_confirm = cls._create_usage("TOUR-PCU-CONFIRM")

        # IK Pre-Condition of 05-approve / 06-reject: Status is
        # Waiting for Approval.
        #
        # ``invalidate_cache()`` after each ``action_confirm()`` is
        # required, not defensive: reading ``confirm_ok`` inside
        # ``action_confirm()``'s own pre-check computes the *whole*
        # ``mixin.policy`` field group at once (``confirm_ok``,
        # ``approve_ok``, ``reject_ok``, ...) while state is still
        # "draft", and that stale group stays cached across the
        # ``write()`` that moves state to "confirm" -- ``_compute_policy``
        # only depends on ``policy_template_id``, not ``state``. Without
        # the refresh, the tour's own read of ``approve_ok``/
        # ``reject_ok`` can return the pre-confirm ``False`` and hide
        # the button (jebakan T-04, skill odoo-development-unit-test,
        # test-traps.md).
        cls.usage_approve = cls._create_usage("TOUR-PCU-APPROVE")
        cls.usage_approve.with_user(cls.admin).action_confirm()
        cls.usage_approve.invalidate_cache()

        cls.usage_reject = cls._create_usage("TOUR-PCU-REJECT")
        cls.usage_reject.with_user(cls.admin).action_confirm()
        cls.usage_reject.invalidate_cache()

        # IK Pre-Condition of 09-finish: Status is Open.
        cls.usage_finish = cls._create_usage("TOUR-PCU-FINISH")
        cls._run_workflow(cls.usage_finish)

        # IK Pre-Condition of 10-cancel: Status is Draft (cancel_ok
        # also allows Waiting for Approval and Open, but Draft is the
        # simplest fixture to prepare).
        cls.usage_cancel = cls._create_usage("TOUR-PCU-CANCEL")

        # IK Pre-Condition of 12-restart: Status is Cancelled.
        #
        # Same cache-staleness hazard as above (jebakan T-04):
        # ``action_cancel()``'s pre-check reads ``cancel_ok``, caching
        # ``restart_ok`` as ``False`` while state is still "draft" --
        # stale after the write to "cancel" unless refreshed.
        cls.usage_restart = cls._create_usage("TOUR-PCU-RESTART")
        cls.usage_restart.with_user(cls.admin).action_cancel()
        cls.usage_restart.invalidate_cache()

        # IK Pre-Condition of 13-reset-number: Status is Draft, with a
        # manually-assigned document number to reset back to "/" so
        # the tour can observe the change.
        cls.usage_reset = cls._create_usage("TOUR-PCU-RESET-MANUAL")

        # IK Pre-Condition of 14-restart-approval: Status is Waiting
        # for Approval. The shipped "Standard" policy.template has no
        # row for restart_approval_ok at all (see
        # docs/promotion_code_usage/14-restart-approval.md note), so
        # this test adds one to exercise the button the IK documents --
        # mirroring the shape of the existing rows in
        # policy_template/promotion_code_usage.xml, scoped to this
        # test transaction only.
        # Same cache-staleness hazard as above (jebakan T-04) --
        # ``restart_approval_ok`` belongs to the same computed field
        # group and would otherwise be read stale (cached ``False``
        # from before this ``action_confirm()``'s write to "confirm").
        cls._grant_restart_approval_ok()
        cls.usage_restart_approval = cls._create_usage("TOUR-PCU-REAPPROVAL")
        cls.usage_restart_approval.with_user(cls.admin).action_confirm()
        cls.usage_restart_approval.invalidate_cache()

        # IK Pre-Condition of 10-cancel: a Cancellation Reason must
        # exist to be picked in the wizard. ``global_use`` is required
        # for it to appear in the wizard's radio list -- without it,
        # the reason is only offered on models explicitly linked via
        # ``ir.model.cancel_reason_ids`` (see
        # ssi_transaction_cancel_mixin/models/base_cancel_reason.py).
        cls.env["base.cancel_reason"].create(
            {
                "name": "TOUR PCU Cancel Reason",
                "code": "TOURPCU",
                "global_use": True,
            }
        )

        # ── Fixtures for the "Apply Promotion Code" wizard tour
        # (docs/promotion_code_usage/16-apply-promotion-code.md), run
        # from a posted customer invoice's own Action (gear) menu --
        # apply_promotion_code_action's own binding_model_id.
        apc_journal = cls.env["account.journal"].create(
            {
                "name": "TOUR APC Journal",
                "code": "TAPC",
                "type": "sale",
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        apc_product = cls.env["product.product"].create(
            {
                "name": "TOUR APC Product",
                "type": "service",
                "property_account_income_id": pcu_income_account.id,
            }
        )
        cls.promotion_type_apc = cls.env["promotion_type"].create(
            {
                "name": "TOUR APC Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 250.0,
                "journal_id": apc_journal.id,
                "product_id": apc_product.id,
                "account_id": pcu_income_account.id,
                "allowed_model_ids": [(6, 0, account_move_model.ids)],
            }
        )
        cls.code_apc = cls.env["promotion_code"].create(
            {
                "voucher_code": "TOUR-APC-CODE",
                "type_id": cls.promotion_type_apc.id,
                "user_id": cls.admin.id,
            }
        )
        cls._run_workflow(cls.code_apc)
        cls.code_apc.sudo().write({"name": "TOUR-APC-CODE"})

        cls.customer_apc = cls.env["res.partner"].create({"name": "TOUR APC Customer"})
        cls.invoice_apc = cls.env["account.move"].create(
            {
                "name": "TOUR-APC-INVOICE",
                "move_type": "out_invoice",
                "partner_id": cls.customer_apc.id,
                "journal_id": apc_journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": apc_product.id,
                            "quantity": 1,
                            "price_unit": 1000000.0,
                            "name": "TOUR APC Invoice Line",
                            "account_id": pcu_income_account.id,
                        },
                    )
                ],
            }
        )
        cls.invoice_apc.action_post()

    @classmethod
    def _create_usage(cls, name):
        """Create one draft ``promotion_code_usage`` fixture against
        ``cls.code_pcu``.

        :param name: document number to assign explicitly (skipping
            the default ``/``), or a falsy value to keep ``/``
        :return: the created ``promotion_code_usage`` record
        """
        vals = {
            "promotion_code_id": cls.code_pcu.id,
            "partner_id": cls.customer_pcu.id,
            "user_id": cls.admin.id,
        }
        if name:
            vals["name"] = name
        return cls.env["promotion_code_usage"].create(vals)

    @classmethod
    def _run_workflow(cls, record):
        """Confirm then approve ``record`` as ``admin``, refreshing the
        cached policy fields in between.

        :param record: the recordset to confirm and approve
        :return: nothing
        """
        record.with_user(cls.admin).action_confirm()
        record.invalidate_cache()
        record.with_user(cls.admin).action_approve_approval()

    @classmethod
    def _grant_restart_approval_ok(cls):
        """Add a test-only ``policy.template_detail`` row granting
        ``restart_approval_ok`` to group _Usages — Validator_ while in
        state ``confirm``.

        The shipped "Standard" ``policy.template`` for
        ``promotion_code_usage`` does not ship this row (see
        docs/promotion_code_usage/14-restart-approval.md), so without
        it the Restart Approval Process button this IK documents is
        never clickable under the default configuration.

        :return: nothing
        """
        template = cls.env.ref("ssi_promotion.policy_template_promotion_code_usage")
        field = cls.env["ir.model.fields"].search(
            [
                ("model_id.model", "=", "promotion_code_usage"),
                ("name", "=", "restart_approval_ok"),
            ],
            limit=1,
        )
        state_confirm = cls.env["ir.model.fields.selection"].search(
            [
                ("field_id.model_id.model", "=", "promotion_code_usage"),
                ("field_id.name", "=", "state"),
                ("value", "=", "confirm"),
            ],
            limit=1,
        )
        validator_group = cls.env.ref(
            "ssi_promotion.promotion_code_usage_validator_group"
        )
        cls.env["policy.template_detail"].create(
            {
                "template_id": template.id,
                "field_id": field.id,
                "restrict_state": True,
                "state_ids": [(6, 0, state_confirm.ids)],
                "restrict_user": True,
                "computation_method": "use_group",
                "group_ids": [(6, 0, validator_group.ids)],
                "restrict_additional": False,
            }
        )

    def test_create(self):
        """Run the create tour for ``promotion_code_usage``.

        IK: docs/promotion_code_usage/01-create.md
        """
        self.start_tour(
            "/web", "ssi_promotion_promotion_code_usage_create", login="admin"
        )

    def test_edit(self):
        """Run the edit tour for ``promotion_code_usage``.

        IK: docs/promotion_code_usage/02-edit.md
        """
        self.start_tour(
            "/web", "ssi_promotion_promotion_code_usage_edit", login="admin"
        )

    def test_delete(self):
        """Run the delete tour for ``promotion_code_usage``.

        IK: docs/promotion_code_usage/03-delete.md
        """
        self.start_tour(
            "/web", "ssi_promotion_promotion_code_usage_delete", login="admin"
        )

    def test_confirm(self):
        """Run the confirm tour for ``promotion_code_usage``.

        IK: docs/promotion_code_usage/04-confirm.md
        """
        self.start_tour(
            "/web", "ssi_promotion_promotion_code_usage_confirm", login="admin"
        )

    def test_approve(self):
        """Run the approve tour for ``promotion_code_usage``.

        IK: docs/promotion_code_usage/05-approve.md
        """
        self.start_tour(
            "/web", "ssi_promotion_promotion_code_usage_approve", login="admin"
        )

    def test_reject(self):
        """Run the reject tour for ``promotion_code_usage``.

        IK: docs/promotion_code_usage/06-reject.md
        """
        self.start_tour(
            "/web", "ssi_promotion_promotion_code_usage_reject", login="admin"
        )

    def test_finish(self):
        """Run the finish tour for ``promotion_code_usage``.

        IK: docs/promotion_code_usage/09-finish.md
        """
        self.start_tour(
            "/web", "ssi_promotion_promotion_code_usage_finish", login="admin"
        )

    def test_cancel(self):
        """Run the cancel tour for ``promotion_code_usage``.

        IK: docs/promotion_code_usage/10-cancel.md
        """
        self.start_tour(
            "/web", "ssi_promotion_promotion_code_usage_cancel", login="admin"
        )

    def test_restart(self):
        """Run the restart tour for ``promotion_code_usage``.

        IK: docs/promotion_code_usage/12-restart.md
        """
        self.start_tour(
            "/web", "ssi_promotion_promotion_code_usage_restart", login="admin"
        )

    def test_reset_number(self):
        """Run the reset document number tour for
        ``promotion_code_usage``.

        IK: docs/promotion_code_usage/13-reset-number.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_usage_reset_number",
            login="admin",
        )

    def test_restart_approval(self):
        """Run the restart approval process tour for
        ``promotion_code_usage``.

        IK: docs/promotion_code_usage/14-restart-approval.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_usage_restart_approval",
            login="admin",
        )

    def test_create_due_recognition(self):
        """Run the "Create Due Recognition" tour.

        IK: docs/promotion_code_usage/15-create-due-recognition.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_usage_create_due_recognition",
            login="admin",
        )

    def test_apply_promotion_code(self):
        """Run the "Apply Promotion Code" tour.

        IK: docs/promotion_code_usage/16-apply-promotion-code.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_usage_apply_promotion_code",
            login="admin",
        )
