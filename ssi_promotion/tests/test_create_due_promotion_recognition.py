# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo_yaml_test import YamlTransactionCase

from odoo import fields
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCreateDuePromotionRecognition(YamlTransactionCase):
    """Scenario tests for ``create_due_promotion_recognition``."""

    def _setup_accounting(self, prefix):
        """Create the income/deferred accounts, journal, and product a
        deferred usage needs.

        :param prefix: short unique code prefix for the created
            ``account.account``/``account.journal`` records
        :return: tuple ``(income_account, deferred_account, journal,
            product)``
        """
        account_type_income = self.env.ref("account.data_account_type_revenue")
        account_type_asset = self.env.ref("account.data_account_type_current_assets")
        income_account = self.env["account.account"].create(
            {
                "code": "%s-INC" % prefix,
                "name": "%s Income" % prefix,
                "user_type_id": account_type_income.id,
            }
        )
        deferred_account = self.env["account.account"].create(
            {
                "code": "%s-DEF" % prefix,
                "name": "%s Deferred" % prefix,
                "user_type_id": account_type_asset.id,
            }
        )
        journal = self.env["account.journal"].create(
            {
                "name": "%s Journal" % prefix,
                "code": prefix,
                "type": "sale",
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        product = self.env["product.product"].create(
            {
                "name": "%s Product" % prefix,
                "type": "service",
                "property_account_income_id": income_account.id,
            }
        )
        return income_account, deferred_account, journal, product

    def _confirm_and_approve(self, record):
        """Run ``action_confirm`` then ``action_approve_approval`` as
        the admin user, refreshing the cached policy fields in
        between.

        :param record: the recordset to confirm and approve
        :return: nothing
        """
        admin = self.env.ref("base.user_admin")
        record.with_user(admin).action_confirm()
        record.invalidate_cache()
        record.with_user(admin).action_approve_approval()

    def test_create_due_promotion_recognition(self):
        """Run the prefill, onchange, and empty-selection scenarios."""
        self.run_yaml_scenario("test_data_create_due_promotion_recognition.yaml")

    def test_action_create_due_recognition_returns_action(self):
        """Assert the action dict and documents the wizard creates.

        Pure Python -- trigger P1 (L-01: an ``action: call`` step in
        YAML discards the return value of the method it calls, so
        the ``ir.actions.act_window`` dict ``action_create_due_
        recognition`` returns cannot be asserted there; L-02: every
        YAML ``asserts`` reaches a dotted-path ``getattr`` on a
        record already sitting in the registry, never a value
        freshly returned by a method call), odoo-development-
        unit-test references/python-escape-hatch.md.
        """
        admin = self.env.ref("base.user_admin")
        income, deferred_account, journal, product = self._setup_accounting("CDPRPY")
        income_usage = self.env.ref(
            "ssi_product_usage_account_type.product_usage_type_income"
        )
        ptype = self.env["promotion_type"].create(
            {
                "name": "Create Due Recognition Python Type",
                "code": "/",
                "discount_usage_id": income_usage.id,
                "discount_type": "fixed",
                "discount_amount": 2500.0,
                "journal_id": journal.id,
                "product_id": product.id,
                "account_id": income.id,
                "recognition_method": "deferred",
                "deferred_account_id": deferred_account.id,
                "recognition_journal_id": journal.id,
            }
        )
        code = self.env["promotion_code"].create(
            {
                "voucher_code": "CDPRPY-001",
                "type_id": ptype.id,
            }
        )
        self._confirm_and_approve(code)
        customer_1 = self.env["res.partner"].create(
            {"name": "Create Due Recognition Python Customer 1"}
        )
        customer_2 = self.env["res.partner"].create(
            {"name": "Create Due Recognition Python Customer 2"}
        )
        today = fields.Date.today()
        usage_1 = self.env["promotion_code_usage"].create(
            {
                "promotion_code_id": code.id,
                "partner_id": customer_1.id,
                "date": today - timedelta(days=30),
                "deferred_account_id": deferred_account.id,
                "recognition_journal_id": journal.id,
                "recognition_date": today - timedelta(days=1),
                "user_id": admin.id,
            }
        )
        usage_2 = self.env["promotion_code_usage"].create(
            {
                "promotion_code_id": code.id,
                "partner_id": customer_2.id,
                "date": today - timedelta(days=20),
                "deferred_account_id": deferred_account.id,
                "recognition_journal_id": journal.id,
                "recognition_date": today - timedelta(days=2),
                "user_id": admin.id,
            }
        )
        self._confirm_and_approve(usage_1)
        self._confirm_and_approve(usage_2)
        self.assertEqual(usage_1.recognition_state, "pending")
        self.assertEqual(usage_2.recognition_state, "pending")
        wizard = (
            self.env["create_due_promotion_recognition"]
            .with_user(admin)
            .create({"date": today})
        )
        self.assertEqual(wizard.usage_ids, usage_1 | usage_2)
        action = wizard.with_user(admin).action_create_due_recognition()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "promotion_code_usage_recognition")
        self.assertEqual(action["view_mode"], "tree,form")
        recognitions = self.env["promotion_code_usage_recognition"].search(
            action["domain"]
        )
        self.assertEqual(len(recognitions), 2)
        self.assertEqual(
            set(recognitions.mapped("usage_id.id")), {usage_1.id, usage_2.id}
        )
        for recognition in recognitions:
            self.assertEqual(recognition.date, today)
            self.assertEqual(recognition.journal_id, journal)
            self.assertEqual(recognition.state, "draft")
            self.assertEqual(recognition.amount, recognition.usage_id.amount_deferred)
