# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import Form, tagged


@tagged("post_install", "-at_install")
class TestPromotionCode(YamlTransactionCase):
    def test_promotion_code(self):
        self.run_yaml_scenario("test_data_promotion_code.yaml")

    def test_onchange_type_id_sets_discount_and_limit(self):
        """Selecting type_id copies discount and usage limit from the type."""
        ptype = self.env["promotion_type"].create(
            {
                "name": "Fixed Voucher",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 10000.0,
                "usage_limit": 5,
            }
        )
        form = Form(self.env["promotion_code"])
        form.voucher_code = "ONCHANGE-001"
        form.type_id = ptype
        self.assertEqual(form.discount_type, "fixed")
        self.assertEqual(form.discount_amount, 10000.0)
        self.assertEqual(form.usage_limit, 5)

    def test_onchange_date_end_from_validity(self):
        """date_end is computed from date_start + validity_duration when the
        promotion type has a validity period."""
        ptype = self.env["promotion_type"].create(
            {
                "name": "Validity Voucher",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 5000.0,
                "has_validity": True,
                "validity_duration": 30,
            }
        )
        form = Form(self.env["promotion_code"])
        form.voucher_code = "ONCHANGE-002"
        form.date_start = date.today()
        form.type_id = ptype
        self.assertEqual(form.date_end, date.today() + timedelta(days=30))

    def test_voucher_code_unique_constraint(self):
        """Two promotion codes cannot share the same voucher_code."""
        ptype = self.env["promotion_type"].create(
            {
                "name": "Unique Voucher Type",
                "code": "/",
                "discount_type": "fixed",
                "discount_amount": 1000.0,
            }
        )
        self.env["promotion_code"].create(
            {
                "voucher_code": "DUPLICATE-001",
                "type_id": ptype.id,
            }
        )
        with self.assertRaises(Exception):
            with self.cr.savepoint():
                self.env["promotion_code"].create(
                    {
                        "voucher_code": "DUPLICATE-001",
                        "type_id": ptype.id,
                    }
                )
