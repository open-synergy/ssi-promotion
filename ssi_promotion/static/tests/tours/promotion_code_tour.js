odoo.define("ssi_promotion.promotion_code_tour", function (require) {
    "use strict";

    var tour = require("web_tour.tour");

    // ── Shared Flow 1 — Open the Promotion > Codes menu.
    var openCodesMenuSteps = [
        tour.stepUtils.showAppsMenuItem(),
        {
            content: "Open the Promotion app",
            trigger: '.o_app[data-menu-xmlid="ssi_promotion.menu_root_promotion"]',
        },
        {
            // "Codes" is the first child (lowest sequence) of the
            // Promotion app root (menu_root_promotion), so it is the
            // app's own landing action: opening the app already loaded
            // it once, and this click reloads the IDENTICAL action a
            // second time. Every content-based gate after it (active
            // breadcrumb, data row present) is therefore tautological
            // -- already true from the first render, never able to go
            // false -- so a synthetic marker is planted here instead
            // (odoo-development-ui-test, patterns-advanced-gotchas.md
            // §T, stale-marker gate; verified to source 14.0
            // 2026-08-20: each controller mounts its own ControlPanel
            // ComponentWrapper as its first child,
            // abstract_controller.js:92-94, and ActionManager destroys
            // the old controller on reload, action_manager.js:691-807
            // -- so the reload always yields a fresh, unmarked
            // .o_control_panel).
            content: "Open the Codes menu",
            trigger:
                '.o_menu_sections [data-menu-xmlid="ssi_promotion.promotion_code_menu"]',
            run: function (actions) {
                // Instrumentation-only marker; dies with the old
                // controller. Planted atomically with the click itself
                // to avoid a race between marking and clicking.
                $(".o_control_panel").addClass("oe_tour_stale");
                actions.click();
            },
        },
        {
            // Gerbang jujur: a control panel WITHOUT the marker only
            // exists once the reload has finished mounting the new
            // controller (the old, marked one is detached from the
            // document, so the selector cannot match it). The row
            // check proves the new controller's data has loaded too --
            // TOUR-PC-EDIT is a Draft fixture, shown under the default
            // dom_draft/confirm/open filter.
            content: "Codes action is remounted",
            trigger: ".o_control_panel:not(.oe_tour_stale)",
            extra_trigger: ".o_data_row:contains(TOUR-PC-EDIT)",
            run: function () {
                // Assertion only; do not trigger the default click action.
            },
        },
    ];

    // IK: docs/promotion_code/01-create.md
    tour.register(
        "ssi_promotion_promotion_code_create",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
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

            // Flow 3 — Fill in the required fields (Promotion Type).
            // # Document is left as "/" -- the system issues it on
            // approve (see Post-Condition); Discount & Usage tab
            // fields are auto-filled by onchange once Promotion Type
            // is picked -- out of tour scope (value verification is
            // unit-test territory).
            {
                content: "Select the Promotion Type",
                trigger: ".o_field_many2one[name='type_id'] input",
                run: "text TOUR PC Type",
            },
            {
                content: "Pick the type from the dropdown",
                trigger: ".ui-autocomplete .ui-menu-item a:contains(TOUR PC Type)",
                in_modal: false,
            },

            // Flow 5 — Click Save.
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

    // IK: docs/promotion_code/02-edit.md
    tour.register(
        "ssi_promotion_promotion_code_edit",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Find and open the record to edit.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-EDIT) .o_data_cell:first",
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

            // Flow 4 — Open the Note tab and change the Note field.
            // The Note tab is not the active tab by default (the
            // Discount & Usage tab is inserted first): its pane stays
            // display:none, hiding the textarea from the tour, until
            // this tab is opened.
            {
                content: "Open the Note tab",
                trigger: ".o_notebook .nav-link:contains(Note)",
            },
            {
                content: "Change the Note",
                trigger: "textarea.o_field_widget[name='note']",
                run: "text Edited via UI test tour.",
            },

            // Flow 5 — Click Save.
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

    // IK: docs/promotion_code/03-delete.md
    tour.register(
        "ssi_promotion_promotion_code_delete",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Find the record by its Referrer, then open it.
            // The document number column cannot be used here: this
            // fixture's is still "/" (Pre-Condition), rendered
            // "*<id>" by name_get() -- "TOUR-PC-DELETE" below matches
            // the Referrer column instead (test_ui_promotion_code.py,
            // cls.delete_referrer).
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-DELETE) .o_data_cell:first",
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
            //
            // Gerbang modal-tertutup (odoo-development-ui-test,
            // patterns.md §K): this is the first step polled after the
            // confirmation dialog closes, so it is exposed to the same
            // FieldWrapper re-render race as a bare Post-Condition
            // assertion would be.
            {
                content: "Click the Promotion Codes breadcrumb",
                trigger: ".breadcrumb-item.o_back_button a:contains(Promotion Codes)",
                extra_trigger: "body:not(:has(.modal))",
            },

            // Post-Condition — Back on the list, without the record.
            {
                content: "Back to the list without the deleted record",
                trigger: ".o_list_view:not(:has(.o_data_row:contains(TOUR-PC-DELETE)))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/04-confirm.md
    tour.register(
        "ssi_promotion_promotion_code_confirm",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to confirm.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-CONFIRM) .o_data_cell:first",
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
            //
            // Gerbang modal-tertutup (odoo-development-ui-test,
            // patterns.md §K): without this, the tour engine starts
            // polling the statusbar the instant the modal leaves the
            // DOM, while the form (including the statusbar
            // FieldWrapper) is still mid-re-render from the RPC
            // response -- see structure-and-runner.md's
            // "Cannot set properties of null (setting 'props')" entry.
            {
                content: "Status is Waiting for Approval",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='confirm'].btn-primary",
                extra_trigger: "body:not(:has(.modal))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/05-approve.md
    tour.register(
        "ssi_promotion_promotion_code_approve",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to approve.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-APPROVE) .o_data_cell:first",
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
            // document is automatically opened, status jumps straight
            // to Open.
            // Gerbang modal-tertutup (patterns.md §K) -- same
            // FieldWrapper re-render race as the confirm tour above.
            {
                content: "Status is Open",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='open'].btn-primary",
                extra_trigger: "body:not(:has(.modal))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/06-reject.md
    tour.register(
        "ssi_promotion_promotion_code_reject",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to reject.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-REJECT) .o_data_cell:first",
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
            //
            // Gerbang modal-tertutup (patterns.md §K) -- same
            // FieldWrapper re-render race as the confirm tour above.
            {
                content: "Status is Rejected",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='reject'].btn-primary",
                extra_trigger: "body:not(:has(.modal))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/09-finish.md
    tour.register(
        "ssi_promotion_promotion_code_finish",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to finish.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-FINISH) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open",
                trigger: ".o_form_view",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Click the Done button.
            {
                content: "Click the Done button",
                trigger: ".o_statusbar_buttons button[name='action_done']",
                extra_trigger: ".o_form_view",
            },

            // Flow 4 — Click OK on the confirmation dialog.
            {
                content: "Confirm the dialog",
                trigger: ".modal-footer button.btn-primary",
                in_modal: true,
            },

            // Post-Condition — Status changes to Done.
            //
            // Gerbang modal-tertutup (patterns.md §K) -- same
            // FieldWrapper re-render race as the confirm tour above.
            {
                content: "Status is Done",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='done'].btn-primary",
                extra_trigger: "body:not(:has(.modal))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/10-cancel.md
    tour.register(
        "ssi_promotion_promotion_code_cancel",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to cancel.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-CANCEL) .o_data_cell:first",
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
                    ".o_radio_item:contains(TOUR PC Cancel Reason) input",
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
            //
            // Gerbang modal-tertutup (patterns.md §K), placed on this
            // FINAL assertion only -- after both stacked modals (the
            // reason wizard, then its own confirmation dialog) have
            // closed -- same FieldWrapper re-render race as the
            // confirm tour above.
            {
                content: "Status is Cancelled",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='cancel'].btn-primary",
                extra_trigger: "body:not(:has(.modal))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/12-restart.md
    tour.register(
        "ssi_promotion_promotion_code_restart",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Remove the default state filter facet from the
            // search bar. The default view (search_default_dom_draft/
            // confirm/open on promotion_code_action) only shows Draft,
            // Waiting for Approval, and In Progress documents -- a
            // Cancelled document like this tour's fixture stays hidden
            // until that facet is removed. Here it is the very first
            // interaction after navigating in, so explicitly wait for
            // one of the default-filtered rows (TOUR-PC-EDIT, a Draft
            // fixture) before touching anything in the search bar --
            // this is now redundant with the stale-marker remount gate
            // in openCodesMenuSteps above (both key on the same row),
            // kept as an explicit, self-documenting checkpoint for this
            // Flow step rather than removed.
            {
                content: "Default-filtered list has settled",
                trigger: ".o_data_row:contains(TOUR-PC-EDIT)",
                extra_trigger: ".o_list_view",
                run: function () {
                    // Assertion only.
                },
            },
            //
            // Candidate-1 (a fresh `$(selector)` lookup via
            // `actions.click()` on the facet-remove icon) was tried
            // and falsified: 5x local `test-module-ci-local.sh` runs
            // showed the click step itself always `succeeded`, yet
            // the gate below still failed 4 of 5 times -- the click
            // lands, but the facet DOM is never refreshed (see issue
            // #78 comments for the full trace). Root cause: the
            // "Open the Codes menu" step reloads the SAME action that
            // was already loaded when the app opened
            // (`promotion_code_menu` is the first child of
            // `menu_root_promotion`, so `promotion_code_action` loads
            // twice), so the "list has settled" gate above is
            // tautological -- it can pass on the FIRST load's DOM,
            // before the second load's SearchBar re-render finishes,
            // leaving the facet-remove click racing that re-render.
            // Per odoo-development-ui-test's patterns-advanced-
            // gotchas.md §S, a facet built from `search_default_dom_*`
            // has no "operation settled" signal available to gate the
            // facet-remove click on, so idiom A (clicking the facet's
            // remove icon) is not safe here regardless of how fresh
            // the selector lookup is. Idiom B (toggling each active
            // filter off through the Filters dropdown) has zero
            // recorded failures across 63 files / 18 repos and does
            // not depend on the facet chip's own re-render timing.
            {
                content: "Open the Filters menu",
                trigger: ".o_search_options .o_filter_menu button",
            },
            {
                // Label = the filter's `string` in
                // ssi_transaction_mixin's mixin_transaction_views.xml
                // (dom_draft).
                content: "Toggle off the Draft filter",
                trigger: ".o_filter_menu .dropdown-item:contains(Draft)",
                run: function () {
                    this.$anchor[0].click();
                },
            },
            {
                // Label = ssi_transaction_confirm_mixin's
                // mixin_transaction_confirm_templates.xml (dom_confirm).
                content: "Toggle off the Waiting for Approval filter",
                trigger:
                    ".o_filter_menu .dropdown-item:contains(" + "Waiting for Approval)",
                run: function () {
                    this.$anchor[0].click();
                },
            },
            {
                // Label = ssi_transaction_open_mixin's
                // mixin_transaction_open_templates.xml (dom_open).
                content: "Toggle off the In Progress filter",
                trigger: ".o_filter_menu .dropdown-item:contains(In Progress)",
                run: function () {
                    this.$anchor[0].click();
                },
            },
            {
                // Gerbang: don't just assume the clicks "took" -- wait
                // for the facet chip to actually be gone before relying
                // on the list containing every state. Kept unchanged
                // from candidate-1 -- this gate works correctly and is
                // mandatory (odoo-development-ui-test, patterns.md §S).
                content: "Default state filter is removed",
                trigger: "body:not(:has(.o_searchview_facet))",
                run: function () {
                    // Assertion only.
                },
            },

            // Flow 3 — Open the record to restart.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-RESTART) .o_data_cell:first",
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
            //
            // Gerbang modal-tertutup (patterns.md §K) -- same
            // FieldWrapper re-render race as the confirm tour above.
            {
                content: "Status is Draft",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='draft'].btn-primary",
                extra_trigger: "body:not(:has(.modal))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/13-reset-number.md
    tour.register(
        "ssi_promotion_promotion_code_reset_number",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record whose document number will be
            // reset. The Pre-Condition fixture carries the manually
            // assigned number "TOUR-PC-RESET-MANUAL".
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-RESET) .o_data_cell:first",
                extra_trigger: ".o_list_view",
            },
            {
                content: "Record is open with its manual document number",
                trigger:
                    ".oe_title .o_field_widget[name='display_name']" +
                    ":contains(TOUR-PC-RESET-MANUAL)",
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
            //
            // Gerbang modal-tertutup (patterns.md §K) -- same
            // FieldWrapper re-render race as the confirm tour above;
            // display_name is itself a field widget re-rendered by
            // the reset RPC's response.
            {
                content: "Document number returns to /",
                trigger: ".oe_title .o_field_widget[name='display_name']:contains(*)",
                extra_trigger: "body:not(:has(.modal))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );

    // IK: docs/promotion_code/14-restart-approval.md
    tour.register(
        "ssi_promotion_promotion_code_restart_approval",
        {
            test: true,
            url: "/web",
        },
        [].concat(openCodesMenuSteps, [
            // Flow 2 — Open the record to restart the approval
            // process for.
            {
                content: "Open the record",
                trigger: ".o_data_row:contains(TOUR-PC-REAPPROVAL) .o_data_cell:first",
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
            // Gerbang modal-tertutup (patterns.md §K) on both remaining
            // assertions too: this tour was an observed victim of the
            // same intermittent FieldWrapper race (see #77) even
            // though the tab click above already carries the gate --
            // the modal-close race window can still be open by the
            // time these two widgets (approval_ids, statusbar) finish
            // their own re-render from the reload RPC.
            {
                content: "The approval process has been rebuilt",
                trigger: ".o_field_widget[name='approval_ids'] .o_data_row",
                extra_trigger: "body:not(:has(.modal))",
                run: function () {
                    // Assertion only.
                },
            },
            {
                content: "Status is still Waiting for Approval",
                trigger:
                    ".o_statusbar_status .o_arrow_button[data-value='confirm'].btn-primary",
                extra_trigger: "body:not(:has(.modal))",
                run: function () {
                    // Assertion only.
                },
            },
        ])
    );
});
