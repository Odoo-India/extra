# -*- coding: utf-8 -*-

import re
import lxml
import json
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
    _order = 'id'

    url = fields.Char('Website Url', help="A url to webpage entered by user, i.e. https://www.odoo.com/page/point-of-sale")
    domain = fields.Char(compute="_compute_urls", store=True, string='base url will be www.odoo.com')
    full_url = fields.Char(compute="_compute_urls", store=True, string='full url will be https://www.odoo.com/page/point-of-sale')
    base_url = fields.Char(compute="_compute_urls", store=True, string='base url will be https://www.odoo.com')
    path = fields.Char(compute="_compute_urls", store=True, string='base url will be /page/point-of-sale')

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
    email = fields.Char(string='Submitted by')

    odoo = fields.Boolean(compute='_verify_odoo', store=True, string='Valid Odoo')
    version = fields.Char(compute='_verify_odoo', store=True, string='Version Info')
    active = fields.Boolean(compute='_verify_odoo', store=True, string='Active', default=False)

    pagespeed_mobile = fields.Text(string="Page Speed")
    pagespeed_desktop = fields.Text(string="Page Speed")

    pagespeed_ids = fields.One2many('odoo.website.pagespeed', 'page_id', 'Page Speed')

    desktop = fields.Many2one('odoo.website.pagespeed', compute='_find_page_speed', string='Parent')
    mobile = fields.Many2one('odoo.website.pagespeed', compute='_find_page_speed', string='Parent')

    display = fields.Boolean('Selected')
    link = fields.Char(compute='_compute_link', string='Link')

    @api.one
    @api.depends('url')
    def _compute_link(self):
        self.link = 'http://odoo.reviews/websites/view/%s' % (self.id)

    @api.one
    @api.depends('pagespeed_ids')
    def _find_page_speed(self):
        speed_obj = self.env['odoo.website.pagespeed']
        desktop = speed_obj.search([('page_id','=',self.id), ('target','=','desktop')], limit=1)
        self.desktop = desktop.id

        mobile = speed_obj.search([('page_id','=',self.id), ('target','=','mobile')], limit=1)
        self.mobile = mobile.id

    # parent_id = fields.Many2one(compute='_compute_parent', relation='odoo.website', string='Parent')
    # @api.depends('url')
    # def _compute_parent(self):
    #     for rec in self:
    #         rec.parent_id = False 
    #         if rec.path:
    #             parent_id = self.search([('base_url','=',rec.base_url), ('path','=',False)], limit=1)
    #             rec.parent_id = parent_id.id

    @api.one
    @api.depends('url')
    def _compute_urls(self):
        full_url = self.url
        if self.url and not self.url.startswith('http'):
            full_url = "http://%s" % (self.url)

        if self.url:
            url = urlparse(self.url)
            self.domain = url.netloc or url.path
            baseurl = "%s://%s" % (url.scheme or 'http', url.netloc or url.path)
            self.base_url = baseurl

            self.full_url = full_url
            self.path = url.path or False
        else:
            self.base_url = False
            self.full_url = False
            self.path = ''

    @api.one
    @api.depends('url')
    def _copute_meta(self):
        try:
            arch = lxml.html.parse(urlopen(self.full_url))
            self.name = arch.find(".//title") != None and arch.find(".//title").text or ""
            if arch.find(".//meta[@name='description']") != None:
                self.description =  arch.find(".//meta[@name='description']").attrib.get('content','')
        except URLError:
            self.name = 'Unknown Website'
            self.description = 'Unknown Website'

    @api.one
    @api.depends('url')
    def _verify_odoo(self):
        url = "%s/%s" % (self.base_url, "web/webclient/version_info")
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
        fd, path = tempfile.mkstemp(suffix='.png', prefix='website.thumb.')
        try:
            process = subprocess.Popen(
                ['wkhtmltoimage', '--height', str(height), '--zoom', str(zoom),'--width',str(width), self.full_url, path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except (OSError, IOError):
            return False
        else:
            out, err = process.communicate()
            png_file = open(path, 'r')
            return png_file.read().encode('base64')


    def get_pagespeed(self, target='desktop'):
        apikey = 'AIzaSyCNn6YxI47bWj4vzb-_dbcuOB9DGEW2VG0'
        apiurl = "https://www.googleapis.com/pagespeedonline/v2/runPagespeed?url=%s&strategy=%s&key=%s" % (self.full_url, target, apikey)
        result = urlopen(apiurl).read()
        return result


    @api.one
    @api.depends('url')
    def _compute_page_speed(self):
        result = self.get_pagespeed()
        jsonresult = json.loads(result)
        if jsonresult.get('responseCode') == 200:
            self.pagespeed_desktop = result

        result = self.get_pagespeed(target='mobile')
        jsonresult = json.loads(result)
        if jsonresult.get('responseCode') == 200:
            self.pagespeed_mobile = result
    

    @api.one
    def compute_pagespeed(self):
        self._compute_page_speed()
        self.compute_pagespeed_target(pagespeed=self.pagespeed_desktop, target='desktop')
        self.compute_pagespeed_target(pagespeed=self.pagespeed_mobile, target='mobile')


    @api.one
    def compute_pagespeed_target(self, pagespeed, target='desktop'):
        result = json.loads(pagespeed)

        def lineformat(line, args):
            for arg in args:
                if arg.get('type') == 'HYPERLINK':
                    key = "{{BEGIN_LINK}}"
                    value = "<a href='%s' target='_new'>" % arg.get('value')
                    line = line.replace(key, value)

                    key = "{{END_LINK}}"
                    value = "</a>"
                    line = line.replace(key, value)
                else:
                    key = '{{%s}}' % arg.get('key')
                    value = "%s" % (arg.get('value'))

                    if arg.get('type') not in ('STRING_LITERAL', 'URL'):
                        value = "<b class='code'>%s</b>" % (arg.get('value'))
                    
                    if arg.get('type') == 'STRING_LITERAL':

                        value = "<code class='code'>%s</code>" % (arg.get('value').replace('<', '&lt;').replace('>', '&gt;'))

                    line = line.replace(key, value)
            return line

        rule_obj = self.env['odoo.website.pagespeed.rules']
        block_obj = self.env['odoo.website.pagespeed.rules.block']
        url_obj = self.env['odoo.website.pagespeed.rules.block.url']

        vals = {
            'name': result.get('title'),
            'version_major': result.get('version').get('major'),
            'version_minor': result.get('version').get('minor'),
            'speed_score': result.get('ruleGroups').get('SPEED').get('score'),
            'usability_score': result.get('ruleGroups', {}).get('USABILITY', {}).get('score', 0),
            'page_id': self.id,
            'locale': result.get('formattedResults').get('locale'),
            'pagespeed': pagespeed,
            'target': target
        }
        for key in result.get('pageStats'):
            vals[key.lower()] = result.get('pageStats').get(key)

        vals['nvd3_json'] = json.dumps([
            {"label": "HTML", "value": vals.get('htmlresponsebytes', 0)},
            {"label": "CSS",  "value": vals.get('cssresponsebytes', 0)},
            {"label": "JavaScript", "value": vals.get('javascriptresponsebytes', 0)},
            {"label": "Image", "value": vals.get('imageresponsebytes', 0)},
            {"label": "Other", "value": vals.get('otherresponsebytes', 0)}
        ])
        entry_id = self.env['odoo.website.pagespeed'].create(vals)

        for key, rule in result.get('formattedResults').get('ruleResults').iteritems():
            entry = {
                'entry_id': entry_id.id,
                'name': rule.get('localizedRuleName'),
                'ruleimpact': rule.get('ruleImpact'),
                'group': rule.get('groups')[0],
                'summary': lineformat(rule.get('summary', {}).get('format', ''), rule.get('summary',{}).get('args',[]))
            }
            rule_id = rule_obj.create(entry)

            for block in rule.get('urlBlocks', []):
                block_val = {
                    'rule_id': rule_id.id,
                    'name': lineformat(block.get('header', {}).get('format', ''), block.get('header', {}).get('args', []))
                }
                block_id = block_obj.create(block_val)

                for url in block.get('urls', []):
                    vals = {
                        'block_id': block_id.id,
                        'name': lineformat(url.get('result', {}).get('format', ''), url.get('result', {}).get('args',[]))
                    }
                    url_obj.create(vals)


class PageSpeedEntry(models.Model):
    _name = 'odoo.website.pagespeed'
    _description = 'Google PageSpeed Entry'
    _order = 'id desc'

    name = fields.Char('Name')
    locale = fields.Char('Locale')
    pagespeed = fields.Text("Page Speed")

    version_major = fields.Integer('Major')
    version_minor = fields.Integer('Minor')

    speed_score = fields.Integer('Speed')
    usability_score = fields.Integer('Usability')

    page_id = fields.Many2one('odoo.website', 'Page')

    numberresources = fields.Integer('# of Resource')
    numberhosts = fields.Integer('# of Host')
    totalrequestbytes = fields.Integer('# of RequestBytes')
    numberstaticresources = fields.Integer('# of RequestBytes')
    htmlresponsebytes = fields.Integer('# of RequestBytes')
    textresponsebytes = fields.Integer('# of RequestBytes')
    cssresponsebytes = fields.Integer('# of RequestBytes')
    imageresponsebytes = fields.Integer('# of RequestBytes')
    javascriptresponsebytes = fields.Integer('# of RequestBytes')
    otherresponsebytes = fields.Integer('# of RequestBytes')
    nvd3_json = fields.Text('Json data for nvd3')

    numberjsresources = fields.Integer('# of RequestBytes')
    numbercssresources = fields.Integer('# of RequestBytes')
    ruler_ids = fields.One2many('odoo.website.pagespeed.rules', 'entry_id')
    create_date = fields.Datetime('Tested on ')
    target = fields.Char('Target Device')


class PageSpeedEntryRule(models.Model):
    _name = 'odoo.website.pagespeed.rules'
    _description = 'Google PageSpeed Entry'
    _order = 'ruleimpact desc'

    name = fields.Char('Name')
    entry_id = fields.Many2one('odoo.website.pagespeed', 'PageSpeed Entry')
    ruleimpact = fields.Float('Impact')
    summary = fields.Char('Summary')
    group = fields.Char('Group')
    urlblock_ids = fields.One2many('odoo.website.pagespeed.rules.block', 'rule_id', 'Urls')


class PageSpeedEntryRule(models.Model):
    _name = 'odoo.website.pagespeed.rules.block'
    _description = 'Google PageSpeed Entry Url Block'

    rule_id = fields.Many2one('odoo.website.pagespeed.rules')
    name = fields.Char('Header')
    url_ids = fields.One2many('odoo.website.pagespeed.rules.block.url', 'block_id', 'Urls')


class PageSpeedEntryRuleUrls(models.Model):
    _name = 'odoo.website.pagespeed.rules.block.url'
    _description = 'Google PageSpeed Entry Ref. Urls'

    name = fields.Char('Name')
    block_id = fields.Many2one('odoo.website.pagespeed.rules.block')
