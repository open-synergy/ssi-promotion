# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPromotionCodeUsageAllocation(YamlTransactionCase):
    """Scenario tests for ``promotion_code_usage_allocation``."""

    def test_promotion_code_usage_allocation(self):
        """Run the reconciliation, cancel, and negative-path scenarios."""
        self.run_yaml_scenario("test_data_promotion_code_usage_allocation.yaml")
