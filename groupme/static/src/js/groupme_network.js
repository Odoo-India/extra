odoo.define('groupme.network', function (require) {
	"use strict";
	var time = require('web.time');

	$(document).ready(function () {

		$("timeago.timeago").each(function (index, el) {
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
	});
});