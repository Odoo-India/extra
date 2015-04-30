# -*- coding: utf-8 -*-

import werkzeug

from openerp import http
# from openerp import SUPERUSER_ID
from openerp.tools.misc import ustr
from openerp.addons.web.http import request
from openerp.tools.mail import html2plaintext


class GroupMe(http.Controller):

    _networks_per_page = 8

    @http.route([
        '/networks',
        '/networks/page/<int:page>'
    ], auth='public', type='http', website=True)
    def network(self, search=False, page=1, **post):
        network_obj = request.env['groupme.network']

        res_user = request.env.user
        public_user = request.website.user_id
        domain = []

        if public_user != res_user:
            domain += [('author_id', '=', res_user.id)]
        else:
            domain += [('website_published', '=', True)]

        if search:
            domain += [("name", "ilike", search)]

        pager_url = "/networks"
        pager_args = {}

        pager_count = network_obj.search_count(domain)
        pager = request.website.pager(url=pager_url, total=pager_count, page=page,
                                      step=self._networks_per_page, scope=self._networks_per_page,
                                      url_args=pager_args)

        networks = network_obj.search(
            domain, limit=self._networks_per_page, offset=pager['offset'])

        return request.render('groupme.networks', {
            'networks': networks,
            'is_public_user': res_user == public_user,
            'search': search,
            'pager': pager,
            'user_id': res_user
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

        body = "%s - %s" % (post['comment'], post['link'])
        contextual_slide.message_post(
            body=body,
            type='comment',
            subtype='mt_comment',
            **post_kwargs
        )
        return werkzeug.utils.redirect(request.httprequest.referrer + "#discuss")

    @http.route(['/networks/network/add_network'], type='json',
                auth='user', methods=['POST'], website=True)
    def create_network(self, *args, **post):
        category_obj = request.env['groupme.network.category']
        network_obj = request.env['groupme.network']

        values = post
        values['author_id'] = request.env.uid
        # values['website_message_ids'] = [0, 0, {'res_id', request.env.uid}]

        if post.get('category_id', False):
            if post.get('category_id')[0] == 0:
                values['category_id'] = category_obj.create({
                    'name': post['category_id'][1]['name'],
                    'description': '',
                    'icon': ''}).id
            else:
                values['category_id'] = post['category_id'][0]

        try:
            network_id = network_obj.create(values)
        except Exception as e:
            return {'error': 'Internal server error, please try again later or contact administrator.\nHere is the error message: %s' % e.message}
        return {'url': "/networks/network/%s" % (network_id.id)}
