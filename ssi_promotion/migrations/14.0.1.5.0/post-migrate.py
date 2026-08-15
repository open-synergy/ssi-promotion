# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# Migration: 14.0.1.4.1 -> 14.0.1.5.0
#
# Changes: 'discount_usage_id' is a new required field on
#          'promotion_type', replacing the 'property_account_income_id'
#          fallback previously used by '_get_final_account'. Existing
#          rows have no way to fill it themselves, so this backfills
#          every row still empty with
#          'ssi_product_usage_account_type.product_usage_type_income'
#          -- the closest equivalent of the fallback this field
#          replaces. 'referrer_discount_usage_id' stays empty
#          (optional, falls back to 'discount_usage_id' at runtime).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Backfill 'discount_usage_id' on existing 'promotion_type' rows.

    :param env: the migration environment
    :param version: the version being migrated to (unused)
    :return: nothing; updates ``promotion_type`` rows
    """
    income_usage = env.ref("ssi_product_usage_account_type.product_usage_type_income")
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE promotion_type
        SET discount_usage_id = %s
        WHERE discount_usage_id IS NULL
        """,
        (income_usage.id,),
    )
    _logger.info(
        "Stamped discount_usage_id=%s on %s promotion_type row(s).",
        income_usage.id,
        env.cr.rowcount,
    )
