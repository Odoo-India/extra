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
    full_url = fields.Char(compute="_compute_urls", store=True, string='Website Full Url')
    base_url = fields.Char(compute="_compute_urls", store=True, string='Base Url')
    image = fields.Binary(string='Desktop Image')
    image_laptop = fields.Binary(string='Laptop Image')
    image_tablet = fields.Binary(string='Tablet Image')
    image_mobile = fields.Binary(string='Mobile Image')

    is_image = fields.Boolean(string='Desktop Image Generated')
    is_image_laptop = fields.Boolean(string='Laptop Image Generated')
    is_image_tablet = fields.Boolean(string='Tablet Image Generated')
    is_image_mobile = fields.Boolean(string='Mobile Image Generated')

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

    def url_to_thumb(self, zoom=1, height=1000, width=1024):
        full_url, base_url = self.get_urls()
        fd, path = tempfile.mkstemp(suffix='.png', prefix='website.thumb.')
        try:
            process = subprocess.Popen(
                ['wkhtmltoimage', '--height', str(height), '--zoom', str(zoom),'--width',str(width), full_url, path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
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
    def _compute_urls(self):
        full_url, base_url = self.get_urls()
        self.base_url = base_url
        self.full_url = full_url
