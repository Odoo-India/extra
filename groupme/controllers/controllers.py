# -*- coding: utf-8 -*-

import werkzeug
import base64
import logging
from openerp import http
# from openerp import SUPERUSER_ID
import json
import time
# from time import gmtime, strftime
from psycopg2 import IntegrityError
from openerp.tools.misc import ustr
from openerp.addons.web.http import request
from openerp.tools.mail import html2plaintext

logger = logging.getLogger(__name__)


class GroupMe(http.Controller):

    _networks_per_page = 12

    @http.route([
        '/networks',
        '/networks/page/<int:page>',
        '/networks/category/<model("groupme.network.category"):category_obj>',
        '/networks/category/<model("groupme.network.category"):category_obj>/page/<int:page>',
        '/networks/tag/<model("groupme.network.tag"):tag_obj>',
        '/networks/tag/<model("groupme.network.tag"):tag_obj>/page/<int:page>'
    ], auth='public', type='http', website=True)
    def network(self, groups=False, search=False, category_obj=False, tag_obj=False,
                page=1, **post):
        network_obj = request.env['groupme.network']
        res_user = request.env.user
        public_user = request.website.user_id
        domain = []

        if public_user != res_user:
            # Logged In

            if groups:
                if groups == "own":
                    domain += [('author_id', '=', res_user.id)]
                elif groups == "membership":
                    # I am Member
                    domain += ['&', '&', ('author_id', '!=', res_user.id),
                               ('message_follower_ids',
                                '=', res_user.partner_id.id),
                               ('website_published', '=', True)]

                elif groups == "other":
                    # I am not a member nor author
                    domain += ['&', '&', ('author_id', '!=', res_user.id),
                               ('message_follower_ids', '!=',
                                res_user.partner_id.id),
                               ('website_published', '=', True)]
            else:
                domain += [('author_id', '=', res_user.id)]
        else:
            domain += [('website_published', '=', True)]

        pager_url = "/networks"
        pager_args = {}

        if search:
            domain += [("name", "ilike", search)]
        if category_obj:
            domain += [("category_id", "=", category_obj.id)]
            pager_url += "/category/%s" % category_obj.id
        elif tag_obj:
            domain += [('tag_ids.id', '=', tag_obj.id)]
            pager_url += "/tag/%s" % tag_obj.id

        pager_count = network_obj.search_count(domain)
        pager = request.website.pager(url=pager_url, total=pager_count, page=page,
                                      step=self._networks_per_page, scope=self._networks_per_page,
                                      url_args=pager_args)

        networks = network_obj.search(
            domain, limit=self._networks_per_page, offset=pager['offset'])

        return request.render('groupme.networks', {
            'title': 'Groups | Odoo',  # page title
            'networks': networks,
            'is_public_user': res_user == public_user,
            'search': search,
            'pager': pager,
            'type': groups,
            'user_id': res_user
        })

    @http.route('/networks/network/<model("groupme.network"):network_id>', auth='public', type='http', website=True)
    def group_details(self, network_id):
        res_user = request.env.user
        public_user = request.website.user_id

        currentrights = getUserRights(res_user, network_id)

        return request.render('groupme.network_view', {
            'title': network_id.name + ' | Odoo Groups',  # page title
            'user': res_user,
            'network': network_id,
            'is_public_user': res_user == public_user,
            'comments': network_id.website_message_ids or [],
            'currentrights': currentrights
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
            return werkzeug.utils.redirect(request.httprequest.referrer + "#messages")
        # public user: check or find author based on email, do not subscribe public user
        # and do not publish their comments by default to avoid direct spam
        if request.uid == request.website.user_id.id:
            if not post.get('email'):
                return werkzeug.utils.redirect(request.httprequest.referrer + "#messages")
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
            active=network_id.view_message,
            **post_kwargs
        )
        return werkzeug.utils.redirect(request.httprequest.referrer + "#messages")

    @http.route(['/networks/network/create'], type='json', auth='user', methods=['POST'], website=True)
    def create_network(self, *args, **post):
        # assign Rights to user
        # by adding user to group "Display Editor Bar on Website" Group
        resgroup = request.env['res.groups'].search(
            [('name', '=', 'Display Editor Bar on Website')])

        if not request.env.user in resgroup.users:
            resgroup.sudo().write({'users': [(4, request.env.user.id)]})

        # category_obj = request.env['groupme.network.category']
        network_obj = request.env['groupme.network']

        values = post
        values['code'] = post['code'].lower()
        values['author_id'] = request.env.uid
        if post.get('category_id', False):
            values['category_id'] = post['category_id'][0]

        try:
            network_id = network_obj.create(values)
            userrights = request.env['groupme.userrights']
            userrightsdata = {'groupid': network_id.id,
                              'partnerid': request.env.user.partner_id.id,
                              'hasAdminRights': True,
                              'hasMessagingRights': True,
                              'hasImportRights': True
                              }
            userrights.sudo().create(userrightsdata)
        except IntegrityError:
            return {'error': 'Integrity Error, Code must be unique!'}
        except Exception as e:
            return {'error': 'Internal server error, please try again later or\
        contact administrator.\nHere is the error message: % s' % e.message}
        return {'url': "/networks/network/%s" % (network_id.id)}

    @http.route(['/networks/network/invite'], type='json', auth='user', methods=['POST'], website=True)
    def invite_people(self, **post):
        network_obj = request.env['groupme.network']
        partner_obj = request.env['res.partner']

        group_id = post.get('network_id')
        group = network_obj.browse(group_id)

        userRights = getUserRights(request.env.user, group)
        if not userRights.hasImportRights:
            logger.info("Unauthorized operation")
            return {'result': False, 'error': 'Unauthoorized operation'}

        partner_ids = []
        for email in post.get('email_ids'):
            if email[0] == 4:
                partner_ids.append(email[1])
            elif email[0] == 0:
                partner_email = email[2].get('name')
                partner_id = partner_obj.create({
                    'name': partner_email,
                    'email': partner_email,
                    'user_id': request.env.uid
                })
                partner_ids.append(partner_id.id)

        group.message_subscribe(partner_ids)

        return {'result': True}

    @http.route(['/networks/network/message/<model("groupme.network"):network_id>'], type='json', auth='user', methods=['POST'], website=True)
    def active_msg(self, network_id, **post):
        network_id.view_message = not network_id.view_message
        return {'result': True}

    @http.route(['/networks/network/removemember/<model("groupme.network"):network_id>/<int:memberid>'], type='json', auth='user',
                methods=['POST'], website=True)
    def removeMember(self, network_id, memberid, **post):
        try:

            userRights = getUserRights(
                request.env.user, network_id)
            if userRights.hasAdminRights:
                logger.info("Unauthoorized operation")
                return {'result': False, 'error': 'Unauthoorized operation'}

            # check authenticity
            if network_id.author_id == request.env.user:
                network_id.message_unsubscribe([memberid])
                # When a user unsubscribes,Remove respective userrights
                member = getUserRights(request.env.user, network_id)
                member.unlink()
                return {'result': True}
        except Exception, ex:
            logger.info(ex)
        return {'result': False}

    @http.route(['/networks/network/joingroup/<model("groupme.network"):network_id>'], type='json', auth='public', methods=['POST'], website=True)
    def joingroup(self, network_id, **post):
        try:
            respartner = request.env['res.partner']
            userids = respartner.sudo().search(
                [("email", "=", post["email_id"])])  # sudo required
            # lucas.jones@thinkbig.example.com
            # george.wilson@thinkbig.example.com
            # laith.jubair@axelor.example.com
            network_id.message_subscribe([userids.id])
            return {'result': True}
        except Exception, e:
            print e.message, e
            return{'result': False, 'error': 'Email Id Not Found'}

    @http.route('/networks/network/importmembers/<model("groupme.network"):network>', auth='user', type='http', website=True)
    def importusers(self, network, **post):
        # if not getUserRights(request.env.user, network).hasImportRights:
        #     return {'result': 'false'}

        c_file = post['file']
        edata = c_file.read().encode('base64')
        ddata = base64.b64decode(edata)
        userslist = ddata.split('\n')

        # to ignore the line headers,if any
        userslist = userslist[1: len(userslist)]
        user = {}
        importids = []
        for userrecord in userslist:
            try:
                user['name'], user['email'] = userrecord.split(',')
                member_idsc = request.env['res.partner'].search(
                    [('email', '=', user['email'])])
                if member_idsc:
                    importids.append(member_idsc.id)
                else:
                    logger.info(user['email'] + " Not Found")
            except Exception, e:
                logger.info("Exception" + str(e))
        network.message_subscribe(importids)
        return str(len(importids)) + " Users were imported"

    @http.route('/networks/network/sendrequest/<model("groupme.network"):network>', auth='user', type='json', website=True)
    def sendjoinrequest(self, network, **post):
        network.write({'request_ids': [(4, request.env.uid)]})
        return {'status': 'Request Sent'}

    @http.route('/networks/network/canceljoinrequest/<model("groupme.network"):network>', auth='user', type='json', website=True)
    def canceljoinrequest(self, network, **post):
        network.write({'request_ids': [(3, request.env.uid)]})
        return {'status': 'Request cancelled'}

    @http.route('/networks/network/<model("groupme.network"):network>/approverequest/', auth='user', type='json', website=True)
    def approvejoinrequest(self, network, **post):
        resuser = request.env['res.users'].search(
            [('email', '=', post['emailid'])])
        network.message_subscribe([resuser.partner_id.id])
        network.write({'request_ids': [(3, resuser.id)]})
        return {'status': 'Request approved'}

    @http.route('/networks/network/<model("groupme.network"):network>/assignrights/<model("res.partner"):respartner>', auth='user', type='json', website=True)
    def assignRights(self, network, respartner, **post):
        values = {
            'groupid': network.id,
            'partnerid': respartner.id,
            post['rights']: True
        }
        userrights = request.env['groupme.userrights']
        thisgrouprights = userrights.search(
            [('groupid', '=', network.id), ('partnerid', '=', respartner.id)])
        if thisgrouprights:
            thisgrouprights.update(values)
        else:
            userrights.create(values)
        return {'status': True}

    # JSON for Message Delivery Status Handler

    @http.route(['/networks/network/message/<model("res.partner"):partner>/<model("mail.message"):msg>/status/<status>'], type='http', website=True)
    def update_msg_status(self, partner=False, msg=False, status=False, **post):
        msgStatus_obj = request.env['groupme.message.status']

        if status == 'delivered':
            if not msgStatus_obj.search(['&', ('msg_id', '=', msg.id), ('partner_id', '=', partner.id)]):
                msgStatePost = {
                    'msg_id': msg.id,
                    'partner_id': partner.id,
                    'status': status
                }
                msgStatus_obj.create(msgStatePost)
        else:
            msgStatus_obj.search([
                '&', ('msg_id', '=', msg.id), ('partner_id', '=', partner.id)]).write({'status': 'read'})
            msgStatus_obj.status

        # return {"result", True}

    # Show Delivery Report

    @http.route('/networks/network/<model("groupme.network"):network>/message/<model("mail.message"):msg>/status', type='json', auth="public", methods=['POST'], website=True)
    def group_msg_delivery_report(self, network=False, msg=False, **post):
        msgStatus_obj = request.env['groupme.message.status'].sudo().search(
            ['&', ('msg_id', '=', msg.id), ('status', '!=', '')])

        # Fetch Records of "this" message from groupme.message.status
        #       Status contains only either msg Delivered or Read

        # Prepare return data
        records = []
        status_partner_ids = []
        for msgState in msgStatus_obj:
            row = {}
            row['name'] = msgState.partner_id.name
            row['status'] = msgState.status
            records.append(row)

            status_partner_ids.append(msgState.partner_id.id)

        # Finding msg not delivered
        # (All Members - Delivered or Read Members)
        for follower in network.message_follower_ids:
            if follower.id not in status_partner_ids:
                row = {}
                row['name'] = follower.name
                row['status'] = 'sent'
                records.append(row)
        return records


def getUserRights(resuser, network_id):
    userrights = request.env['groupme.userrights']

    return userrights.sudo().search(
        [('groupid', '=', network_id.id),
         ('partnerid', '=', resuser.partner_id.id)])
