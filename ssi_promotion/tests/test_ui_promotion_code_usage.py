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
        income_usage = cls.env.ref(
            "ssi_product_usage_account_type.product_usage_type_income"
        )

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
                "discount_usage_id": income_usage.id,
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
                "name": "TOUR-CDPR-CODE",
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
                "discount_usage_id": income_usage.id,
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
                "name": "TOUR-PCU-CODE",
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
        #
        # Deliberately posted through its OWN journal, not
        # ``pcu_journal``: ``account.journal.refund_sequence`` groups
        # a journal's own numbering by "is a credit note or not", so a
        # plain ``entry``-type accounting entry (open-synergy/
        # ssi-promotion#38) shares its own numbering bucket with this
        # invoice. Sharing ``pcu_journal`` would make Odoo's own
        # sequence.mixin derive the accounting entry posted for
        # ``cls.usage_finish`` from this invoice's own manually-set,
        # digit-less name (appending "1"), producing a display name
        # that also contains "TOUR-PCU-ALLOC-INV" and confuses the
        # tour's own autocomplete match below.
        pcu_invoice_journal = cls.env["account.journal"].create(
            {
                "name": "TOUR PCUW Invoice Journal",
                "code": "TPCUI",
                "type": "sale",
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        alloc_invoice = cls.env["account.move"].create(
            {
                "name": "TOUR-PCU-ALLOC-INV",
                "move_type": "out_invoice",
                "partner_id": cls.customer_pcu.id,
                "journal_id": pcu_invoice_journal.id,
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

        # ── Fixtures for 09-finish / 17-reopen: both transitions are
        # driven by base.automation off ``recognition_state``, not a
        # button (see docs/promotion_code_usage/09-finish.md and
        # 17-reopen.md) -- so the triggering
        # promotion_code_usage_recognition document is completed (and,
        # for 17-reopen, then cancelled) here in Python, and the tour
        # itself only opens the already-transitioned record and reads
        # its statusbar (odoo-development-ui-test skill,
        # scope-and-boundaries.md §1 rule 6). This needs its own
        # Deferred promotion type -- ``cls.promotion_type_pcu`` stays
        # Immediate since every other tour fixture in this file still
        # depends on it landing straight on Done.
        pcu_deferred_account = cls.env["account.account"].create(
            {
                "code": "TOURPCUW-DEF",
                "name": "TOUR PCUW Deferred",
                "user_type_id": account_type_asset.id,
            }
        )
        promotion_type_pcu_deferred = cls.env["promotion_type"].create(
            {
                "name": "TOUR PCUW Deferred Type",
                "code": "/",
                "discount_usage_id": income_usage.id,
                "discount_type": "fixed",
                "discount_amount": 250.0,
                "journal_id": pcu_journal.id,
                "product_id": pcu_product.id,
                "account_id": pcu_income_account.id,
                "recognition_method": "deferred",
                "deferred_account_id": pcu_deferred_account.id,
                "recognition_journal_id": pcu_journal.id,
            }
        )
        code_pcu_deferred = cls.env["promotion_code"].create(
            {
                "name": "TOUR-PCU-DEF-CODE",
                "type_id": promotion_type_pcu_deferred.id,
                "user_id": cls.admin.id,
            }
        )
        cls._run_workflow(code_pcu_deferred)
        customer_pcu_deferred = cls.env["res.partner"].create(
            {"name": "TOUR PCU Deferred Customer"}
        )

        # IK Pre-Condition of 09-finish: Status is Open, Recognition
        # State is Pending -- reached here, then fully recognized so
        # the usage moves itself to Done without any button on this
        # record.
        cls.usage_finish = cls.env["promotion_code_usage"].create(
            {
                "name": "TOUR-PCU-FINISH",
                "promotion_code_id": code_pcu_deferred.id,
                "partner_id": customer_pcu_deferred.id,
                "user_id": cls.admin.id,
                "deferred_account_id": pcu_deferred_account.id,
                "recognition_journal_id": pcu_journal.id,
            }
        )
        cls._run_workflow(cls.usage_finish)
        recognition_finish = cls.env["promotion_code_usage_recognition"].create(
            {
                "usage_id": cls.usage_finish.id,
                "date": cls.usage_finish.date,
                "amount": cls.usage_finish.amount_to_recognize,
                "journal_id": pcu_journal.id,
                "user_id": cls.admin.id,
            }
        )
        cls._run_workflow(recognition_finish)
        cls.usage_finish.invalidate_cache()
        # Verify the fixture's own Pre-Condition out loud instead of
        # silently relying on the tour to notice it went wrong (issue
        # open-synergy/ssi-promotion#72 ronde-3): reading 'state' here
        # forces the pending 'recognition_completed'/'state' recompute
        # -- and the base.automation it can trigger -- to settle in
        # this fixture's own controlled context, the same rhythm the
        # passing YAML scenario gets for free from its own explicit
        # `refresh: true` reads between steps.
        assert cls.usage_finish.state == "done", (
            "Fixture invariant violated: TOUR-PCU-FINISH should have "
            "moved itself to Done via the "
            "promotion_code_usage_open_2_done base.automation once "
            "its only recognition finished, but its own state still "
            "reads %r." % cls.usage_finish.state
        )

        # IK Pre-Condition of 17-reopen: Status is Done, Recognition
        # State is Recognized -- reached the same way as usage_finish
        # above, then the recognition is cancelled so the usage moves
        # itself back to Open without any button on this record.
        cls.usage_reopen = cls.env["promotion_code_usage"].create(
            {
                "name": "TOUR-PCU-REOPEN",
                "promotion_code_id": code_pcu_deferred.id,
                "partner_id": customer_pcu_deferred.id,
                "user_id": cls.admin.id,
                "deferred_account_id": pcu_deferred_account.id,
                "recognition_journal_id": pcu_journal.id,
            }
        )
        cls._run_workflow(cls.usage_reopen)
        recognition_reopen = cls.env["promotion_code_usage_recognition"].create(
            {
                "usage_id": cls.usage_reopen.id,
                "date": cls.usage_reopen.date,
                "amount": cls.usage_reopen.amount_to_recognize,
                "journal_id": pcu_journal.id,
                "user_id": cls.admin.id,
            }
        )
        cls._run_workflow(recognition_reopen)
        cls.usage_reopen.invalidate_cache()
        # Same rationale as usage_finish's own assert above -- and it
        # also proves the tour below is testing something real: without
        # it, "Status is Open" after the wizard is equally true whether
        # the automation ever fired at all (issue #72 ronde-3 note).
        assert cls.usage_reopen.state == "done", (
            "Fixture invariant violated: TOUR-PCU-REOPEN should have "
            "moved itself to Done via the "
            "promotion_code_usage_open_2_done base.automation once "
            "its only recognition finished, but its own state still "
            "reads %r." % cls.usage_reopen.state
        )
        recognition_reopen_cancel_reason = cls.env["base.cancel_reason"].create(
            {
                "name": "TOUR PCU Recognition Cancel Reason",
                "code": "TOURPCURCXL",
                "global_use": True,
            }
        )
        recognition_reopen.with_user(cls.admin).action_cancel(
            cancel_reason=recognition_reopen_cancel_reason
        )
        cls.usage_reopen.invalidate_cache()
        assert cls.usage_reopen.state == "open", (
            "Fixture invariant violated: TOUR-PCU-REOPEN should have "
            "moved itself back to Open via the "
            "promotion_code_usage_done_2_open base.automation once "
            "its Done recognition was cancelled, but its own state "
            "still reads %r." % cls.usage_reopen.state
        )

        # IK Pre-Condition of 10-cancel: Status is Done, with no
        # Recognitions yet (cancel_ok also allows Draft, Waiting for
        # Approval, and Open, but Done -- the newest allowed state,
        # open-synergy/ssi-promotion#73 -- is the one most easily
        # confused with the disallowed "Done with Recognitions" case,
        # so it is the one this tour exercises). ``cls.code_pcu``'s
        # own promotion type is Immediate (no deferred side), so
        # running it through ``_run_workflow`` alone lands it on Done
        # via the ``promotion_code_usage_open_2_done`` base.automation,
        # the same mechanism ``usage_finish``/``usage_reopen`` rely on
        # above -- without ever creating a
        # ``promotion_code_usage_recognition`` document against it.
        cls.usage_cancel = cls._create_usage("TOUR-PCU-CANCEL")
        cls._run_workflow(cls.usage_cancel)
        cls.usage_cancel.invalidate_cache()
        # Same rationale as usage_finish's own assert above -- and it
        # also proves this usage has no Recognitions of its own, which
        # is exactly the Pre-Condition this tour's Cancel button relies
        # on being granted.
        assert cls.usage_cancel.state == "done", (
            "Fixture invariant violated: TOUR-PCU-CANCEL should have "
            "moved itself to Done via the "
            "promotion_code_usage_open_2_done base.automation once "
            "its Immediate promotion type left it with nothing "
            "deferred to wait for, but its own state still reads "
            "%r." % cls.usage_cancel.state
        )
        assert not cls.usage_cancel.recognition_ids, (
            "Fixture invariant violated: TOUR-PCU-CANCEL should have "
            "no Recognitions of its own -- 10-cancel.md's own "
            "Pre-Condition requires that for cancel_ok to grant Cancel "
            "from Done, but this fixture has %d."
            % len(cls.usage_cancel.recognition_ids)
        )

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
        #
        # ssi_financial_accounting REPLACES core account.menu_finance's
        # own groups_id (menu.xml, "Hide menu"), so the invoice is
        # reached through its own app instead (Financial Accounting >
        # Account Receivable > Invoices, gated by
        # ssi_financial_accounting.invoice_user_group). No group grant
        # is needed here: that module's own security data already adds
        # base.user_admin to invoice_validator_group (implying
        # invoice_user_group) at install time
        # (security/res_groups/invoice.xml).
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
                "discount_usage_id": income_usage.id,
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
                "name": "TOUR-APC-CODE",
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

    def test_reopen(self):
        """Run the reopen tour for ``promotion_code_usage``.

        IK: docs/promotion_code_usage/17-reopen.md
        """
        self.start_tour(
            "/web", "ssi_promotion_promotion_code_usage_reopen", login="admin"
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
