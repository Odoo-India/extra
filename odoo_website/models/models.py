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
    _order = 'name'

    name = fields.Char('Website Name')
    description = fields.Text('Description', translate=True)
    url = fields.Char('Website Url', translate=True)
    image = fields.Binary('Image', translate=True)
    image_mobile = fields.Binary('Mobile Image', translate=True)
    is_odoo = fields.Boolean('Valid Odoo')
    version_info = fields.Char('Version Info')

    active = fields.Boolean('Active', default=False)

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

    def get_urls(self):
        if self.url.startswith('http://') or self.url.startswith('https://'):
            url = self.url.strip('/')
        else:
            url = 'http://' + self.url.strip('/')
        url_obj = urlparse(url)
        base_url = re.sub(url_obj.path+'$', '', url)
        return (url, base_url)

    @api.one
    def verify_odoo(self):
        if self.url:
            full_url, base_url = self.get_urls()
            try:
                req = Request(base_url+"/web/webclient/version_info", data='{"jsonrpc":"2.0","method":"call","params":{},"id":1}', headers= {'content-type': 'application/json'})
                content = urlopen(req)
                if content.code == 200:
                    self.is_odoo = True
                    self.active = True
                    self.version_info = content.read()
            except URLError, e:
                self.is_odoo = False

            try:
                arch = lxml.html.parse(urlopen(full_url))
                self.name = arch.find(".//title") != None and arch.find(".//title").text or ""
                if arch.find(".//meta[@name='description']") != None:
                    self.description =  arch.find(".//meta[@name='description']").attrib.get('content','')
            except URLError:
                self.name = 'Unknown Website'
                self.description = 'Unknown Website'

        return self.is_odoo

    @api.one
    def get_image(self, viewtype='desktop'):
        if self.url:
            full_url, base_url = self.get_urls()

            if viewtype == 'desktop':
                self.image =  self.url_to_thumb(full_url, zoom=0.9)

            if viewtype == 'mobile':
                self.image_mobile = self.url_to_thumb(full_url, width=400, height=600)

            if viewtype == 'tablate':
                #TODO: check the resolution
                pass
    
