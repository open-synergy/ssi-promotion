# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPromotionCodeUsageReferrerDocument(YamlTransactionCase):
    """Scenario tests for the per-side reference document of
    ``promotion_code_usage``.
    """

    def test_promotion_code_usage_referrer_document(self):
        """Run the per-side allocation, percentage, fallback, and
        disallowed model scenarios.
        """
        self.run_yaml_scenario("test_data_promotion_code_usage_referrer_document.yaml")
