# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# HttpSavepointCase -- NOT HttpCase. In 14.0, plain HttpCase does not set
# up ``cls.env`` in ``setUpClass`` (see odoo-development-ui-test skill,
# structure-and-runner.md "Base class").
from odoo.tests import HttpSavepointCase, tagged


@tagged("post_install", "-at_install")
class TestUiPromotionCode(HttpSavepointCase):
    """Tour tests for the ``promotion_code`` work instructions."""

    @classmethod
    def setUpClass(cls):
        """Create one ``promotion_type`` and one ``promotion_code``
        fixture per tour, each already in the state its own IK
        Pre-Condition requires.

        Every fixture is owned by ``admin`` (``user_id``) since the
        tours run as ``admin`` and the model's own record rule
        (``promotion_code_internal_user_rule``) is scoped to
        ``user_id == user.id`` -- without this, ``admin``'s tour
        session would see an empty list. This mirrors the same
        prerequisite documented and exercised by
        ``test_data_promotion_code.yaml`` (jebakan T-05, skill
        odoo-development-unit-test).
        """
        super().setUpClass()
        cls.admin = cls.env.ref("base.user_admin")
        cls.promotion_type = cls.env["promotion_type"].create(
            {
                "name": "TOUR PC Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 1000.0,
            }
        )

        # IK Pre-Condition of 02-edit / 04-confirm: Status is Draft.
        cls.code_edit = cls._create_code("TOUR-PC-EDIT")
        # IK Pre-Condition of 03-delete: Status is Draft and the
        # document number is still "/" -- do NOT give this one an
        # explicit name (see docs/promotion_code/03-delete.md).
        cls.code_delete = cls._create_code("TOUR-PC-DELETE")
        cls.code_confirm = cls._create_code("TOUR-PC-CONFIRM")

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
        cls.code_approve = cls._create_code("TOUR-PC-APPROVE")
        cls.code_approve.with_user(cls.admin).action_confirm()
        cls.code_approve.invalidate_cache()

        cls.code_reject = cls._create_code("TOUR-PC-REJECT")
        cls.code_reject.with_user(cls.admin).action_confirm()
        cls.code_reject.invalidate_cache()

        # IK Pre-Condition of 09-finish: Status is Open.
        cls.code_finish = cls._create_code("TOUR-PC-FINISH")
        cls._run_to_open(cls.code_finish)

        # IK Pre-Condition of 10-cancel: Status is Draft (cancel_ok
        # also allows Waiting for Approval and Open, but Draft is the
        # simplest fixture to prepare).
        cls.code_cancel = cls._create_code("TOUR-PC-CANCEL")

        # IK Pre-Condition of 12-restart: Status is Cancelled.
        #
        # Same cache-staleness hazard as above (jebakan T-04):
        # ``action_cancel()``'s pre-check reads ``cancel_ok``, caching
        # ``restart_ok`` as ``False`` while state is still "draft" --
        # stale after the write to "cancel" unless refreshed.
        cls.code_restart = cls._create_code("TOUR-PC-RESTART")
        cls.code_restart.with_user(cls.admin).action_cancel()
        cls.code_restart.invalidate_cache()

        # IK Pre-Condition of 13-reset-number: Status is Draft, with a
        # manually-assigned document number to reset back to "/" so
        # the tour can observe the change.
        cls.code_reset = cls._create_code("TOUR-PC-RESET", name="TOUR-PC-RESET-MANUAL")

        # IK Pre-Condition of 14-restart-approval: Status is Waiting
        # for Approval. The shipped "Standard" policy.template has no
        # row for restart_approval_ok at all (see
        # docs/promotion_code/14-restart-approval.md note), so this
        # test adds one to exercise the button the IK documents --
        # mirroring the shape of the existing rows in
        # policy_template/promotion_code.xml, scoped to this test
        # transaction only.
        # Same cache-staleness hazard as above (jebakan T-04) --
        # ``restart_approval_ok`` belongs to the same computed field
        # group and would otherwise be read stale (cached ``False``
        # from before this ``action_confirm()``'s write to "confirm").
        # Named "REAPPROVAL", not "RESTART-APPROVAL": the latter shares
        # the "TOUR-PC-RESTART" prefix with ``code_restart``'s voucher
        # code above, and the tour's ``:contains(TOUR-PC-RESTART)``
        # trigger for that other tour does a *substring* match -- it
        # would silently open this record instead once both are made
        # visible by the same search filter (see promotion_code_tour.js
        # 12-restart, "Enable the Cancel filter").
        cls._grant_restart_approval_ok()
        cls.code_restart_approval = cls._create_code("TOUR-PC-REAPPROVAL")
        cls.code_restart_approval.with_user(cls.admin).action_confirm()
        cls.code_restart_approval.invalidate_cache()

        # IK Pre-Condition of 10-cancel: a Cancellation Reason must
        # exist to be picked in the wizard. ``global_use`` is required
        # for it to appear in the wizard's radio list -- without it,
        # the reason is only offered on models explicitly linked via
        # ``ir.model.cancel_reason_ids`` (see
        # ssi_transaction_cancel_mixin/models/base_cancel_reason.py).
        cls.env["base.cancel_reason"].create(
            {
                "name": "TOUR PC Cancel Reason",
                "code": "TOURPC",
                "global_use": True,
            }
        )

    @classmethod
    def _create_code(cls, voucher_code, name=False):
        """Create one draft ``promotion_code`` fixture.

        :param voucher_code: value for the unique ``voucher_code``
            field, also used by the tours to locate the row in the
            list view
        :param name: document number to assign explicitly (skipping
            the default ``/``), or a falsy value to keep ``/``
        :return: the created ``promotion_code`` record
        """
        vals = {
            "voucher_code": voucher_code,
            "type_id": cls.promotion_type.id,
            "user_id": cls.admin.id,
        }
        if name:
            vals["name"] = name
        return cls.env["promotion_code"].create(vals)

    @classmethod
    def _run_to_open(cls, record):
        """Confirm then approve ``record`` as ``admin``, refreshing
        the cached policy fields in between, so it reaches state
        Open.

        :param record: the recordset to confirm and approve
        :return: nothing
        """
        record.with_user(cls.admin).action_confirm()
        record.invalidate_cache()
        record.with_user(cls.admin).action_approve_approval()

    @classmethod
    def _grant_restart_approval_ok(cls):
        """Add a test-only ``policy.template_detail`` row granting
        ``restart_approval_ok`` to group _Codes — Validator_ while in
        state ``confirm``.

        The shipped "Standard" ``policy.template`` for
        ``promotion_code`` does not ship this row (see
        docs/promotion_code/14-restart-approval.md), so without it
        the Restart Approval Process button this IK documents is
        never clickable under the default configuration.

        :return: nothing
        """
        template = cls.env.ref("ssi_promotion.policy_template_promotion_code")
        field = cls.env["ir.model.fields"].search(
            [
                ("model_id.model", "=", "promotion_code"),
                ("name", "=", "restart_approval_ok"),
            ],
            limit=1,
        )
        state_confirm = cls.env["ir.model.fields.selection"].search(
            [
                ("field_id.model_id.model", "=", "promotion_code"),
                ("field_id.name", "=", "state"),
                ("value", "=", "confirm"),
            ],
            limit=1,
        )
        validator_group = cls.env.ref("ssi_promotion.promotion_code_validator_group")
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
        """Run the create tour for ``promotion_code``.

        IK: docs/promotion_code/01-create.md
        """
        self.start_tour("/web", "ssi_promotion_promotion_code_create", login="admin")

    def test_edit(self):
        """Run the edit tour for ``promotion_code``.

        IK: docs/promotion_code/02-edit.md
        """
        self.start_tour("/web", "ssi_promotion_promotion_code_edit", login="admin")

    def test_delete(self):
        """Run the delete tour for ``promotion_code``.

        IK: docs/promotion_code/03-delete.md
        """
        self.start_tour("/web", "ssi_promotion_promotion_code_delete", login="admin")

    def test_confirm(self):
        """Run the confirm tour for ``promotion_code``.

        IK: docs/promotion_code/04-confirm.md
        """
        self.start_tour("/web", "ssi_promotion_promotion_code_confirm", login="admin")

    def test_approve(self):
        """Run the approve tour for ``promotion_code``.

        IK: docs/promotion_code/05-approve.md
        """
        self.start_tour("/web", "ssi_promotion_promotion_code_approve", login="admin")

    def test_reject(self):
        """Run the reject tour for ``promotion_code``.

        IK: docs/promotion_code/06-reject.md
        """
        self.start_tour("/web", "ssi_promotion_promotion_code_reject", login="admin")

    def test_finish(self):
        """Run the finish tour for ``promotion_code``.

        IK: docs/promotion_code/09-finish.md
        """
        self.start_tour("/web", "ssi_promotion_promotion_code_finish", login="admin")

    def test_cancel(self):
        """Run the cancel tour for ``promotion_code``.

        IK: docs/promotion_code/10-cancel.md
        """
        self.start_tour("/web", "ssi_promotion_promotion_code_cancel", login="admin")

    def test_restart(self):
        """Run the restart tour for ``promotion_code``.

        IK: docs/promotion_code/12-restart.md
        """
        self.start_tour("/web", "ssi_promotion_promotion_code_restart", login="admin")

    def test_reset_number(self):
        """Run the reset document number tour for ``promotion_code``.

        IK: docs/promotion_code/13-reset-number.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_reset_number",
            login="admin",
        )

    def test_restart_approval(self):
        """Run the restart approval process tour for ``promotion_code``.

        IK: docs/promotion_code/14-restart-approval.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_restart_approval",
            login="admin",
        )
