/* Copyright 2017 Jairo Llopis <jairo.llopis@tecnativa.com>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

 odoo.define("website_sale_require_legal.tour", function (require) {
    "use strict";

    var core = require("web.core");
    var tour = require("web_tour.tour");

    var steps = [
        {
            trigger: "a:contains('ipod')",
        },
        {
            trigger: "#add_to_cart",
        },
        {
            trigger: ".btn-primary:contains('process checkout')",
        },
        {
            trigger: ".btn-primary:contains('next')",
        },
        {
            trigger: ".form-group.has-error #accepted_legal_terms",
        },
        {
            trigger: ".btn-primary:contains('next')",
        },
        {
            trigger: ".form-group:not(.has-error) #accepted_legal_terms",
        },
    ];

    tour.register(
        "website_sale_require_legal",
        {
            url: "/shop?debug=assets",
            test: true,
        },
        steps
    );

    return {
        steps: steps,
    }
});
