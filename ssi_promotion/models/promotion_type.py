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

    The discount rule granted to the referrer
    (promotion_code.partner_id) is configured separately from the voucher
    user's own through the 'Referrer Discount Type' family of fields,
    which defaults to 'Same as Customer' so both sides keep sharing a
    single amount unless told otherwise.

    Also configures whether a usage of this type recognizes its
    discount immediately or defers it: see 'Recognition Method',
    'Deferred Account', and the journal used to release that deferral
    later, 'Recognition Journal'.

    The referrer's own side of that deferral is configured separately
    through the 'Referrer Recognition Method' family of fields, which
    defaults to 'Same as Customer' so both sides keep sharing a single
    deferral rule unless told otherwise.
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
    referrer_discount_type = fields.Selection(
        string="Referrer Discount Type",
        selection=[
            ("same", "Same as Customer"),
            ("fixed", "Fixed"),
            ("percentage", "Percentage"),
            ("python", "Python Code"),
        ],
        default="same",
        required=True,
        help="How the discount amount granted to the referrer "
        "(promotion_code.partner_id) by a promotion code of this type is "
        "computed: Same as Customer = the referrer gets exactly what the "
        "voucher user gets, Fixed = a flat amount, Percentage = a "
        "percentage of the referenced document's total, Python Code = a "
        "custom formula set through 'Referrer Discount Python Code'.",
    )
    referrer_discount_amount = fields.Float(
        string="Referrer Discount Amount",
        help="Flat discount amount granted to the referrer per usage when "
        "'Referrer Discount Type' is set to Fixed.",
    )
    referrer_discount_percentage = fields.Float(
        string="Referrer Discount Percentage (%)",
        help="Percentage of the referenced document's total amount granted "
        "to the referrer as discount per usage when 'Referrer Discount "
        "Type' is set to Percentage.",
    )
    referrer_discount_python_code = fields.Text(
        string="Referrer Discount Python Code",
        default="# Available variables: env, document, promotion_code, "
        "promotion_type, reference_document\n"
        "# Assign the computed referrer discount amount to 'result'\n"
        "result = 0.0",
        help="Python code executed to compute the referrer's discount "
        "amount when 'Referrer Discount Type' is set to Python Code. The "
        "code must assign the computed amount to a variable named "
        "'result'.",
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
    referrer_recognition_method = fields.Selection(
        string="Referrer Recognition Method",
        selection=[
            ("same", "Same as Customer"),
            ("immediate", "Immediate"),
            ("deferred", "Deferred"),
        ],
        default="same",
        required=True,
        help="How the discount granted to the referrer "
        "(promotion_code.partner_id) by a promotion_code_usage of this "
        "type is booked on its own journal entry: Same as Customer = the "
        "referrer follows the voucher user's own 'Recognition Method', "
        "Immediate = the referrer journal entry line debits its Final "
        "Account right away, Deferred = that line debits 'Referrer "
        "Deferred Account' instead, so the referrer's own discount can "
        "be recognized later independently of the voucher user's.",
    )
    referrer_deferred_account_id = fields.Many2one(
        string="Referrer Deferred Account",
        comodel_name="account.account",
        ondelete="restrict",
        help="Account debited on the referrer journal entry line of a "
        "promotion_code_usage of this type instead of its Final "
        "Account, while that usage's own 'Referrer Recognition Method' "
        "is set to Deferred. Defaulted onto each new usage of this "
        "type, but may still be overridden manually on the usage "
        "itself.",
    )
    referrer_recognition_journal_id = fields.Many2one(
        string="Referrer Recognition Journal",
        comodel_name="account.journal",
        ondelete="restrict",
        help="Accounting journal used by a promotion_code_usage_"
        "recognition document that releases a usage of this type's own "
        "Referrer Deferred Account. Defaulted onto each new usage of "
        "this type, but may still be overridden manually on the usage "
        "itself.",
    )
    allocation_account_selection_method = fields.Selection(
        string="Allocation Account Selection Method",
        selection=[
            ("manual", "Manual"),
            ("domain", "Domain"),
            ("code", "Python Code"),
        ],
        default="domain",
        required=True,
        help="How a promotion_code_usage_allocation row's own 'Allowed "
        "Accounts' is computed from this type: Manual = a fixed set of "
        "accounts ('Allocation Accounts'), Domain = accounts matching "
        "an Odoo search domain ('Allocation Account Domain'), Python "
        "Code = accounts returned by a custom formula ('Allocation "
        "Account Python Code').",
    )
    allocation_account_ids = fields.Many2many(
        string="Allocation Accounts",
        comodel_name="account.account",
        relation="rel_promotion_type_2_allocation_account",
        column1="promotion_type_id",
        column2="account_account_id",
        help="Fixed set of accounts a promotion_code_usage_allocation row "
        "of this type may target, used when 'Allocation Account "
        "Selection Method' is set to Manual.",
    )
    allocation_account_domain = fields.Text(
        string="Allocation Account Domain",
        default="[('reconcile', '=', True)]",
        help="Odoo search domain on 'account.account' selecting the "
        "accounts a promotion_code_usage_allocation row of this type "
        "may target, used when 'Allocation Account Selection Method' "
        "is set to Domain. The default keeps every reconcilable "
        "account allowed, matching the behaviour before this field "
        "existed.",
    )
    allocation_account_python_code = fields.Text(
        string="Allocation Account Python Code",
        default="result = []",
        help="Python code executed to compute the accounts a "
        "promotion_code_usage_allocation row of this type may target, "
        "used when 'Allocation Account Selection Method' is set to "
        "Python Code. The code must assign the resulting recordset to "
        "a variable named 'result'.",
    )
