# -*- coding: utf-8 -*-
{
    'name': "electronicos_nomina",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','base_electronicos','hr_payroll','l10n_co_bases'], #,'consolidated_payroll'

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_message.xml',
        'data/data.xml',
        'views/views.xml',
        'views/templates.xml',
        #'views/consolidated_payroll.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}