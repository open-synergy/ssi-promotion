# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import psycopg2
from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestPromotionCode(YamlTransactionCase):
    """Scenario tests for ``promotion_code``."""

    def test_promotion_code(self):
        """Run the CRUD, workflow, and onchange scenarios."""
        self.run_yaml_scenario("test_data_promotion_code.yaml")

    @mute_logger("odoo.sql_db")
    def test_voucher_code_unique_constraint(self):
        """Reject a duplicate ``voucher_code`` at database level.

        Pure Python -- trigger P5 (L-22: ``psycopg2.IntegrityError``,
        raised here by the ``voucher_code_unique`` entry in
        ``_sql_constraints``, is outside the 12 error types
        ``expect_error`` understands), odoo-development-unit-test
        references/python-escape-hatch.md. ``mute_logger`` silences
        the PostgreSQL ERROR line this intentionally triggers, so
        ``oca_checklog_odoo`` does not fail CI even though the test
        itself passes.
        """
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
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self.env["promotion_code"].create(
                    {
                        "voucher_code": "DUPLICATE-001",
                        "type_id": ptype.id,
                    }
                )
