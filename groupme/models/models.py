# -*- coding: utf-8 -*-

import time
import hashlib
import logging
from datetime import datetime
from openerp.tools import image
from openerp import models, fields, api

_logger = logging.getLogger(__name__)


class Category(models.Model):
    _name = 'groupme.network.category'
    _description = 'Category'
    _inherit = ['website.published.mixin']

    name = fields.Char('Name')
    icon = fields.Char('Icon')
    description = fields.Html('Page')

    number_groups = fields.Integer(
        compute='_compute_total', string='Total Groups')
    group_ids = fields.One2many('groupme.network', 'category_id', 'Groups')

    def _compute_total(self):
        for rec in self:
            self.number_groups = len(rec.group_ids)


class Tag(models.Model):
    _name = 'groupme.network.tag'
    _description = 'Tag'

    name = fields.Char('Name')


class Network(models.Model):
    _name = 'groupme.network'
    _description = 'Network'
    _inherit = [
        'mail.thread', 'website.seo.metadata', 'website.published.mixin']

    category_id = fields.Many2one('groupme.network.category', 'Category')
    tag_ids = fields.Many2many(
        'groupme.network.tag', 'rel_network_tag', 'network_id', 'tag_id', 'Tags')

    name = fields.Char('Name', translate=True, required=True)
    code = fields.Char('Code', required=True)

    title = fields.Html('Title', translate=True)
    description = fields.Html('Description', translate=True)

    image = fields.Binary('Logo', help='group logo')
    image_medium = fields.Binary('Medium', compute="_get_image", store=True)
    image_thumb = fields.Binary('Thumbnail', compute="_get_image", store=True)

    author_id = fields.Many2one('res.users', 'Admin')
    member_ids = fields.Many2many(
        'res.partner', 'rel_network_users', 'network_id', 'user_id', string='Members')

    star = fields.Boolean('Star Group')
    active = fields.Boolean('Active', default=True)
    visibility = fields.Selection(
        [('public', 'Public'), ('private', 'Private')], string='Visiblity', default="public")

    create_date = fields.Datetime('Create Date')
    location = fields.Char('Location')
    message_per_day = fields.Integer('Message per Day', default=10)
    website_message_ids = fields.One2many(
        'mail.message', 'res_id',
        domain=lambda self: [
            ('model', '=', self._name), ('type', '=', 'comment')],
        string='Website Messages', help="Website communication history")

    @api.depends('image')
    def _get_image(self):
        for record in self:
            if record.image:
                record.image_medium = image.crop_image(
                    record.image, thumbnail_ratio=3)
                record.image_thumb = image.crop_image(
                    record.image, thumbnail_ratio=4)
            else:
                record.image_medium = False
                record.iamge_thumb = False

    def save(self, **post):
        logger.info(post)


class res_partner(models.Model):
    _inherit = 'res.partner'

    network_ids = fields.Many2many(
        'res.partner', 'rel_network_users', 'user_id', 'network_id', string='Members')
    company_name = fields.Char('Company')
    devicekey = fields.Char('Device Key')
