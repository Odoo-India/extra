from openerp import http
from openerp.http import request


class EventSurvey(http.Controller):

    @http.route('/event_survey/submit', type='json', auth='public')
    def submit_event(self, **post):
        partner_obj = request.env['res.partner'].sudo()
        track_obj = request.env['event.track.custom'].sudo()
        feedback_obj = request.env['event.track.feedback'].sudo()
        track = track_obj.search([('odoo_event_id', '=', post.get("track_id"))], limit=1)
        if not track:
            track = track_obj.create({
                'odoo_event_id': post.get("track_id"),
                'name': post.get('track_name'),
                'odoo_url': "https://www.odoo.com/event/304/track/%s" % (post.get("track_id"))
            })
        partner = partner_obj.search([('email', '=', post.get("email"))], limit=1)
        if not partner:
            partner = partner_obj.create({'name': post.get("user_name"), "email": post.get("email"), "is_exp_user": True})

        if feedback_obj.search([('partner_id', '=', partner.id), ('track_id', '=', track.id)]):
            return {'status': 'exist'}

        feedback_obj.create({
            'track_id': track.id,
            'partner_id': partner.id,
            'comment': post.get("comment"),
            'overall_rating': post.get("overall_rating"),
            'content_rating': post.get("content_rating"),
        })

        overall_rating = ["Not Rated", "Not good at all", "Not so good", "Average", "Good", "Excellent"]
        content_rating = ["Not Rated", "To basic", "Average", "Excellent", "Advance", "To Advance"]
        body = '''<div>
                        Feedback from<b> <a class="oe_mail_action_author" data-partner="%s" href="#id=%s&view_type=form&model=res.partner">%s</a></b></div>
                        <div> &nbsp; &nbsp; &bull; <b>Overall, how would you rate this track ?:</b> %s%s [%s]</div>
                        <div> &nbsp; &nbsp; &bull; <b>Based on description/my expectations, the content was ?:</b>%s</div>
                        <div> &nbsp; &nbsp; &bull; <b>Comment:</b> %s</div>
        '''%(partner.id,partner.id, partner.name,'&#9733;'*int(post.get("overall_rating")),'&#9734;'*(5-int(post.get("overall_rating"))),overall_rating[int(post.get("overall_rating"))],content_rating[int(post.get("content_rating"))],post.get("comment"))
        track.message_post(body=body)
        return {'status': 'success'}

    @http.route('/event_survey/add_attendee', type='json', auth='public')
    def add_atendee(self, **post):
        partner_obj = request.env['res.partner'].sudo()
        partner = partner_obj.search([('email', '=', post.get("email"))], limit=1)
        if not partner:
            partner = partner_obj.create({'name': post.get("name"), "email": post.get("email"),'is_exp_user': True, "plus_img_url": post.get("image_url"), "plus_profile_url": post.get("gplus_url")})
        else:
            partner.is_exp_user = True
