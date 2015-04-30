# -*- coding: utf-8 -*-

import werkzeug

from openerp import http
# from openerp import SUPERUSER_ID
from openerp.tools.misc import ustr
from openerp.addons.web.http import request
from openerp.tools.mail import html2plaintext


class GroupMe(http.Controller):

    @http.route('/networks', auth='public', type='http', website=True)
    def network(self, search_key=False, **post):
        network_obj = request.env['groupme.network']

        res_user = request.env.user
        public_user = request.website.user_id
        domain = []

        if public_user != res_user:
            domain += [('author_id', '=', res_user.id)]

        if search_key:
            domain += [("name", "ilike", search_key)]

        networks = network_obj.search(domain)

        return request.render('groupme.networks', {
            'networks': networks,
            'is_public_user': res_user == public_user,
            'search': search_key
        })

    @http.route('/networks/network/<model("groupme.network"):network_id>', auth='public', type='http', website=True)
    def group_details(self, network_id):
        res_user = request.env.user
        public_user = request.website.user_id

        return request.render('groupme.network_view', {
            'user': res_user,
            'network': network_id,
            'is_public_user': res_user == public_user,
            'comments': network_id.website_message_ids or []
        })

    @http.route('/networks/network/<model("groupme.network"):network_id>/comment', type='http', auth="public", methods=['POST'], website=True)
    def group_comment(self, network_id, **post):
        """ Controller for message_post. Public user can post; their name and
        email is used to find or create a partner and post as admin with the
        right partner. Their comments are not published by default. Logged
        users can post as usual. """
        # TDE TODO :
        # - fix _find_partner_from_emails -> is an api.one + strange results + should work as public user
        # - subscribe partner instead of user writing the message ?
        # - public user -> cannot create mail.message ?
        if not post.get('comment'):
            return werkzeug.utils.redirect(request.httprequest.referrer + "#discuss")
        # public user: check or find author based on email, do not subscribe public user
        # and do not publish their comments by default to avoid direct spam
        if request.uid == request.website.user_id.id:
            if not post.get('email'):
                return werkzeug.utils.redirect(request.httprequest.referrer + "#discuss")
            # TDE FIXME: public user has no right to create mail.message, should
            # be investigated - using SUPERUSER_ID meanwhile
            contextual_slide = network_id.sudo().with_context(
                mail_create_nosubcribe=True)
            # TDE FIXME: check in mail_thread, find partner from emails should
            # maybe work as public user
            partner_id = network_id.sudo()._find_partner_from_emails(
                [post.get('email')])[0][0]
            if partner_id:
                partner = request.env['res.partner'].sudo().browse(partner_id)
            else:
                partner = request.env['res.partner'].sudo().create({
                    'name': post.get('name', post['email']),
                    'email': post['email']
                })
            post_kwargs = {
                'author_id': partner.id,
                'website_published': False,
                'email_from': partner.email,
            }
        # logged user: as usual, published by default
        else:
            contextual_slide = network_id
            post_kwargs = {}

        contextual_slide.message_post(
            body=post['comment'],
            type='comment',
            subtype='mt_comment',
            **post_kwargs
        )
        return werkzeug.utils.redirect(request.httprequest.referrer + "#discuss")

    # @http.route('/networks/new', auth='public', type='http', website=True)
    # def group_new(self):
    #     res_user = request.env.user
    #     public_user = request.website.user_id

    #     return request.render('groupme.networks_create', {
    #         'user': res_user,
    #         'is_public_user': res_user == public_user
    #     })

    @http.route(['/networks/network/add_network'], type='json', auth='user', methods=['POST'], website=True)
    def create_network(self, *args, **post):

        values = post
        values['author_id'] = request.env.uid

        if post.get('category_id'):
            if post['category_id'][0] == 0:
                values['category_id'] = request.env['groupme.network.category'].create({
                    'name': post['category_id'][1]['name'],
                    'description': '',
                    'icon': ''}).id
            else:
                values['category_id'] = post['category_id'][0]

        try:
            network_id = request.env['groupme.network'].create(values)
        except Exception as e:
            return {'error': _('Internal server error, please try again later or contact administrator.\nHere is the error message: %s' % e.message)}
        return {'url': "/networks/network/%s" % (network_id.id)}

    # @http.route('/networks/save', auth='public', type='http', website=True)
    # def group_save(self, **post):
    #     group_obj = request.env['groupme.network']
    #     rec = {
    #         'name': post.get('name'),
    #         'code': post.get('code'),
    #         'visibility': post.get('visibility'),
    #         'author_id': request.env.user.id
    #     }
    #     rec_id = group_obj.create(rec)
    #     if rec_id:
    #         url = '/network/%s' % (rec_id.id)
    #         return request.redirect(url)
    #     else:
    # TODO: move to error page if new group not created
    #         pass
