# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PromotionType(models.Model):
    """
    Configuration for a category of voucher/referral code.

    Determines how much discount a promotion_code_usage grants (fixed
    amount, percentage of the referenced document, or custom Python
    formula), how many times a code may be used, whether the code expires,
    which document models a usage may reference, the Python rule used to
    validate a usage, and the accounting configuration used to generate
    the customer (and optional referrer) journal entry automatically.

    Also configures whether a usage of this type recognizes its
    discount immediately or defers it: see 'Recognition Method',
    'Deferred Account', and the journal used to release that deferral
    later, 'Recognition Journal'.
    """

    _name = "promotion_type"
    _inherit = [
        "mixin.master_data",
    ]
    _description = "Promotion Type"

    discount_type = fields.Selection(
        string="Discount Type",
        selection=[
            ("fixed", "Fixed"),
            ("percentage", "Percentage"),
            ("python", "Python Code"),
        ],
        default="fixed",
        required=True,
        help="How the discount amount granted by a promotion code of this "
        "type is computed: Fixed = a flat amount, Percentage = a "
        "percentage of the referenced document's total, Python Code = "
        "a custom formula set through 'Discount Python Code'.",
    )
    discount_amount = fields.Float(
        string="Discount Amount",
        help="Flat discount amount granted per usage when 'Discount Type' "
        "is set to Fixed.",
    )
    discount_percentage = fields.Float(
        string="Discount Percentage (%)",
        help="Percentage of the referenced document's total amount granted "
        "as discount per usage when 'Discount Type' is set to Percentage.",
    )
    discount_python_code = fields.Text(
        string="Discount Python Code",
        default="# Available variables: env, document, promotion_code, "
        "promotion_type, reference_document\n"
        "# Assign the computed discount amount to 'result'\n"
        "result = 0.0",
        help="Python code executed to compute the discount amount when "
        "'Discount Type' is set to Python Code. The code must assign the "
        "computed amount to a variable named 'result'.",
    )
    usage_limit = fields.Integer(
        string="Usage Limit",
        default=0,
        help="Maximum number of times a single promotion code of this type "
        "may be used (state open/done). Set to 0 for unlimited usage.",
    )
    has_validity = fields.Boolean(
        string="Has Validity Period",
        default=False,
        help="If checked, a promotion code of this type expires after "
        "'Validity Duration (Days)' counted from its start date.",
    )
    validity_duration = fields.Integer(
        string="Validity Duration (Days)",
        help="Number of days a promotion code of this type stays valid "
        "after its start date. Only used when 'Has Validity Period' is "
        "checked.",
    )
    validity_python_code = fields.Text(
        string="Validity Check Python Code",
        default="# Available variables: env, document, promotion_code, "
        "promotion_type, reference_document\n"
        "# Assign True/False to 'result'\n"
        "result = True",
        help="Python code executed when a promotion_code_usage of this "
        "type is confirmed, in addition to the usage limit and validity "
        "period check. The code must assign True (valid) or False "
        "(invalid) to a variable named 'result'.",
    )
    allowed_model_ids = fields.Many2many(
        string="Allowed Reference Models",
        comodel_name="ir.model",
        relation="rel_promotion_type_2_model",
        column1="type_id",
        column2="model_id",
        help="Document models that a promotion_code_usage of this type is "
        "allowed to reference through its 'Reference Document' field. "
        "Referencing any other model is rejected.",
    )
    journal_id = fields.Many2one(
        string="Discount Journal",
        comodel_name="account.journal",
        domain=[("type", "=", "sale")],
        help="Sales journal used to create the customer accounting entry "
        "when a promotion_code_usage of this type is approved.",
    )
    product_id = fields.Many2one(
        string="Discount Product",
        comodel_name="product.product",
        help="Product resolved through the Product Usage Account Type "
        "mechanism (together with 'Discount Usage') as the fallback for "
        "the voucher user's own discount account when a "
        "promotion_code_usage of this type is approved and 'Discount "
        "Account' is not set. See '_get_product_account'.",
    )
    account_id = fields.Many2one(
        string="Discount Account",
        comodel_name="account.account",
        help="Account debited on the customer accounting entry's own "
        "discount line. If left empty, the account is resolved from "
        "'Discount Product' through the Product Usage Account Type "
        "mechanism (product, its template, its category, then "
        "'Discount Usage' itself) -- see '_get_product_account'.",
    )
    discount_usage_id = fields.Many2one(
        string="Discount Usage",
        comodel_name="product.usage_type",
        required=True,
        ondelete="restrict",
        help="Product usage code used to resolve the voucher user's own "
        "discount account from 'Discount Product' (product, template, "
        "category, then this usage's own 'Account') when 'Discount "
        "Account' is not set. See '_get_product_account'.",
    )
    referrer_product_id = fields.Many2one(
        string="Referrer Discount Product",
        comodel_name="product.product",
        help="Product resolved through the Product Usage Account Type "
        "mechanism (together with 'Referrer Discount Usage', falling "
        "back to 'Discount Usage') as the fallback for the referrer's "
        "own discount account (promotion_code.partner_id) when a "
        "promotion_code_usage of this type is approved. If left empty, "
        "'Discount Product' is reused.",
    )
    referrer_discount_usage_id = fields.Many2one(
        string="Referrer Discount Usage",
        comodel_name="product.usage_type",
        ondelete="restrict",
        help="Product usage code used to resolve the referrer's own "
        "discount account, the same way 'Discount Usage' resolves the "
        "voucher user's own. If left empty, 'Discount Usage' is reused.",
    )
    referrer_journal_id = fields.Many2one(
        string="Referrer Discount Journal",
        comodel_name="account.journal",
        domain=[("type", "=", "sale")],
        help="Sales journal used to create the referrer accounting "
        "entry. If left empty, 'Discount Journal' is reused.",
    )
    recognition_method = fields.Selection(
        string="Recognition Method",
        selection=[
            ("immediate", "Immediate"),
            ("deferred", "Deferred"),
        ],
        default="immediate",
        required=True,
        help="How the discount granted by a promotion_code_usage of this "
        "type is booked on its journal entry(-ies). Immediate = the "
        "customer and referrer journal entry lines debit their Final "
        "Account (see 'Discount Account', falling back to the products' "
        "own income account) right away, exactly as before this field "
        "existed. Deferred = both lines debit 'Deferred Account' "
        "instead, so the discount can be recognized later by a "
        "separate document.",
    )
    deferred_account_id = fields.Many2one(
        string="Deferred Account",
        comodel_name="account.account",
        ondelete="restrict",
        help="Account debited on the journal entry line(s) of a "
        "promotion_code_usage of this type instead of its Final "
        "Account, while that usage's own 'Recognition Method' is set "
        "to Deferred. Defaulted onto each new usage of this type, but "
        "may still be overridden manually on the usage itself.",
    )
    recognition_journal_id = fields.Many2one(
        string="Recognition Journal",
        comodel_name="account.journal",
        ondelete="restrict",
        help="Accounting journal used by a promotion_code_usage_"
        "recognition document that releases a usage of this type's "
        "own Deferred Account. Defaulted onto each new usage of this "
        "type, but may still be overridden manually on the usage "
        "itself.",
    )
