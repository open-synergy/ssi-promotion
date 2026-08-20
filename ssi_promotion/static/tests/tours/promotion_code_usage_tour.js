odoo.define("ssi_promotion.promotion_code_usage_tour", function (require) {
    "use strict";

    var tour = require("web_tour.tour");

    // ── Shared Flow 1 — Open the Promotion > Usages menu.
    var openUsagesMenuSteps = [
        tour.stepUtils.showAppsMenuItem(),
        {
            content: "Open the Promotion app",
            trigger: '.o_app[data-menu-xmlid="ssi_promotion.menu_root_promotion"]',
        },
        {
            content: "Open the Usages menu",
            trigger:
                '.o_menu_sections [data-menu-xmlid="ssi_promotion.promotion_code_usage_menu"]',
        },
        {
            // Gerbang: tunggu action TUJUAN benar-benar terpasang (nama
            // action, bukan nama menuitem -- keduanya berbeda di sini:
            // menuitem "Usages", action "Promotion Code Usages").
            content: "Usages list is displayed",
            trigger:
                ".o_control_panel .breadcrumb-item.active:contains(Promotion Code Usages)",
            extra_trigger: ".o_list_view",
            run: function () {
                // Assertion only; do not trigger the default click action.
            },
        },
    ];

    // IK: docs/promotion_code_usage/01-create.md
    tour.register(
        "ssi_promotion_promotion_code_usage_create",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow 2 — Click the New button. (14.0: "Create")
            {
                content: "Click Create",
                trigger: ".o_list_button_add",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Form is open in edit mode",
                trigger: ".o_form_view.o_form_editable",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Fill in the required fields (Promotion Code,
            // Voucher User). Usage Date keeps its own default (today);
            // Reference Document is optional and left empty. Discount
            // & Accounting Entry tab fields are auto-computed once
            // Promotion Code is picked -- out of tour scope (value
            // verification is unit-test territory).
            {
                content: "Select the Promotion Code",
                trigger: ".o_field_many2one[name='promotion_code_id'] input",
                run: "text TOUR-PCU-CODE",
            },
            {
                content: "Pick the promotion code from the dropdown",
                trigger: ".ui-autocomplete .ui-menu-item a:contains(TOUR-PCU-CODE)",
                in_modal: false,
            },
            {
                content: "Select the Voucher User",
                trigger: ".o_field_many2one[name='partner_id'] input",
                run: "text TOUR PCU Create Customer",
            },
            {
                content: "Pick the partner from the dropdown",
                trigger:
                    ".ui-autocomplete .ui-menu-item a:contains(TOUR PCU Create Customer)",
                in_modal: false,
            },

            // Flow 3 (cont.) — Select the Reference Document, needed
            // below by the "Populate Allocation" inline action.
            {
                content: "Choose the Reference Document model",
                trigger: ".o_field_widget[name='document_reference'] select",
                run: "text account.move",
            },
            {
                content: "Select the Reference Document",
                trigger: ".o_field_widget[name='document_reference'] input",
                run: "text TOUR-PCU-ALLOC-INV",
            },
            {
                content: "Pick the reference document from the dropdown",
                trigger:
                    ".ui-autocomplete .ui-menu-item a:contains(TOUR-PCU-ALLOC-INV)",
                in_modal: false,
            },

            // Flow 5 — Open the Allocation tab and click Populate
            // Allocation (an inline action documented in
            // docs/promotion_code_usage/01-create.md, not a tour of
            // its own -- see odoo-development-instruksi-kerja,
            // action-placement.md).
            {
                content: "Open the Allocation tab",
                trigger: ".o_notebook .nav-link:contains(Allocation)",
            },
            {
                content: "Click Populate Allocation",
                trigger: "button[name='action_populate_allocation']",
                extra_trigger: ".o_form_view",
            },
            {
                // Gerbang: the Allocation tab starts empty, so a data
                // row naming the reference invoice can only appear
                // once action_populate_allocation has actually run
                // (patterns.md §P).
                content: "Allocation row is populated from the reference document",
                trigger:
                    ".o_field_widget[name='allocation_ids'] " +
                    ".o_data_row:contains(TOUR-PCU-ALLOC-INV)",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 6 — Click Save.
            {
                content: "Save the record",
                trigger: ".o_form_button_save",
            },

            // Post-Condition — A new record is created in Draft status.
            {
                content: "Record is saved in Draft status",
                trigger: ".o_form_view.o_form_readonly",
                extra_trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='draft'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/02-edit.md
    tour.register(
        "ssi_promotion_promotion_code_usage_edit",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow 2 — Find and open the record to edit.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCU-EDIT) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Edit button.
            {
                content: "Click the Edit button",
                trigger: ".o_form_button_edit",
            },
            {
                content: "Form is now editable",
                trigger: ".o_form_view.o_form_editable",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 4 — Change the Usage Date field, and set Reference
            // Document (needed below by "Populate Allocation").
            {
                content: "Change the Usage Date",
                trigger: ".o_field_widget[name='date'] input",
                run: "text 01/15/2026",
            },
            {
                content: "Choose the Reference Document model",
                trigger: ".o_field_widget[name='document_reference'] select",
                run: "text account.move",
            },
            {
                content: "Select the Reference Document",
                trigger: ".o_field_widget[name='document_reference'] input",
                run: "text TOUR-PCU-ALLOC-INV",
            },
            {
                content: "Pick the reference document from the dropdown",
                trigger:
                    ".ui-autocomplete .ui-menu-item a:contains(TOUR-PCU-ALLOC-INV)",
                in_modal: false,
            },

            // Flow 5 — Open the Allocation tab and click Populate
            // Allocation (an inline action documented in
            // docs/promotion_code_usage/02-edit.md, not a tour of its
            // own -- see odoo-development-instruksi-kerja,
            // action-placement.md).
            {
                content: "Open the Allocation tab",
                trigger: ".o_notebook .nav-link:contains(Allocation)",
            },
            {
                content: "Click Populate Allocation",
                trigger: "button[name='action_populate_allocation']",
                extra_trigger: ".o_form_view",
            },
            {
                // Gerbang: the Allocation tab starts empty, so a data
                // row naming the reference invoice can only appear
                // once action_populate_allocation has actually run
                // (patterns.md §P).
                content: "Allocation row is populated from the reference document",
                trigger:
                    ".o_field_widget[name='allocation_ids'] " +
                    ".o_data_row:contains(TOUR-PCU-ALLOC-INV)",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 6 — Click Save.
            {
                content: "Save the record",
                trigger: ".o_form_button_save",
            },

            // Post-Condition — The record is updated with the new values.
            {
                content: "Record is saved",
                trigger: ".o_form_view.o_form_readonly",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/03-delete.md
    tour.register(
        "ssi_promotion_promotion_code_usage_delete",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow 2 — Open the record to delete.
            // This fixture keeps its default document number "/" (the
            // IK Pre-Condition for delete), so its own display name
            // renders as "*<id>" (mixin_transaction.py name_get) --
            // the only row in this list carrying a literal "*".
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(*) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click Action > Delete.
            {
                content: "Open the Action menu",
                trigger: ".o_cp_action_menus button:contains(Action)",
            },
            {
                content: "Click Delete",
                // Item Action menu adalah komponen Owl; cocokkan LABEL
                // PERSIS, bukan substring ":contains" yang bisa keliru
                // menunjuk item lain (mis. "Archive").
                trigger: ".o_cp_action_menus .o_menu_item a",
                run: function () {
                    var $delete = $(".o_cp_action_menus .o_menu_item a").filter(
                        function () {
                            return $(this).text().trim() === "Delete";
                        }
                    );
                    $delete[0].click();
                },
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm deletion",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // After delete, 14.0 can display the NEXT record in the
            // list instead of returning to the list itself. Click the
            // breadcrumb explicitly before asserting the list.
            {
                content: "Click the Promotion Code Usages breadcrumb",
                trigger:
                    ".breadcrumb-item.o_back_button a:contains(Promotion Code Usages)",
            },

            // Post-Condition — Back on the list, without the record.
            {
                content: "Back to the list without the deleted record",
                trigger: ".o_list_view:not(:has(.o_data_row:contains(*)))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/04-confirm.md
    tour.register(
        "ssi_promotion_promotion_code_usage_confirm",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow 2 — Open the record to confirm.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCU-CONFIRM) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Confirm button.
            {
                content: "Click the Confirm button",
                trigger: ".o_statusbar_buttons button[name='action_confirm']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status changes to Waiting for Approval.
            {
                content: "Status is Waiting for Approval",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='confirm'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/05-approve.md
    tour.register(
        "ssi_promotion_promotion_code_usage_approve",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow 2 — Open the record to approve.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCU-APPROVE) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Approve button.
            {
                content: "Click the Approve button",
                trigger: ".o_statusbar_buttons button[name='action_approve_approval']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Sole approval level fulfilled: this
            // document is automatically opened, and since it has no
            // deferred side (Recognition State Not Applicable) it
            // finishes in the very same operation, status landing
            // straight on Done (docs/promotion_code_usage/05-approve.md).
            {
                content: "Status is Done",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='done'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/06-reject.md
    tour.register(
        "ssi_promotion_promotion_code_usage_reject",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow 2 — Open the record to reject.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCU-REJECT) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Reject button.
            {
                content: "Click the Reject button",
                trigger: ".o_statusbar_buttons button[name='action_reject_approval']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status changes to Rejected.
            {
                content: "Status is Rejected",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='reject'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/09-finish.md
    //
    // Triggered by base.automation off recognition_state, not a button
    // (see the IK's own Flow) -- the triggering
    // promotion_code_usage_recognition document is already completed
    // in Python (setUpClass), so this tour only opens the
    // already-finished record and reads its statusbar
    // (odoo-development-ui-test skill, scope-and-boundaries.md §1
    // rule 6).
    tour.register(
        "ssi_promotion_promotion_code_usage_finish",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow — Open the record whose deferred side is fully
            // recognized.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCU-FINISH) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Post-Condition — Status is Done, reached on its own.
            {
                content: "Status is Done",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='done'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/17-reopen.md
    //
    // Triggered by base.automation off recognition_state, not a button
    // (see the IK's own Flow) -- the triggering
    // promotion_code_usage_recognition document is already completed
    // and cancelled in Python (setUpClass), so this tour only opens
    // the already-reopened record and reads its statusbar
    // (odoo-development-ui-test skill, scope-and-boundaries.md §1
    // rule 6).
    tour.register(
        "ssi_promotion_promotion_code_usage_reopen",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow — Open the record whose Done recognition was
            // cancelled.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCU-REOPEN) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Post-Condition — Status is back on Open, reached on its
            // own.
            {
                content: "Status is Open",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='open'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/10-cancel.md
    tour.register(
        "ssi_promotion_promotion_code_usage_cancel",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow 2 — Open the record to cancel.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCU-CANCEL) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Cancel button.
            // The Cancel button is type="action" (it opens the
            // base.select_cancel_reason wizard action) -- its "name"
            // attribute resolves to a numeric action id at render time,
            // so it must be targeted by label, not by name
            // (selectors.md §4).
            {
                content: "Click the Cancel button",
                trigger: ".o_statusbar_buttons button:enabled:contains('Cancel')",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — In the wizard that appears, select the
            // Cancellation Reason.
            {
                content: "Wizard is open",
                // 14.0: trigger is searched INSIDE the modal, so do not
                // prefix it with ".modal" (see patterns.md §H).
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },
            // Cancel_reason_id is rendered with widget="radio" by
            // the Select Cancel Reason wizard view
            // (ssi_transaction_cancel_mixin/wizards/
            // base_select_cancel_reason_views.xml), so it is a radio
            // item that gets clicked -- not a many2one autocomplete.
            {
                content: "Select the cancellation reason",
                trigger:
                    ".o_field_widget[name='cancel_reason_id'] " +
                    ".o_radio_item:contains(TOUR PCU Cancel Reason) input",
                run: "click",
            },

            // Flow 5 — Click Confirm.
            {
                content: "Confirm the wizard",
                trigger: ".modal-footer button[name='action_confirm']",
                in_modal: true,
            },

            // Flow 6 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status changes to Cancelled.
            {
                content: "Status is Cancelled",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='cancel'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/12-restart.md
    tour.register(
        "ssi_promotion_promotion_code_usage_restart",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow 2 — Remove the default state filter facet from the
            // search bar. The default view (search_default_dom_draft/
            // confirm/open on promotion_code_usage_action) only shows
            // Draft, Waiting for Approval, and Open documents -- a
            // Cancelled document like this tour's fixture stays hidden
            // until that facet is removed. Removing the facet (instead
            // of opening the Filters dropdown to toggle a Cancel
            // filter) avoids the Owl FilterMenu dropdown, whose open
            // state is not reliably set by a synthetic click in 14.0
            // (odoo-development-ui-test, patterns.md §I/§J); the facet
            // chip's remove icon is a plain DOM element with no such
            // hazard, and this exact idiom is already proven by
            // promotion_code_tour.js's own 12-restart tour. Here it is
            // the very first interaction after navigating in, so
            // explicitly wait for one of the default-filtered rows
            // (TOUR-PCU-EDIT, a Draft fixture) before touching the
            // facet, to rule out clicking a transient pre-settle
            // render of the search bar.
            {
                content: "Default-filtered list has settled",
                trigger: ".o_data_row:contains(TOUR-PCU-EDIT)",
                extra_trigger: ".o_list_view",
                run: function () {
                    // Assertion only.
                },
            },
            {
                content:
                    "Remove the default state filter to reveal " +
                    "Cancelled documents",
                trigger: ".o_searchview_facet .o_facet_remove",
                run: "click",
            },
            {
                // Gerbang: don't just assume the click "took" -- wait
                // for the facet chip to actually be gone before relying
                // on the list containing every state.
                content: "Default state filter is removed",
                trigger: "body:not(:has(.o_searchview_facet))",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Open the record to restart.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCU-RESTART) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 4 — Click the Restart button.
            {
                content: "Click the Restart button",
                trigger: ".o_statusbar_buttons button[name='action_restart']",
                extra_trigger: ".o_form_view",
            },

            // Flow 5 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status returns to Draft.
            {
                content: "Status is Draft",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='draft'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/13-reset-number.md
    tour.register(
        "ssi_promotion_promotion_code_usage_reset_number",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow 2 — Open the record whose document number will be
            // reset. The Pre-Condition fixture carries the manually
            // assigned number "TOUR-PCU-RESET-MANUAL".
            {
                content: "Open the record",
                trigger:
                    ".o_data_row:contains(TOUR-PCU-RESET-MANUAL) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open with its manual document number",
                trigger:
                    ".oe_title .o_field_widget[name='display_name']" +
                    ":contains(TOUR-PCU-RESET-MANUAL)",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Reset Document Number button.
            {
                content: "Click the Reset Document Number button",
                trigger:
                    ".o_statusbar_buttons button[name='action_reset_document_number']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Document number returns to "/", shown
            // as "*<id>" by name_get (mixin_transaction.py). This
            // string could not have matched before the reset ran,
            // since the record showed its manual number instead
            // (patterns.md §P).
            {
                content: "Document number returns to /",
                trigger: ".oe_title .o_field_widget[name='display_name']:contains(*)",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/14-restart-approval.md
    tour.register(
        "ssi_promotion_promotion_code_usage_restart_approval",
        {
            test: true,
            url: "/web",
        },
        [].concat(openUsagesMenuSteps, [
            // Flow 2 — Open the record to restart the approval
            // process for.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PCU-REAPPROVAL) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Restart Approval Process button.
            {
                content: "Click the Restart Approval Process button",
                trigger:
                    ".o_statusbar_buttons button[name='action_reload_approval_template']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status remains Waiting for Approval, and
            // the Approvals tab displays the approval list newly formed
            // from the approval template. Row count/content is out of
            // tour scope (unit test territory); the gate below only
            // proves the reload happened.
            {
                content: "Open the Approvals tab",
                trigger: ".o_notebook .nav-link:contains(Approvals)",
                extra_trigger: "body:not(:has(.modal))",
            },
            {
                content: "The approval process has been rebuilt",
                trigger: ".o_field_widget[name='approval_ids'] .o_data_row",
                run: function () {
                    // Assertion only.
                },
            },
            {
                content: "Status is still Waiting for Approval",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='confirm'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code_usage/15-create-due-recognition.md
    tour.register(
        "ssi_promotion_promotion_code_usage_create_due_recognition",
        {
            test: true,
            url: "/web",
        },
        [
            // Flow 1 — Open the Promotion > Create Due Recognition menu.
            tour.stepUtils.showAppsMenuItem(),
            {
                content: "Open the Promotion app",
                trigger: '.o_app[data-menu-xmlid="ssi_promotion.menu_root_promotion"]',
            },
            {
                content: "Open the Create Due Recognition menu",
                trigger:
                    '.o_menu_sections [data-menu-xmlid="ssi_promotion.create_due_promotion_recognition_menu"]',
            },

            // Flow 2 — The wizard opens with Date and Usages pre-filled.
            {
                content: "The wizard is displayed",
                // 14.0: trigger is searched INSIDE the modal, so do not
                // prefix it with ".modal" (see patterns.md §H).
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Create Due Recognition button.
            {
                content: "Click the Create Due Recognition button",
                trigger: ".modal-footer button[name='action_create_due_recognition']",
            },

            // Post-Condition — The list of newly created Usage Recognition
            // documents is displayed.
            {
                content: "Usage Recognitions list is displayed",
                trigger:
                    ".o_control_panel .breadcrumb-item.active:contains(Usage Recognitions)",
                extra_trigger: ".o_list_view",
                run: function () {
                    // Assertion only.
                },
            },
        ]
    );

    // IK: docs/promotion_code_usage/16-apply-promotion-code.md
    tour.register(
        "ssi_promotion_promotion_code_usage_apply_promotion_code",
        {
            test: true,
            url: "/web",
        },
        [
            // Flow 1 — Open the Financial Accounting > Account
            // Receivable > Invoices menu, then open the fixture
            // invoice. ssi_financial_accounting REPLACES core
            // account.menu_finance's own groups_id (menu.xml, "Hide
            // menu") so the standard "Invoicing" app never renders at
            // all -- account.move is reached through
            // ssi_financial_accounting's own app instead.
            // "Account Receivable" (menu_account_receivable) is a
            // level-2 section: unlike a level-3+ grouping header, a
            // level-2 section ALWAYS renders its own clickable
            // dropdown-toggle with data-menu-xmlid even though it has
            // no action of its own (patterns.md §A, "Jumlah level
            // menu di IK ≠ jumlah step tour") -- it needs its own step
            // to open the dropdown before its own leaf ("Invoices")
            // becomes visible and clickable. The row-contains trigger
            // below doubles as both "the right list loaded" and "open
            // the record", since only the intended list can ever
            // contain this fixture's own unique document number.
            tour.stepUtils.showAppsMenuItem(),
            {
                content: "Open the Financial Accounting app",
                trigger:
                    '.o_app[data-menu-xmlid="ssi_financial_accounting.menu_root_financial_accounting"]',
            },
            {
                content: "Open the Account Receivable menu",
                trigger:
                    '.o_menu_sections [data-menu-xmlid="ssi_financial_accounting.menu_account_receivable"]',
            },
            {
                content: "Open the Invoices menu",
                trigger:
                    '.o_menu_sections [data-menu-xmlid="ssi_financial_accounting.customer_invoice_menu"]',
            },
            {
                content: "Open the fixture invoice",
                trigger: ".o_data_row:contains(TOUR-APC-INVOICE) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Invoice is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 2 — Click Action, then Apply Promotion Code.
            {
                content: "Open the Action menu",
                trigger: ".o_cp_action_menus button:contains(Action)",
            },
            {
                content: "Click Apply Promotion Code",
                // Action menu item is an Owl component; the correct
                // click target is the <a> inside .o_menu_item, matched
                // on EXACT label -- :contains() as a substring could
                // otherwise match an unrelated item (patterns.md §I).
                trigger: ".o_cp_action_menus .o_menu_item a",
                run: function () {
                    var $item = $(".o_cp_action_menus .o_menu_item a").filter(
                        function () {
                            return $(this).text().trim() === "Apply Promotion Code";
                        }
                    );
                    $item[0].click();
                },
            },

            // Flow 3 — In the wizard that appears, select the
            // Promotion Code (Voucher User fills in automatically,
            // read-only; Date keeps its own default of today).
            {
                content: "Wizard is open",
                // 14.0: trigger is searched INSIDE the modal, so do
                // not prefix it with ".modal" (see patterns.md §H).
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },
            {
                content: "Select the Promotion Code",
                trigger: ".o_field_many2one[name='promotion_code_id'] input",
                run: "text TOUR-APC-CODE",
            },
            {
                content: "Pick the promotion code from the dropdown",
                trigger: ".ui-autocomplete .ui-menu-item a:contains(TOUR-APC-CODE)",
                in_modal: false,
            },

            // Flow 4 — Click Apply.
            {
                content: "Click the Apply button",
                trigger: ".modal-footer button[name='action_apply_promotion_code']",
                in_modal: true,
            },

            // Post-Condition — The new usage is created in Draft
            // status, and its own form is displayed.
            {
                content: "New usage is created in Draft status",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='draft'].btn-primary",
                run: function () {
                    // Assertion only.
                },
            },
        ]
    );
});
