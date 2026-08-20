# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
# Migration: 14.0.1.17.0 -> 14.0.1.18.0
#
# Changes: 'voucher_code' is removed from 'promotion_code'; 'name'
#          (the '# Document' field from 'mixin.transaction') becomes
#          the single code field going forward. This backfills 'name'
#          from the legacy 'voucher_code' for rows where it carries a
#          value that is not already taken by another row. The
#          'voucher_code' column itself is kept, unused, so a skipped
#          row's original code can still be recovered by hand.

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Copy 'voucher_code' into 'name' on existing 'promotion_code' rows.

    Only rows whose 'voucher_code' is non-empty, differs from the
    row's own 'name', and is not already used as the 'name' of a
    different row are updated -- 'name' carries no database-level
    unique index (see Keputusan Desain, open-synergy/ssi-promotion#67),
    so silently colliding two rows onto the same code would only
    surface later as a confusing duplicate-number ``UserError``. Rows
    left untouched because their 'voucher_code' was blank, or because
    it conflicted with another row's 'name', are logged with their id
    -- that log is the only remaining trace a legacy code was not
    carried over.

    :param env: the migration environment
    :param version: the version being migrated to (unused)
    :return: nothing; updates ``promotion_code`` rows
    """
    cr = env.cr
    openupgrade.logged_query(
        cr,
        """
        UPDATE promotion_code AS pc
        SET name = btrim(pc.voucher_code)
        WHERE pc.voucher_code IS NOT NULL
          AND btrim(pc.voucher_code) != ''
          AND btrim(pc.voucher_code) != pc.name
          AND NOT EXISTS (
              SELECT 1
              FROM promotion_code AS other
              WHERE other.name = btrim(pc.voucher_code)
                AND other.id != pc.id
          )
        """,
    )
    _logger.info(
        "Copied voucher_code into name on %s promotion_code row(s).",
        cr.rowcount,
    )

    cr.execute(
        """
        SELECT id, btrim(voucher_code) = '' AS is_blank
        FROM promotion_code
        WHERE voucher_code IS NOT NULL
          AND (btrim(voucher_code) = '' OR btrim(voucher_code) != name)
        ORDER BY id
        """
    )
    blank_ids = []
    conflict_ids = []
    for row_id, is_blank in cr.fetchall():
        (blank_ids if is_blank else conflict_ids).append(row_id)

    if blank_ids:
        _logger.warning(
            "promotion_code row(s) %s had a blank voucher_code -- "
            "nothing to carry over into name.",
            blank_ids,
        )
    if conflict_ids:
        _logger.warning(
            "promotion_code row(s) %s kept their old name -- "
            "voucher_code conflicted with another row's name.",
            conflict_ids,
        )
