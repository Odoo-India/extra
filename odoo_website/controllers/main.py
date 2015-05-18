# -*- coding: utf-8 -*-

import base64
import werkzeug
from openerp import http
from openerp.addons.web.http import request

class OdooWebsites(http.Controller):

    _websites_per_page = 12

    @http.route('/websites', auth='public', type='http', website=True)
    def index(self, search=False, category_obj=False, tag_obj=False, page=1, **post):
        website_obj = request.env['odoo.website']

        res_user = request.env.user
        public_user = request.website.user_id

        websites = website_obj.search([], limit=10)

        return request.render('odoo_website.websites', {
            'title': 'Websites build with Odoo CMS',
            'websites': websites,
            'is_public_user': res_user == public_user
        })


    @http.route('/websites/all', auth='public', type='http', website=True)
    def website_list(self, **post):
        website_obj = request.env['odoo.website']

        res_user = request.env.user
        public_user = request.website.user_id
        websites = website_obj.search([], limit=5)
        return request.render('odoo_website.website_list', {
            'websites': websites,
            'is_public_user': res_user == public_user
        })


    @http.route('/websites/view/<model("odoo.website"):website_id>', auth='public', type='http', method='POST', website=True)
    def view(self, website_id, **post):
       return request.render('odoo_website.view', {
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
                website_inst = website_obj.sudo().create(vals)

            url = '/websites/view/%s' % (website_inst.id)
            return werkzeug.utils.redirect(url)
        else:
            #TODO: error page
            pass

    @http.route('/websites/genrate_screenshot/<model("odoo.website"):odoo_website>', auth='public', type='json', website=True)
    def genrate_screenshot(self, odoo_website, type=None):
        if type == 'desktop':
            odoo_website.image = odoo_website.url_to_thumb(zoom=0.9, width=1350, height=850)
            odoo_website.is_image = True
        if type == 'mobile':
            odoo_website.image_mobile = odoo_website.url_to_thumb(width=400, height=630)
            odoo_website.is_image_mobile = True
        if type == 'tablet':
            odoo_website.image_tablet = odoo_website.url_to_thumb(width=820, height=1050)
            odoo_website.is_image_tablet = True
        if type == 'laptop':
            odoo_website.image_laptop = odoo_website.url_to_thumb(width=1250, height=790)
            odoo_website.is_image_laptop = True
        return {'status': True}
