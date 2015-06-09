odoo.define('groupme.network', function(require) {
      "use strict";
      var ajax = require('web.ajax');
      var time = require('web.time');


      var page_widgets = {};
      var characters = 200;

      $(document).ready(function() {

            $("#oe_main_menu_navbar").removeClass('navbar');
            $("#oe_main_menu_navbar").removeClass('navbar-inverse');
            $("#oe_main_menu_navbar").css('display', 'none');

            $("timeago.timeago").each(function(index, el) {
                  var datetime = $(el).attr('datetime'),
                        datetime_obj = time.str_to_datetime(datetime),
                        // if presentation 7 days, 24 hours, 60 min, 60 second, 1000 millis old(one week)
                        // then return fix formate string else timeago
                        display_str = "";
                  if (datetime_obj && new Date().getTime() - datetime_obj.getTime() > 7 * 24 * 60 * 60 * 1000) {
                        display_str = datetime_obj.toDateString();
                  } else {
                        display_str = $.timeago(datetime_obj);
                  }
                  $(el).text(display_str);
            });


            $("#trueMsgLabel p a, #falseMsgLabel p a").click(function(ev) {
                  ev.preventDefault();
                  var active_msg = $(this).data('active_msg');
                  var network_id = $(this).data('network_id');
                  var url = "/networks/network/message/" + network_id;

                  ajax.jsonRpc(url, 'call', {}).then(function(data) {
                        if (data.result == true) {
                              $('#trueMsgLabel, #falseMsgLabel').toggle();
                        }
                        if (data.error) {
                              console.log("ERROR : ", data.error);
                        }
                  });
            });

            $("div .js_publish_management").click(function(ev) {
                  if ($(this).hasClass('css_published'))
                        $('#comment').hide();
                  else
                        $('#comment').show();
            });

            // Allowed only (characters) in text-area
            $("#txtMsg").keyup(function() {
                  if ($(this).val().length > characters) {
                        $(this).val($(this).val().substr(0, characters));
                  }
                  var remaining = characters - $(this).val().length;
                  $("#counter").html("You have <strong>" + remaining + "</strong> characters remaining");
                  if (remaining <= 10)
                        $("#counter").css("color", "red");
                  else
                        $("#counter").css("color", "inherit");
            });
            $('.js_group_type').on('change', function(e) {
                  var type;
                  if(this.id == 'optMyGroups'){
                      type = "own";
                  }
                  else if(this.id == 'optMembership'){
                      type = "membership";
                  }
                  else if(this.id == 'optAllGroups'){
                      type = "other";
                  }
                  window.location= "/networks?groups="+type;
            });
      });

      return {
            page_widgets: page_widgets,
      };
});