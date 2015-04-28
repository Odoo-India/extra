# -*- coding: utf-8 -*-

from openerp import http
from openerp import SUPERUSER_ID
from openerp.tools.misc import ustr
from openerp.addons.web.http import request
from openerp.tools.mail import html2plaintext

class GroupMe(http.Controller):

    @http.route('/networks', auth='public', type='http', website=True)
    def network(self):
        network_obj = request.env['groupme.network']
        partner_obj = request.env['res.partner']

        res_user = request.env.user
        public_user = request.website.user_id
        user_obj = False
        domain = []

        if public_user != res_user:
            domain = [('author_id', '=', res_user.id)]
            user_obj = partner_obj.browse(res_user)

        networks = network_obj.search(domain)

        return request.render('groupme.networks', {
            'networks': networks,
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
            #TODO: move to error page if new group not created
            pass