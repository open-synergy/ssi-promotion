# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# HttpSavepointCase -- NOT HttpCase. In 14.0, plain HttpCase does not set
# up ``cls.env`` in ``setUpClass`` (see odoo-development-ui-test skill,
# structure-and-runner.md "Base class").
from odoo.tests import HttpSavepointCase, tagged


@tagged("post_install", "-at_install")
class TestUiPromotionCodeUsageRecognition(HttpSavepointCase):
    """Tour tests for the ``promotion_code_usage_recognition`` work
    instructions.
    """

    @classmethod
    def setUpClass(cls):
        """Create one Open, Deferred usage and one recognition fixture
        per tour, each already in the state its own IK Pre-Condition
        requires.

        Every fixture is owned by ``admin`` (``user_id``) since the
        tours run as ``admin`` and the model's own record rule
        (``promotion_code_usage_recognition_internal_user_rule``) is
        scoped to ``user_id == user.id`` -- without this, ``admin``'s
        tour session would see an empty list.
        """
        super().setUpClass()
        cls.admin = cls.env.ref("base.user_admin")
        account_type_income = cls.env.ref("account.data_account_type_revenue")
        account_type_asset = cls.env.ref("account.data_account_type_current_assets")
        income_account = cls.env["account.account"].create(
            {
                "code": "TOURPCUR-INC",
                "name": "TOUR PCUR Income",
                "user_type_id": account_type_income.id,
            }
        )
        deferred_account = cls.env["account.account"].create(
            {
                "code": "TOURPCUR-DEF",
                "name": "TOUR PCUR Deferred",
                "user_type_id": account_type_asset.id,
            }
        )
        journal = cls.env["account.journal"].create(
            {
                "name": "TOUR PCUR Journal",
                "code": "TPCUR",
                "type": "sale",
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        product = cls.env["product.product"].create(
            {
                "name": "TOUR PCUR Product",
                "type": "service",
                "property_account_income_id": income_account.id,
            }
        )
        promotion_type = cls.env["promotion_type"].create(
            {
                "name": "TOUR PCUR Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 1000.0,
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
                "voucher_code": "TOUR-PCUR-CODE",
                "type_id": promotion_type.id,
            }
        )
        cls._run_workflow(code)
        customer = cls.env["res.partner"].create({"name": "TOUR PCUR Customer"})
        cls.usage = cls.env["promotion_code_usage"].create(
            {
                "name": "TOUR-PCUR-USAGE",
                "promotion_code_id": code.id,
                "partner_id": customer.id,
                "user_id": cls.admin.id,
                "deferred_account_id": deferred_account.id,
                "recognition_journal_id": journal.id,
            }
        )
        cls._run_workflow(cls.usage)

        # IK Pre-Condition of 02-edit / 03-delete / 04-confirm / 10-cancel:
        # Status is Draft.
        cls.recognition_edit = cls._create_recognition("TOUR-PCUR-EDIT")
        # Delete requires the document number to still be "/" -- do NOT
        # give this one an explicit name (see docs/.../03-delete.md).
        cls.recognition_delete = cls._create_recognition(False)
        cls.recognition_confirm = cls._create_recognition("TOUR-PCUR-CONFIRM")
        cls.recognition_cancel = cls._create_recognition("TOUR-PCUR-CANCEL")

        # IK Pre-Condition of 05-approve: Status is Waiting for Approval.
        cls.recognition_approve = cls._create_recognition("TOUR-PCUR-APPROVE")
        cls.recognition_approve.with_user(cls.admin).action_confirm()

        # IK Pre-Condition of 10-cancel: a Cancellation Reason must exist
        # to be picked in the wizard.
        cls.env["base.cancel_reason"].create({"name": "TOUR Cancel Reason"})

    @classmethod
    def _create_recognition(cls, name):
        """Create one draft recognition fixture against ``cls.usage``.

        :param name: document number to assign explicitly (skipping
            the default ``/``), or a falsy value to keep ``/``
        :return: the created ``promotion_code_usage_recognition``
            record
        """
        vals = {
            "usage_id": cls.usage.id,
            "date": cls.usage.date,
            "amount": cls.usage.amount_deferred,
            "journal_id": cls.usage.recognition_journal_id.id,
            "user_id": cls.admin.id,
        }
        if name:
            vals["name"] = name
        return cls.env["promotion_code_usage_recognition"].create(vals)

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

    def test_create(self):
        """Run the create tour for ``promotion_code_usage_recognition``.

        IK: docs/promotion_code_usage_recognition/01-create.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_usage_recognition_create",
            login="admin",
        )

    def test_edit(self):
        """Run the edit tour for ``promotion_code_usage_recognition``.

        IK: docs/promotion_code_usage_recognition/02-edit.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_usage_recognition_edit",
            login="admin",
        )

    def test_delete(self):
        """Run the delete tour for ``promotion_code_usage_recognition``.

        IK: docs/promotion_code_usage_recognition/03-delete.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_usage_recognition_delete",
            login="admin",
        )

    def test_confirm(self):
        """Run the confirm tour for ``promotion_code_usage_recognition``.

        IK: docs/promotion_code_usage_recognition/04-confirm.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_usage_recognition_confirm",
            login="admin",
        )

    def test_approve(self):
        """Run the approve tour for ``promotion_code_usage_recognition``.

        IK: docs/promotion_code_usage_recognition/05-approve.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_usage_recognition_approve",
            login="admin",
        )

    def test_cancel(self):
        """Run the cancel tour for ``promotion_code_usage_recognition``.

        IK: docs/promotion_code_usage_recognition/10-cancel.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_usage_recognition_cancel",
            login="admin",
        )
