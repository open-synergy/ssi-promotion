# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPromotionCodeUsageRecognition(YamlTransactionCase):
    """Scenario tests for ``promotion_code_usage_recognition``."""

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

    def test_promotion_code_usage_recognition(self):
        """Run the workflow, onchange, and cancel-guard scenarios."""
        self.run_yaml_scenario("test_data_promotion_code_usage_recognition.yaml")

    def test_recognition_lines_with_referrer(self):
        """Assert each Recognition Line's own content on a referrer usage.

        A full recognition of a usage whose promotion code has a
        referrer produces exactly two Recognition Lines: one
        ``customer`` line and one ``referrer`` line, each carrying
        its own ``line_type``, ``amount`` (half of the usage's own
        Amount To Recognize, since both sides share the same
        Discount Amount), and ``debit_account_id`` (the customer's
        or referrer's own Final Account).

        Pure Python -- trigger P3 (L-06: ``odoo-yaml-test``'s o2m
        assert is set-based and cannot assert per-row field values,
        only membership/count), odoo-development-unit-test
        references/python-escape-hatch.md.
        """
        admin = self.env.ref("base.user_admin")
        income, deferred_account, journal, product = self._setup_accounting("PCURLN")
        account_type_income = self.env.ref("account.data_account_type_revenue")
        referrer_income = self.env["account.account"].create(
            {
                "code": "PCURLN-REFINC",
                "name": "PCURLN Referrer Income",
                "user_type_id": account_type_income.id,
            }
        )
        referrer_product = self.env["product.product"].create(
            {
                "name": "PCURLN Referrer Product",
                "type": "service",
                "property_account_income_id": referrer_income.id,
            }
        )
        ptype = self.env["promotion_type"].create(
            {
                "name": "Recognition Line Referrer Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 3000.0,
                "journal_id": journal.id,
                "product_id": product.id,
                "account_id": income.id,
                "referrer_product_id": referrer_product.id,
                "recognition_method": "deferred",
                "deferred_account_id": deferred_account.id,
                "recognition_journal_id": journal.id,
            }
        )
        referrer = self.env["res.partner"].create({"name": "Recognition Referrer"})
        code = self.env["promotion_code"].create(
            {
                "voucher_code": "RECOG-LINE-001",
                "type_id": ptype.id,
                "partner_id": referrer.id,
            }
        )
        self._confirm_and_approve(code)
        customer = self.env["res.partner"].create({"name": "Recognition Customer"})
        usage = self.env["promotion_code_usage"].create(
            {
                "promotion_code_id": code.id,
                "partner_id": customer.id,
                "deferred_account_id": deferred_account.id,
                "recognition_journal_id": journal.id,
            }
        )
        self._confirm_and_approve(usage)
        self.assertEqual(usage.amount_to_recognize, 6000.0)
        self.assertEqual(usage.amount_deferred, 6000.0)
        recognition = self.env["promotion_code_usage_recognition"].create(
            {
                "usage_id": usage.id,
                "date": usage.date,
                "amount": 6000.0,
                "journal_id": journal.id,
                "user_id": admin.id,
            }
        )
        self._confirm_and_approve(recognition)
        self.assertEqual(recognition.state, "done")
        lines = recognition.recognition_line_ids
        self.assertEqual(len(lines), 2)
        customer_line = lines.filtered(lambda line: line.line_type == "customer")
        referrer_line = lines.filtered(lambda line: line.line_type == "referrer")
        self.assertEqual(len(customer_line), 1)
        self.assertEqual(len(referrer_line), 1)
        self.assertEqual(customer_line.amount, 3000.0)
        self.assertEqual(referrer_line.amount, 3000.0)
        self.assertEqual(
            customer_line.debit_account_id,
            usage._get_final_account(referrer=False),
        )
        self.assertEqual(
            referrer_line.debit_account_id,
            usage._get_final_account(referrer=True),
        )
        self.assertNotEqual(
            customer_line.debit_account_id, referrer_line.debit_account_id
        )
