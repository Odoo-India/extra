# -*- coding: utf-8 -*-
{
    'name': "Group Me",

    'summary': """
        One way news publication in Groups, can be used by Club Members, School, Colleges announcements
        """,

    'description': """
        One way news publication in Groups, can be used by Club Members, School, Colleges announcements
    """,

    'author': "Odoo SA",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Mobile',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
