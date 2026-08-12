# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Promotion + Operating Unit",
    "version": "14.0.1.0.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "contributors": [
        "Andhitia Rama <andhitia.r@gmail.com>",
    ],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_promotion",
        "ssi_operating_unit_mixin",
    ],
    "data": [
        "security/res_group/promotion_code.xml",
        "security/res_group/promotion_code_usage.xml",
        "security/ir_rule/promotion_code.xml",
        "security/ir_rule/promotion_code_usage.xml",
        "views/promotion_code.xml",
        "views/promotion_code_usage.xml",
    ],
}
