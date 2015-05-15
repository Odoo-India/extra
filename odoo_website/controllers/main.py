# -*- coding: utf-8 -*-

import base64
import werkzeug
from openerp import http
from openerp.addons.web.http import request

class OdooWebsites(http.Controller):

    _websites_per_page = 12

    @http.route('/websites', auth='public', type='http', website=True)
    def index(self, search=False, category_obj=False, tag_obj=False, page=1, **post):
        # website_obj = request.env['odoo.website']

        res_user = request.env.user
        public_user = request.website.user_id

        # websites = website_obj.search([])
        
        return request.render('odoo_website.websites', {
            'title': 'Websites build with Odoo CMS',
            # 'websites': websites,
            'is_public_user': res_user == public_user
            # 'search': search,
            # 'pager': pager,
            # 'user_id': res_user
        })

    @http.route('/websites/view/<model("odoo.website"):website_id>', auth='public', type='http', method='POST', website=True)
    def view(self, website_id, **post):
       return request.render('odoo_website.new', {
            'odoo_website': website_id
        })

    @http.route('/websites/new', auth='public', type='http', method='POST', website=True)
    def new(self, **post):
        website_obj = request.env['odoo.website']
        website = post.get('website')
        if website:
            vals = {
                'url': website
            }
            website_inst = website_obj.search([('url','=',website)], limit=1)
            if not website_inst:
                website_inst = website_obj.create(vals)
                website_inst.verify_odoo()

            url = '/websites/view/%s' % (website_inst.id)
            return werkzeug.utils.redirect(url)
        else:
            #TODO: error page
            pass