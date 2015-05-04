# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
import subprocess
import tempfile
import lxml
from urllib2 import urlopen, URLError, HTTPError, Request
from urlparse import urlparse
import re
import requests

class WebsiteExamples(models.Model):
    _name = 'website.examples'
    _inherit = ['mail.thread', 'website.seo.metadata']
    _order = 'name'

    name = fields.Char('Website Name', required=True)
    description = fields.Text('Description', translate=True)
    url = fields.Char('Website Url', translate=True)
    image = fields.Binary('Image', translate=True)
    image_mobile = fields.Binary('Mobile Image', translate=True)
    is_odoo = fields.Boolean('Valid Odoo')
    version_info = fields.Char('Version Info')

    def url_to_thumb(self, url, zoom = 1, height=1000, width=1024):
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
        

    @api.onchange('url')
    def _onchange_url(self):
        if self.url:
            full_url, base_url = self.get_urls()
            self.image =  self.url_to_thumb(full_url,zoom=0.9)
            self.image_mobile =  self.url_to_thumb(full_url, width=400, height=600)
            try:
                arch = lxml.html.parse(urlopen(full_url))
                self.name = arch.find(".//title") != None and arch.find(".//title").text or ""
                if arch.find(".//meta[@name='description']") != None:
                    self.description =  arch.find(".//meta[@name='description']").attrib.get('content','')
            except URLError:
                print "META::: ERROR >>>>>"

            try:
                req = Request(base_url+"/web/webclient/version_info", data='{"jsonrpc":"2.0","method":"call","params":{},"id":1}', headers= {'content-type': 'application/json'})
                content = urlopen(req)
                if content.code == 200:
                    self.is_odoo = True
                    self.version_info = content.read()
            except URLError, e:
                self.is_odoo = False
                print "URLLLL::: ERROR >>>>>",e.code

