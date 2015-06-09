odoo.define('groupme.network.new', function(require) {
    "use strict";
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var website = require('website.website');
    var network = require('groupme.network');

    var _t = core._t;
    var QWeb = core.qweb;

    $(document).ready(function() {

        var url = window.location.href;
        var defaulttab = url.substring(url.indexOf('#'), url.length);
        $('.nav-tabs a[href="' + defaulttab + '"]').tab('show');

        function redirectUrlWithTab(tab) {
            var url = window.location.href;
            if (url.indexOf('#') != -1)
                url = url.substring(0, url.indexOf('#') + 1) + tab;
            else
                url = url + "#" + tab;
            //window.location.hash=tab
            window.location = url;
            location.reload();
        }


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
            getVisibility: function() {
                return $("#visibility").val();
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
                        'visibility': self.getVisibility(),
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
                    ajax.jsonRpc("/networks/network/create", 'call', values).then(function(data) {
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
                    ajax.jsonRpc("/networks/network/invite", 'call', values).then(function(data) {
                        if (!data.result) {
                            self.display_alert(data.error);
                            $('.oe_people_inviting').hide();
                            $('.modal-footer, .modal-body').show();
                        } else {
                            //if (data.result == "true") {
                            $('.modal').modal('hide');
                            location.reload();
                            //}
                        }
                    });
                }
            },
            cancel: function() {
                this.trigger("cancel");
            }
        });
        var JoinDialog = Widget.extend({
            template: 'groupme.joingroup',
            events: {
                'click button.save': 'save',
                'click button[data-dismiss="modal"]': 'cancel',
            },
            init: function(el, net_id) {
                this.network_id = net_id;
                this.index_content = "";
                // $("#joingroupform").attr('action', '/networks/network/joingroup/' + this.network_id);
            },
            start: function() {
                this.$el.modal({
                    // backdrop: 'static'
                });
            },
            display_alert: function(message) {
                this.$('.alert-warning').remove();
                $('<div class="alert alert-warning" role="alert">' + message + '</div>').insertBefore(this.$('form'));
            },

            // Values and save
            get_value: function() {
                var canvas = this.$('#data_canvas')[0],
                    values = {
                        'network_id': this.network_id,
                        'email_id': this.get_email_id()
                    };
                return values;
            },
            get_email_id: function() {
                return this.$('#email').val();
            },
            validate: function() {

                this.$('.form-group').removeClass('has-error');
                if (!this.$('#email').val()) {
                    this.$('#email').closest('.form-group').addClass('has-error');
                    return false;
                }
                return true;
            },
            save: function(ev) {

                var self = this;
                if (self.validate()) {
                    var values = self.get_value();

                    $('.oe_network_joining').show();
                    $('.modal-footer, .modal-body').hide();

                    ajax.jsonRpc("/networks/network/joingroup/" + this.network_id, 'call', values).then(function(data) {

                        $('.oe_network_joining').hide();
                        if (data.result) {
                            $('.modal').modal('hide');
                            redirectUrlWithTab("members");
                            // var url = window.location.href;
                            // url = url.substring(0, url.indexOf('#'));
                            // window.location = url + "#members";
                            // location.reload();
                        } else {
                            self.display_alert(data.error);
                            $('.oe_people_inviting').hide();
                            $('.modal-footer, .modal-body').show();
                        }
                    });
                }
            },
            cancel: function() {
                this.trigger("cancel");
            }
        });

        // ImportDialog
        var ImportDialog = Widget.extend({
            template: 'groupme.importcsvmembers',
            events: {
                'click button.save': 'save',
                'change input:file': 'previewCSV',
                'click button[data-dismiss="modal"]': 'cancel',
            },
            init: function(el, net_id) {
                this.network_id = net_id;
                this.index_content = "";
                this.isCSVValid = false;
            },
            start: function() {
                this.$el.modal({
                    // backdrop: 'static'
                });
                $("#importmembersform").prop('action', "/networks/network/importmembers/" + this.network_id);
            },
            display_alert: function(message) {
                this.$('.alert-warning').remove();
                $('<div class="alert alert-warning" role="alert">' + message + '</div>').insertBefore(this.$('form'));
            },
            // Values and save
            get_value: function() {
                var canvas = this.$('#data_canvas')[0],
                    values = {
                        'network_id': this.network_id,
                        'email_id': this.get_email_id()
                    };
                return values;
            },
            get_email_id: function() {
                return this.$('#email').val();
            },
            previewCSV: function() {
                var self = this;
                if (!self.validate()) {
                    return false;
                }
                //clear table data or alerts,if any
                $("#tabledata > tbody").html("");
                $("#tabledata").removeClass("hidden");
                self.$('.alert-warning').remove();
                var CSVValid = true;
                var reader = new FileReader();
                reader.readAsText(document.getElementById('upload').files[0]);
                reader.onload = function(event) {
                    var csvData = event.target.result;
                    var html = "";
                    var rows = csvData.split("\n");
                    rows = rows.slice(1, rows.length);
                    rows.forEach(function getvalues(ourrow) {
                        html += "<tr><td></td>";
                        var columns = ourrow.split(",");
                        for (var i = 0; i <= columns.length - 1; i++) {
                            html += "<td>" + columns[i] + "</td>";
                        };
                        var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
                        var isEmailValid = regex.test(columns[1]);
                        if (i != 2 && !isEmailValid) {
                            CSVValid = false;
                            return false;
                        }
                        html += "<td> </td>";
                        html += "</tr>";
                    });
                    if (!CSVValid) {
                        self.isCSVValid = CSVValid;
                        self.display_alert("Invalid CSV Format");
                        $("#tabledata").addClass("hidden");
                        return false;
                    } else
                        self.isCSVValid = CSVValid;
                    $('#tabledata').append(html);
                };
                reader.onerror = function() {
                    self.display_alert("Invalid CSV Format");
                };
            },
            validate: function() {
                this.$('.form-group').removeClass('has-error');
                if (!this.$('#upload').val()) {
                    this.$('#upload').closest('.form-group').addClass('has-error');
                    return false;
                }
                return true;
            },
            save: function(ev) {
                var self = this;
                if (self.validate() && self.isCSVValid) {
                    var values = self.get_value();
                    $('.oe_members_upload_loading').show();
                    $('.modal-footer, .modal-body').hide();
                    // $("#importmembersform").submit();
                    var formData = new FormData();
                    formData.append('file', document.getElementById('upload').files[0]);
                    $.ajax({
                        url: "/networks/network/importmembers/" + this.network_id,
                        data: formData,
                        type: 'POST',
                        contentType: false,
                        processData: false,
                        error: function(jqXHR, textStatus, errorMessage) {
                            $(".fa-spin").remove();
                            $("#importStatus").text("Import failed - " + errorMessage);
                        },
                        success: function(data) {
                            $(".fa-spin").remove();
                            $('.nav-tabs a[href="#members"]').tab('show');
                            $("#importStatus").text("Import Completed - " + data);
                            window.location.hash = "members"
                            location.reload();
                        }
                    });
                }
            },
            cancel: function() {}
        });

        var invitedialogloaded = false;
        var network_id = $('#oe_networkid').data('network_id');
        var invitedialog = false;

        // var approverequest = new AjaxJsonRPC($(".approveButton"), "/networks/network/" + network_id + "/approverequest/");
        $("#sendrequest").on('click', function() {
            var that = this;
            return ajax.jsonRpc("/networks/network/sendrequest/" + network_id, 'call').then(function(data) {
                if (data.status) {
                    $(that).text(data.status);
                    $(that).prop('disabled', true);
                } else {
                    $("#resultErrorMessage").text("No such User.").css("display", "block");
                }
            });
        });

        $("#cancelrequest").on('click', function() {
            var that = this;
            return ajax.jsonRpc("/networks/network/canceljoinrequest/" + network_id, 'call').then(function(data) {
                if (data.status) {
                    $(that).text(data.status);
                    $(that).prop('disabled', true);
                } else {
                    console.log('');
                    $("#resultErrorMessage").text("No such User.").css("display", "block");
                }
            });
        });
        $('.oe_js_invite').on('click', function() {
            $('.nav-tabs a[href="#members"]').tab('show');
            if (!invitedialogloaded) {
                website.add_template_file('/groupme/static/src/xml/groupme_network_invite.xml').done(function() {
                    invitedialog = new InvitationDialog(self, network_id);
                    invitedialog.appendTo(document.body);
                });
                invitedialogloaded = !invitedialogloaded;
            } else {
                invitedialog.appendTo(document.body);
            }
        });

        var joind = false;
        $('#joingroup').on('click', function() {
            if (!joind) {
                website.add_template_file('/groupme/static/src/xml/groupme_joingroup.xml').done(function() {
                    joind = new JoinDialog(self, network_id);
                    joind.appendTo(document.body);
                });
            } else
                joind.appendTo(document.body);
        });
        $('.removeMember').on('click', function() {
            var that = this;
            var memberid = $(this).data('memberid');
            return ajax.jsonRpc("/networks/network/removemember/" + network_id + "/" + memberid, 'call').then(function(data) {
                if (data.result) {
                    $(that).closest(".col-xs-4").remove();
                } else {
                    $("#resultErrorMessage").text("No such User.").css("display", "block");
                }
            });
        });
        var importd = false;
        $('.importbutton').on('click', function() {
            if (!importd) {
                website.add_template_file('/groupme/static/src/xml/groupme_importcsvmembers.xml').done(function() {
                    importd = new ImportDialog(self, network_id);
                    importd.appendTo(document.body);
                });
            } else
                importd.appendTo(document.body);
        });
        $(".follower_card").hover(function() {
            $(this).children(".dropdown").removeClass("hidden");
            $(this).children(".dropdown").click();
            $(this).children(".userrights").attr("style", "visibility:visible");
            $(this)
        }, function() {
            $(this).children(".dropdown").click();
            $(this).children(".dropdown").addClass("hidden");
            $(this).children(".userrights").attr("style", "visibility:hidden");
        });
        $(".approveButton").on('click', function() {
            var that = this;
            var values = {
                'userid': $(this).data('userid'),
                'emailid': $(this).data('emailid')
            };
            return ajax.jsonRpc("/networks/network/" + network_id + "/approverequest/", 'call', values).then(function(data) {
                if (data.status) {
                    $(that).text(data.status);
                    $(that).prop('disabled', true);
                    $(that).closest('tr').fadeOut('2000');
                } else {
                    $("#resultErrorMessage").text("No such User.").css("display", "block");
                }
            });
        });

        $(".ignoreButton").on('click', function() {
            var that = this;
            var values = {
                'userid': $(this).data('userid'),
                'emailid': $(this).data('emailid')
            };
            return ajax.jsonRpc("/networks/network/canceljoinrequest/" + network_id, 'call', values).then(function(data) {
                if (data.status) {
                    $(that).text(data.status);
                    $(that).prop('disabled', true);
                    $(that).closest('tr').fadeOut('2000');
                } else {
                    $("#resultErrorMessage").text("No such User.").css("display", "block");
                }
            });
        });

        $(".rights").on('click', function() {
            $(this).addClass("fa-spinner fa-spin");
            var that = this;
            var values = {
                'rights': $(this).data('rights')
            };
            var memberid = $(this).data('memberid');
            return ajax.jsonRpc("/networks/network/" + network_id + "/assignrights/" + memberid, 'call', values).then(function(data) {
                if (data.status) {
                    $(that).removeClass("fa-spinner fa-spin");
                } else {
                    $("#resultErrorMessage").text("No such User.").css("display", "block");
                }
            });
        });

        var MessageAnalysis = Widget.extend({
            template: 'groupme.msg_delivery_report',
            events: {
                'click a.js_msg_sort': 'listSortBy',
                'keyup input.js_txt_search': 'searchByName',
                'click li.next': 'go_next',
                'click li.previous': 'go_previous',
                'change .js_sel_records': 'changeMemberPerPage',
                'click button[data-dismiss="modal"]': 'cancel',
            },
            init: function(el, msg_id, net_id) {
                this.msg_id = msg_id;
                this.network_id = net_id;
                this.page =0;
                this.index_content = "";
                this.sortby = "all";
                this.search = false;
                this.MEMBERS_PER_PAGE = 10;
            },
            start: function() {
                self = this;
                this.$el.modal({
                    backdrop: 'static',
                    keyboard: false
                });
                $('.js_div_table').css({'max-height': $( window ).height()*0.5  , 'overflow-y': 'auto'});
                $('.js_msg_loading').show();
                $('.modal-body, .modal-footer').hide();
                self.getRows();
            },
            searchByName: function(e){
                var self = this;
                var $e = $(e.currentTarget);
                var search = $e.parent().find('.js_txt_search').val();  //text-transform:lowercase
                self.search = search;
                self.page = 0;
                self.display_rows();
            },
            listSortBy: function(e){
                var self = this;
                var $e = $(e.currentTarget);
                $('.js_msg_sort').css('font-weight', 'normal');
                $e.css('font-weight', 'bold');
                self.sortby = $e.data('sortby');
                self.search = false;
                self.page=0;
                self.display_rows();
            },
            go_next: function(e){
                var $e = $(e.currentTarget);
                if($e.hasClass('disabled'))
                {
                    e.preventDefault();
                    return false;
                }
                this.page += 1;
                this.display_rows();
            },
            go_previous: function(e){
                var $e = $(e.currentTarget);
                if($e.hasClass('disabled'))
                {
                    e.preventDefault();
                    return false;
                }
                if(this.page > 0)
                    this.page -= 1;
                this.display_rows();
            },
            styleToSearch: function(){
                var $row;
                var search=this.search;

                $(".tblDeliveryReport tbody tr").each(function(index) {
                    $row = $(this);
                    if ($row.find("td:first").text() != ""){
                        var thisValue = $row.find("td:first").text().toLowerCase();
                        if (thisValue.indexOf(search) < 0) {
                            $(this).hide();
                        }
                        else{
                            var eleVal = $row.find("td:first").text();
                            var str;
                            if( (str = eleVal.substr(thisValue.search(search), search.length)) )
                                $(this).find('td:first').html(eleVal.replace(str, '<kbd>' + str + '</kbd>'));
                            else
                                $(this).find('td:first').html(eleVal);
                            $(this).show();
                        }
                    }
                });
            },
            display_rows: function () {
                var self = this;
                var status = _.countBy(this.records, "status");

                $(".msgSent").text((status.delivered || 0) + (status.read || 0) + (status.sent || 0));
                // $(".msgDelivered").text((status.delivered || 0)  (status.read) || 0 );
                $(".msgDelivered").text(status.delivered || 0);
                $(".msgRead").text(status.read);
                $(".msgNoStatus").text(status.sent);

                var records;

                if(self.sortby && self.sortby != 'all')
                    records = _.where(this.records, {'status': self.sortby})
                else
                    records = self.records;

                if(self.search)
                {   // records : all/sent/deliveered/read any sortby is selected, search will be apply to that only
                    records = _.filter(records, function(item){ return item.name.toLowerCase().indexOf(self.search) > -1});
                }

                var from = this.page * this.MEMBERS_PER_PAGE;

                var upto = parseInt(from) + parseInt(this.MEMBERS_PER_PAGE);
                $('.js_search_count').text(records.length);
                var rows = _(records).chain()
                    .slice(from, upto)
                    .values()
                    .value();

                $('.tblDeliveryReport tbody').replaceWith(
                    core.qweb.render(
                        'groupme.message_status_record', {rows: rows}));
                if(this.search)
                    this.styleToSearch();

                $('.pager')
                    .find('li.previous').toggleClass('disabled', (from === 0)).end()
                    .find('li.next').toggleClass('disabled', (from + this.MEMBERS_PER_PAGE >= records.length));
            },
            getRows: function($el) {
                var self = this;
                var url = "/networks/network/"+self.network_id+"/message/" + self.msg_id + "/status";

                ajax.jsonRpc(url, 'call', {}).then(function(data) {
                    self.records = data;
                    $('.js_msg_loading').hide();
                    $('.modal-body, .modal-footer').show();
                    self.display_rows();
                });
            },
            cancel: function() {
                this.trigger("cancel");
            }
        });
        var objMsgAnalysis = false;
        $('.oe_msg_analysis').on('click', function(ev) {
            var msg_id = $(this).data('msg_id');
            var network_id = $(this).data('network_id');
            // website.add_template_file('/groupme/static/src/xml/groupme_msg_delivery_report.xml');
            if (!objMsgAnalysis) {
                website.add_template_file('/groupme/static/src/xml/groupme_msg_delivery_report.xml').done(function() {
                    objMsgAnalysis = new MessageAnalysis(self, msg_id, network_id);
                    objMsgAnalysis.appendTo(document.body);
                });
            } else
            {
                objMsgAnalysis = new MessageAnalysis(self, msg_id, network_id);
                objMsgAnalysis.appendTo(document.body);
            }
        });

    });
});