# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# HttpSavepointCase -- NOT HttpCase. In 14.0, plain HttpCase does not set
# up ``cls.env`` in ``setUpClass`` (see odoo-development-ui-test skill,
# structure-and-runner.md "Base class").
from odoo.tests import HttpSavepointCase, tagged


@tagged("post_install", "-at_install")
class TestUiPromotionCodeUsage(HttpSavepointCase):
    """Tour tests for the "Create Due Recognition" wizard, whose work
    instruction lives under ``docs/promotion_code_usage/`` since it is
    triggered from a menu above ``promotion_code_usage``.
    """

    @classmethod
    def setUpClass(cls):
        """Create one Open, Deferred usage due for recognition today.

        Owned by ``admin`` (``user_id``) since the tour runs as
        ``admin`` and the model's own record rule
        (``promotion_code_usage_internal_user_rule``) is scoped to
        ``user_id == user.id``.
        """
        super().setUpClass()
        cls.admin = cls.env.ref("base.user_admin")
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

    def test_create_due_recognition(self):
        """Run the "Create Due Recognition" tour.

        IK: docs/promotion_code_usage/01-create-due-recognition.md
        """
        self.start_tour(
            "/web",
            "ssi_promotion_promotion_code_usage_create_due_recognition",
            login="admin",
        )
