# -*- coding: utf-8 -*-

from openerp import http
from openerp import SUPERUSER_ID
from openerp.tools.misc import ustr
from openerp.addons.web.http import request
from openerp.tools.mail import html2plaintext
from openerp.Debugger import Debugg
logger = Debugg


class GroupMe(http.Controller):

    @http.route(['/networks', '/networks/<string:search>'], auth='public', type='http', website=True)
    def network(self, search="", **post):
        network_obj = request.env['groupme.network']
        partner_obj = request.env['res.partner']
        category_obj = request.env['groupme.network.category']

        res_user = request.env.user
        public_user = request.website.user_id
        user_obj = False
        domain = []
        if public_user != res_user:
            domain = [('author_id', '=', res_user.id)]
            user_obj = partner_obj.browse(res_user)

        if search:
            search = request.httprequest.query_string.split("=")[1]
            domain = [("name", "ilike", search)]

        networks = network_obj.search(domain)
        categories = category_obj.search([])
        return request.render('groupme.networks', {
            'networks': networks,
            'categories': categories,
            'is_public_user': res_user == public_user,
            'user': user_obj
        })

    @http.route('/network/<model("groupme.network"):network_id>', auth='public', type='http', website=True)
    def group_details(self, network_id):
        res_user = request.env.user
        public_user = request.website.user_id

        return request.render('groupme.network_view', {
            'user': res_user,
            'network': network_id,
            'is_public_user': res_user == public_user
        })

    @http.route('/networks/new', auth='public', type='http', website=True)
    def group_create(self):
        res_user = request.env.user
        public_user = request.website.user_id

        return request.render('groupme.networks_create', {
            'user': res_user,
            'is_public_user': res_user == public_user
        })

    @http.route('/networks/save', auth='public', type='http', website=True)
    def group_save(self, **post):
        group_obj = request.env['groupme.network']
        logger.info(post)
        rec = {
            'name': post.get('name'),
            'code': post.get('code'),
            'visibility': post.get('visibility'),
            'author_id': request.env.user.id
        }
        rec_id = group_obj.create(rec)
        if rec_id:
            url = '/network/%s' % (rec_id.id)
            return request.redirect(url)
        else:
            # TODO: move to error page if new group not created
            pass

        # @http.route('/website/image/groupme.network/#{network.id}/image_thumb', auth='public', type='http', website=True)
        # def imageServing(self, id, **post):
        #     return
        #     pass

        @http.route('/networks/search', auth='public', type='http', website=True)
        def searchNetwork(self, **post):
            print post
            pass
