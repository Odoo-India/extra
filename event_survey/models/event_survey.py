# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

class event_track(models.Model):
    _name = "event.track.custom"
    _inherit = ['mail.thread']

    name = fields.Char(string="Title")
    odoo_event_id = fields.Char()
    average_rating = fields.Float(compute="_average_ratings", store=True, string="Average Rating")
    number_of_feedback = fields.Float(compute="_average_ratings", store=True, string="#feedback")
    odoo_url = fields.Char(string="Go to actual event")
    feedback_ids = fields.One2many("event.track.feedback", "track_id", "Feedbacks", copy=False, ondelete='cascade')

    @api.multi
    @api.depends('feedback_ids')
    def _average_ratings(self):
        for track in self:
            if track.feedback_ids:
                track.average_rating = sum([float(rating) for rating in track.feedback_ids.mapped('overall_rating')]) / len(track.feedback_ids)
                track.number_of_feedback = len(track.feedback_ids)

class EventTrackFeedback(models.Model):
    _name = "event.track.feedback"

    track_id = fields.Many2one("event.track.custom")
    partner_id = fields.Many2one("res.partner", string="Submited by")
    comment = fields.Text(string="Comment")
    overall_rating = fields.Selection([
        ("0", "Not Rated"),
        ("1", "Not good at all"),
        ("2", "Not so good"),
        ("3", "Average"),
        ("4", "Good"),
        ("5", "Excellent")], string="Overall, how would you rate this track ?", default="0")
    content_rating = fields.Selection([
        ("0", "Not Rated"),
        ("1", "To basic"),
        ("2", "Average"),
        ("3", "Excellent"),
        ("4", "Advance"),
        ("5", "To Advance")], string="Based on description/my expectations, the content was ?", default="0")

class event_attendee(models.Model):
    _inherit = "res.partner"

    is_exp_user = fields.Boolean("Odoo Exprience User")
    plus_img_url = fields.Char("Google Plus Image URL")
    plus_profile_url = fields.Char("Google Plus Profile URL")
