# -*- coding: utf-8 -*-

import re
import lxml
import tempfile
import requests
import subprocess

from urllib2 import urlopen
from urllib2 import URLError
from urllib2 import Request
from urllib2 import HTTPError
from urlparse import urlparse

from openerp import models, fields, api, _

class OdooWebsite(models.Model):
    _name = 'odoo.website'
    _inherit = ['mail.thread', 'website.seo.metadata']
    _order = 'id desc'

    url = fields.Char('Website Url')
    image = fields.Binary(compute='_get_desktop_image', store=True, string='Image')
    image_mobile = fields.Binary(compute='_get_mobile_image', store=True, string='Mobile Image')
    
    name = fields.Char(compute='_copute_meta', store=True, string='Website Name')
    description = fields.Text(compute='_copute_meta', store=True, string='Description')

    odoo = fields.Boolean(compute='_verify_odoo', store=True, string='Valid Odoo')
    version = fields.Char(compute='_verify_odoo', store=True, string='Version Info')
    active = fields.Boolean(compute='_verify_odoo', store=True, string='Active', default=False)

    pagespeed = fields.Text(compute='_compute_page_speed', store=True, string="Page Speed")

    def get_urls(self):
        if self.url.startswith('http://') or self.url.startswith('https://'):
            url = self.url.strip('/')
        else:
            url = 'http://' + self.url.strip('/')
        url_obj = urlparse(url)
        base_url = re.sub(url_obj.path+'$', '', url)
        return (url, base_url)

    @api.one
    @api.depends('url')
    def _copute_meta(self):
        full_url, base_url = self.get_urls()
        try:
            arch = lxml.html.parse(urlopen(full_url))
            self.name = arch.find(".//title") != None and arch.find(".//title").text or ""
            if arch.find(".//meta[@name='description']") != None:
                self.description =  arch.find(".//meta[@name='description']").attrib.get('content','')
        except URLError:
            self.name = 'Unknown Website'
            self.description = 'Unknown Website'

    @api.one
    @api.depends('url')
    def _verify_odoo(self):
        full_url, base_url = self.get_urls()
        url = "%s/%s" % (base_url, "web/webclient/version_info")
        self.active = False
        self.odoo = False
        try:
            req = Request(url, 
                data='{"jsonrpc":"2.0","method":"call","params":{},"id":1}', 
                headers= {'content-type': 'application/json'})
            content = urlopen(req)
            if content.code == 200:
                self.odoo = True
                self.active = True
                self.version = content.read()
        except URLError, e:
            self.is_odoo = False

    def url_to_thumb(self, url, zoom=1, height=1000, width=1024):
        fd, path = tempfile.mkstemp(suffix='.png', prefix='website.thumb.')
        try:
            process = subprocess.Popen(
                ['wkhtmltoimage', '--height', str(height), '--zoom', str(zoom),'--width',str(width), url, path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except (OSError, IOError):
            return False
        else:
            out, err = process.communicate()
            png_file = open(path, 'r')
            return png_file.read().encode('base64')

    @api.one
    @api.depends('url')
    def _compute_page_speed(self):
        self.pagespeed = ''

    @api.one
    @api.depends('url')
    def _get_desktop_image(self):
        full_url, base_url = self.get_urls()
        self.image =  self.url_to_thumb(full_url, zoom=0.9)

    @api.one
    @api.depends('url')
    def _get_mobile_image(self):
        full_url, base_url = self.get_urls()
        self.image_mobile = self.url_to_thumb(full_url, width=400, height=600)
