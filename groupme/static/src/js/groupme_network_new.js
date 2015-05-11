odoo.define('groupme.network.new', function(require) {
    "use strict";
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var website = require('website.website');
    var network = require('groupme.network');

    var _t = core._t;

    $(document).ready(function() {

        var url = window.location.href;
        var defaulttab = url.substring(url.indexOf('#'), url.length);
        $('.nav-tabs a[href="' + defaulttab + '"]').tab('show');

        var NetworkDialog = Widget.extend({
            template: 'groupme.network_new',
            events: {
                'hidden.bs.modal': 'destroy',
                'click button.save': 'save',
                'click button[data-dismiss="modal"]': 'cancel'
            },
            init: function(el) {
                this.index_content = "";
            },
            start: function() {
                var self = this;
                self.$el.modal({
                    backdrop: 'static'
                });
                self.set_category_id();
                self.set_tag_ids();
                self.checkCode();
            },
            display_alert: function(message) {
                var self = this;
                self.$('.alert-warning').remove();
                $('<div class="alert alert-warning" role="alert">' + message + '</div>').insertBefore(this.$('form'));
            },
            checkCode: function() {
                var codecheckResponse = function(data) {
                    $("#codestatus").removeClass("fa-spin");
                    if (data.length != 0) {
                        $("#code").closest('.form-group').removeClass('has-success').addClass('has-error');
                        $("#codestatus").removeClass("fa-check").addClass("fa-times");
                        $("#codestatus").addClass("fa-spin");
                    } else {
                        $("#code").closest('.form-group').removeClass('has-error').addClass('has-success');
                        $("#codestatus").removeClass("fa-times").addClass("fa-check");
                    }
                }
                var codecheckRequest = function() {
                    ajax.jsonRpc("/web/dataset/call_kw", 'call', {
                        model: 'groupme.network',
                        method: 'search_read',
                        args: [],
                        kwargs: {
                            fields: ['name'],
                            domain: [
                                ['code', '=', self.code.value.toLowerCase()]
                            ],
                            context: website.get_context()
                        }
                    }).then(codecheckResponse);
                }
                $("#code").on('input', codecheckRequest);
            },
            select2_wrapper: function(tag, multi, fetch_fnc) {
                return {
                    width: '100%',
                    placeholder: tag,
                    allowClear: true,
                    formatNoMatches: _.str.sprintf(_t("No matches found in %s"), tag),
                    multiple: multi,
                    selection_data: false,
                    fetch_rpc_fnc: fetch_fnc,
                    formatSelection: function(data) {
                        if (data.tag) {
                            data.text = data.tag;
                        }
                        return data.text;
                    },
                    createSearchChoice: function(term) {
                        if (tag != "Category")
                            return {
                                id: _.uniqueId('tag_'),
                                create: true,
                                tag: term,
                                text: _.str.sprintf(_t("Create New %s '%s'"), tag, term)
                            };
                    },
                    fill_data: function(query, data) {
                        var that = this,
                            tags = {
                                results: []
                            };
                        _.each(data, function(obj) {
                            if (that.matcher(query.term, obj.name)) {
                                tags.results.push({
                                    id: obj.id,
                                    text: obj.name
                                });
                            }
                        });
                        query.callback(tags);
                    },
                    query: function(query) {
                        var that = this;
                        // fetch data only once and store it
                        if (!this.selection_data) {
                            this.fetch_rpc_fnc().then(function(data) {
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
            set_category_id: function() {
                var self = this;
                $('#category_id').select2(this.select2_wrapper(_t('Category'), false,
                    function() {
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
            get_category_id: function() {
                var value = $('#category_id').select2('data');
                if (value && value.create) {
                    return [0, {
                        'name': value.text
                    }];
                }
                return [value ? value.id : null];
            },
            set_tag_ids: function() {
                $('#tag_ids').select2(this.select2_wrapper(_t('Tags'), true, function() {
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
            get_tag_ids: function() {
                var res = [];
                _.each($('#tag_ids').select2('data'),
                    function(val) {
                        if (val.create) {
                            res.push([0, 0, {
                                'name': val.text
                            }]);
                        } else {
                            res.push([4, val.id]);
                        }
                    });

                return res;
            },
            // Values and save
            get_value: function() {
                var self = this;
                var canvas = self.$('#data_canvas')[0],
                    values = {
                        'name': self.$('#name').val(),
                        'code': self.$('#code').val(),
                        'tag_ids': self.get_tag_ids(),
                        'category_id': self.get_category_id()
                    };
                return values;
            },
            validate: function() {
                var self = this;
                self.$('.form-group').removeClass('has-error');
                if (!self.$('#name').val()) {
                    self.$('#name').closest('.form-group').addClass('has-error');
                    return false;
                }
                if (!self.$('#code').val()) {
                    self.$('#code').closest('.form-group').addClass('has-error');
                    return false;
                }
                if ($("#codestatus").hasClass("fa-times")) {
                    $("#codeErrorMessage").text("Code Already Exists").css("display", "block");
                    return false;
                } else {
                    $("#codeErrorMessage").css("display", "none");
                }
                return true;
            },
            save: function(ev) {
                var self = this;
                if (self.validate()) {
                    var values = self.get_value();
                    if ($(ev.target).data('published')) {
                        values.website_published = true;
                    }
                    $('.oe_network_creating').show();
                    $('.modal-footer, .modal-body').hide();
                    ajax.jsonRpc("/networks/network/add_network", 'call', values).then(function(data) {
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
            cancel: function() {
                this.trigger("cancel");
            },
            destroy: function() {

            }
        });
        var networkdialog = false;
        $('.oe_js_network_new').on('click', function() {
            website.add_template_file('/groupme/static/src/xml/groupme_network_new.xml').done(function() {
                // var $net_new = new NetworkDialog(self).appendTo(document.body);
                if (!networkdialog)
                    networkdialog = new NetworkDialog(self);
                network.page_widgets['network'] = networkdialog.appendTo(document.body);
                $('#s2id_tag_ids').addClass('form-control');

                $('#s2id_category_id').addClass('form-control');
                $('#s2id_category_id a').css('height', '30px').children('span').css('margin-top', '2px');
            });
        });
        var InvitationDialog = Widget.extend({
            template: 'groupme.invite',
            events: {
                'click button.save': 'save',
                'click button[data-dismiss="modal"]': 'cancel',
                'input email_ids': 'set_email_ids'
            },
            init: function(el, net_id) {
                this.network_id = net_id;
                this.index_content = "";
            },
            start: function() {
                this.$el.modal({
                    // backdrop: 'static'
                });
                this.set_email_ids();
            },
            display_alert: function(message) {
                this.$('.alert-warning').remove();
                $('<div class="alert alert-warning" role="alert">' + message + '</div>').insertBefore(this.$('form'));
            },
            select2_wrapper: function(tag, multi, fetch_fnc) {
                return {
                    width: '100%',
                    placeholder: tag,
                    allowClear: true,
                    formatNoMatches: _.str.sprintf(_t("No matches found. Type to create new %s"), tag),
                    multiple: multi,
                    selection_data: false,
                    fetch_rpc_fnc: fetch_fnc,
                    formatSelection: function(data) {
                        if (data.tag) {
                            data.text = data.tag;
                        }
                        return data.text;
                    },
                    createSearchChoice: function(term) {
                        return {
                            id: _.uniqueId('tag_'),
                            create: true,
                            tag: term,
                            text: _.str.sprintf(_t("Create New %s '%s'"), tag, term)
                        };
                    },
                    fill_data: function(query, data) {
                        var that = this,
                            tags = {
                                results: []
                            };
                        _.each(data, function(obj) {
                            var joinMsg = obj.name + ' <' + obj.email + '>';
                            if (that.matcher(query.term, joinMsg)) {

                                tags.results.push({
                                    id: obj.id,
                                    text: joinMsg
                                });
                            }
                        });
                        query.callback(tags);
                    },
                    query: function(query) {
                        var that = this;
                        // fetch data only once and store it
                        if (!this.selection_data) {
                            this.fetch_rpc_fnc().then(function(data) {
                                that.fill_data(query, data);
                                that.selection_data = data;
                            });
                        } else {
                            this.fill_data(query, this.selection_data);
                        }
                    }
                };
            },
            set_email_ids: function() {
                $('#email_ids').select2(this.select2_wrapper(_t('Email'), true, function() {
                    return ajax.jsonRpc("/web/dataset/call_kw", 'call', {
                        model: 'res.partner',
                        method: 'search_read',
                        args: [],
                        kwargs: {
                            fields: ['name', 'email'],
                            context: website.get_context()
                        }
                    });
                }));
            },
            get_email_ids: function() {
                var res = [];
                _.each($('#email_ids').select2('data'),
                    function(val) {
                        if (val.create) {
                            res.push([0, 0, {
                                'name': val.text
                            }]);
                        } else {
                            res.push([4, val.id]);
                        }
                    });

                return res;
            },

            // Values and save
            get_value: function() {
                var canvas = this.$('#data_canvas')[0],
                    values = {
                        'network_id': this.network_id,
                        'email_ids': this.get_email_ids()
                    };
                return values;
            },
            validate: function() {
                this.$('.form-group').removeClass('has-error');
                if (!this.$('#email_ids').val()) {
                    this.$('#email_ids').closest('.form-group').addClass('has-error');
                    return false;
                }
                return true;
            },
            save: function(ev) {
                var self = this;
                if (self.validate()) {
                    var values = self.get_value();

                    $('.oe_people_inviting').show();
                    $('.modal-footer, .modal-body').hide();
                    ajax.jsonRpc("/networks/network/invite_people", 'call', values).then(function(data) {
                        if (data.error) {
                            self.display_alert(data.error);
                            $('.oe_people_inviting').hide();
                            $('.modal-footer, .modal-body').show();
                        } else {
                            if (data.result == "true") {
                                $('.modal').modal('hide');
                            }
                        }
                    });
                }
            },
            cancel: function() {
                this.trigger("cancel");
            }
        });
        var invitedialogloaded = false;
        var network_id = false;
        var invitedialog = false;
        $('.oe_js_invite').on('click', function() {
            $('.nav-tabs a[href="#members"]').tab('show');
            if (!invitedialogloaded) {
                website.add_template_file('/groupme/static/src/xml/groupme_network_invite.xml').done(function() {
                    network_id = $('.oe_js_invite').data('network_id');
                    invitedialog = new InvitationDialog(self, network_id);
                    invitedialog.appendTo(document.body);
                });
                invitedialogloaded = !invitedialogloaded;
            } else {
                invitedialog.appendTo(document.body);
            }
        });
        $('#joingroup').on('click', function() {
            $('#joingroupmodal').modal("show");
        });
        $('#joingroupbutton').on('click', function() {
            var network_id = $('.oe_js_joingroup').data('network_id');
            var values = {
                'email_id': $('#email').val()
            };
            $("#resultErrorMessage").text("").css("display", "none");
            $('.oe_network_joining').show();
            return ajax.jsonRpc("/networks/network/joingroup/" + network_id, 'call', values).then(function(data) {
                $('.oe_network_joining').hide();
                if (data.result) {
                    $('#joingroupmodal').modal('hide');
                    $('.nav-tabs a[href="#members"]').tab('show');
                    var url = window.location.href;
                    url = url.substring(0, url.indexOf('#')) + "#members";
                    window.location.replace(url);
                    location.reload();
                } else {
                    $("#resultErrorMessage").text("No such User.").css("display", "block");
                }
            });
        });
        $('.removeMember').on('click', function() {
            var memberid = $(this).data('memberid');
            var network_id = $('.oe_js_joingroup').data('network_id');
            return ajax.jsonRpc("/networks/network/group/" + network_id + "/" + memberid, 'call').then(function(data) {
                if (data.result) {
                    $('#joingroupmodal').modal('hide');
                    $('.nav-tabs a[href="#members"]').tab('show');
                    var url = window.location.href;
                    url = url.substring(0, url.indexOf('#')) + "#members";
                    window.location.replace(url);
                    location.reload();
                } else {
                    $("#resultErrorMessage").text("No such User.").css("display", "block");
                }
            });
        });
    });
});