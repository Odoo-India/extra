odoo.define('groupme.network.new', function (require) {
    "use strict";
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var website = require('website.website');

    var _t = core._t;

    $(document).ready(function () {
        //website.add_template_file('/groupme/static/src/xml/groupme_network_new.xml');
        var NetworkDialog = Widget.extend({
            template: 'groupme.network_new',
            events: {
                'hidden.bs.modal': 'destroy',
                'click button.save': 'save',
                'click button[data-dismiss="modal"]': 'cancel'            
            },
            init: function (el) {
                console.log("====== init =========");
                this.index_content = "";
            },
            start: function () {
                console.log("====== Start =========");
                this.$el.modal({
                    backdrop: 'static'
                });
                this.set_category_id();
                this.set_tag_ids();
            },
            display_alert: function (message) {                
                this.$('.alert-warning').remove();
                $('<div class="alert alert-warning" role="alert">' + message + '</div>').insertBefore(this.$('form'));
            },
            select2_wrapper: function (tag, multi, fetch_fnc) {
            return {
                width: '100%',
                placeholder: tag,
                allowClear: true,
                formatNoMatches: _.str.sprintf(_t("No matches found. Type to create new %s"), tag),
                multiple: multi,
                selection_data: false,
                fetch_rpc_fnc : fetch_fnc,
                formatSelection: function (data) {
                    if (data.tag) {
                        data.text = data.tag;
                    }
                    return data.text;
                },
                createSearchChoice: function (term) {
                    return {
                        id: _.uniqueId('tag_'),
                        create: true,
                        tag: term,
                        text: _.str.sprintf(_t("Create New %s '%s'"), tag, term)
                    };
                },
                fill_data: function (query, data) {
                    var that = this,
                        tags = {results: []};
                    _.each(data, function (obj) {
                        if (that.matcher(query.term, obj.name)) {
                            tags.results.push({id: obj.id, text: obj.name });
                        }
                    });
                    query.callback(tags);
                },
                query: function (query) {
                    var that = this;
                    // fetch data only once and store it
                    if (!this.selection_data) {
                        this.fetch_rpc_fnc().then(function (data) {
                            that.fill_data(query, data);
                            that.selection_data = data;
                        });
                    } else {
                        this.fill_data(query, this.selection_data);
                    }
                }
            };
        },
        // Category management from select2
        set_category_id: function () {
            var self =  this;
            $('#category_id').select2(this.select2_wrapper(_t('Category'), false,
                function () {
                    return ajax.jsonRpc("/web/dataset/call_kw", 'call', {
                        model: 'groupme.network.category',
                        method: 'search_read',
                        args: [],
                        kwargs: {
                            fields: ['name'],
                            context: website.get_context()
                        }
                    });
                }));
        },
        get_category_id: function () {
            var value = $('#category_id').select2('data');
            if (value && value.create) {
                return [0, {'name': value.text}];
            }
            return [value ? value.id : null];
        },
        set_tag_ids: function () {
            $('#tag_ids').select2(this.select2_wrapper(_t('Tags'), true, function () {
                return ajax.jsonRpc("/web/dataset/call_kw", 'call', {
                    model: 'groupme.network.tag',
                    method: 'search_read',
                    args: [],
                    kwargs: {
                        fields: ['name'],
                        context: website.get_context()
                    }
                });
            }));
        },
        get_tag_ids: function () {
            var res = [];
            _.each($('#tag_ids').select2('data'),
                function (val) {
                    if (val.create) {
                        res.push([0, 0, {'name': val.text}]);
                    } else {
                        res.push([4, val.id]);
                    }
                });
            return res;
        },
        // Values and save
        get_value: function () {
            var canvas = this.$('#data_canvas')[0],
                values = {
                    'name': this.$('#name').val(),
                    'code': this.$('#code').val(),
                    'tag_ids': this.get_tag_ids(),
                    'category_id': this.get_category_id()
                };
            return values;
        },
        validate: function () {
            this.$('.form-group').removeClass('has-error');
            if (!this.$('#name').val()) {
                this.$('#name').closest('.form-group').addClass('has-error');
                return false;
            }
            if (!this.$('#code').val()) {
                this.$('#code').closest('.form-group').addClass('has-error');
                return false;
            }

            return true;
        },
        save: function (ev) {
            var self = this;
            if (this.validate()) {
                var values = this.get_value();
                if ($(ev.target).data('published')) {
                    values.website_published = true;
                }
                $('.oe_network_creating').show();
                $('.modal-footer, .modal-body').hide();
                ajax.jsonRpc("/networks/network/add_network", 'call', values).then(function (data) {
                    if (data.error) {
                        self.display_alert(data.error);
                        $('.oe_network_creating').hide();                
                        $('.modal-footer, .modal-body').show();
                    } else {
                        window.location = data.url;
                    }
                });
            }
        },
        cancel: function () {
            this.trigger("cancel");
        },
        });
 
 
        $('.oe_js_network_new').on('click', function () {
            website.add_template_file('/groupme/static/src/xml/groupme_network_new.xml').done(function() {
                    var $net_new = new NetworkDialog(self).appendTo(document.body);
                    $('#s2id_tag_ids').addClass('form-control');

                    $('#s2id_category_id').addClass('form-control');
                    $('#s2id_category_id a').css('height', '30px').children('span').css('margin-top','2px');

                    $('#code').on('input',function(){
                        var resss= ajax.jsonRpc("/web/dataset/call_kw", 'call', {
                            model: 'groupme.network',
                            method: 'search_read',
                            args: [],
                            kwargs: {
                                fields: ['name'],
                                domain: [['code', '=', self.code.value]],
                                context: website.get_context()
                            }
                        }).then(function (data) {
                            if(data.length!=0){
                                $("#code").closest('.form-group').removeClass('has-success').addClass('has-error');
                                $("#codestatus").removeClass("fa-check").addClass("fa-times");
                                $("#ErrorMessages").css("display", "block");
                            }else{
                                $("#code").closest('.form-group').removeClass('has-error').addClass('has-success');
                                $("#codestatus").removeClass("fa-times").addClass("fa-check");
                                $("#ErrorMessages").css("display", "none");
                            }
                         });
                    });
            });
        });

    });
});
