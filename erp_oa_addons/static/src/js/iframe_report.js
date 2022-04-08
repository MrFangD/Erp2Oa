odoo.define('roke_mes_sync_PSERP.iframe_template', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');

var HomePageWidget = AbstractAction.extend({
    template: 'roke_mes_sync_PSERP.plc_data',
    events: {  },

});

core.action_registry.add('roke_mes_sync_PSERP_iframe_template', HomePageWidget);

return HomePageWidget;

});
