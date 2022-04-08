odoo.define('erp_oa_addons.button', function (require){
    "use strict";
    var rpc = require("web.rpc");
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');


    var ImportViewMixin = {
        /**
         * @override
         */
        init: function (viewInfo, params) {
            var importEnabled = 'import_enabled' in params ? params.import_enabled : true;
            this.controllerParams.importEnabled = importEnabled;
        },
    };
    var ImportControllerMixin = {
        /**
         * @override
         */
        init: function (parent, model, renderer, params) {
            this.importEnabled = params.importEnabled;
        },
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
        /**
         * Adds an event listener on the import button.
         *
         * @private
         */
        _bindImport: function () {
            if (!this.$buttons) {
                return;
            }
            var self = this;
            /*业务ID*/
            this.$buttons.on('click', '.o_button_erp2oa_ywid', function () {
                rpc.query({
                    model: 'erp2oa.erp.ljbm',
                    method: 'get_erp_ywid',
                    args: [""]
                }).then(function (action_dict) {
                    self.trigger_up('reload');
                   // self.do_action(
                   //     action_dict
                   // )
                });
            });

            /*业务模块*/
            this.$buttons.on('click', '.o_button_erp2oa_models', function () {
                // var self = this;
                // var records = self.getSelectedIds();
                // console.log('--records--');
                // console.log(records);
                rpc.query({
                    model: 'erp2oa.erp.models',
                    method: 'get_erp2oa_models',
                    args: [""]
                }).then(function (action_dict) {
                   self.trigger_up('reload');
                });
            });
            /*表字段*/
            this.$buttons.on('click', '.o_button_erp2oa_table_field', function () {
                // var self = this;
                // var records = self.getSelectedIds();
                // console.log('--records--');
                // console.log(records);
                rpc.query({
                    model: 'erp2oa.erp.table',
                    method: 'get_erp2oa_table_field',
                    args: [""]
                }).then(function (action_dict) {
                   // self.trigger_up('reload');
                   self.do_action(
                       action_dict
                   )
                });
            });
        }
    };
    ListView.include({
        init: function () {
            this._super.apply(this, arguments);
            ImportViewMixin.init.apply(this, arguments);
        },
    });
    ListController.include({
        init: function () {
            this._super.apply(this, arguments);
            ImportControllerMixin.init.apply(this, arguments);
        },
        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------
        /**
         * Extends the renderButtons function of ListView by adding an event listener
         * on the import button.
         *
         * @override
         */
        renderButtons: function () {
            this._super.apply(this, arguments);
            ImportControllerMixin._bindImport.call(this);

            if (this.modelName=="erp2oa.erp.ljbm" && this.$buttons){
                this.$buttons.find(".o_button_erp2oa_ywid").css("display","inline-block");
            }
            if (this.modelName=="erp2oa.erp.models" && this.$buttons){
                this.$buttons.find(".o_button_erp2oa_models").css("display","inline-block");
            }
            if (this.modelName=="erp2oa.erp.table" && this.$buttons){
                this.$buttons.find(".o_button_erp2oa_table_field").css("display","inline-block");
            }
        }
    });
}
);