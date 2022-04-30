{
    'name': 'Container tracking',
    'version': '15.0.0.1',
    'summary': 'Container tracking',
    'category': 'Stock',
    'author': 'Osis',
    'website': 'https://www.osis.dz',
    'license': 'OPL-1',
    'depends': ['stock', 'purchase_stock', 'mail', 'utm'],
    'data': [

        'security/ir.model.access.csv',
        'data/data.xml',
        'data/ir_sequence_data.xml',
        'data/folder_stage_data.xml',

        'views/folder_checklist_view.xml',
        'views/folder_stage.xml',
        'views/container_task_type.xml',
        'views/res_transport.xml',
        'views/res_container.xml',
        'views/res_container_folder.xml',
        'views/res_container_task.xml',
        'views/purchase_order_views.xml',
        'views/stock_move.xml',
        'views/stock_move_line.xml',
        'views/stock_picking_views.xml',

        'wizard/put_in_container_views.xml',
        'wizard/folder_in_purchase_views.xml',
        'wizard/res_container_confirmation_views.xml',

        'views/menuitem.xml'

    ],
    'demo': [],
    'images': ['static/description/banner.png'],
    'pre_init_hook':'pre_init_check',
    'price': 140,
    'currency': "EUR",

    'external_dependencies': {
        'python': [],
    },
    
    'installable': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'container_tracking/static/src/scss/menu_kb_style.scss'
        ],
        'web.report_assets_common': [
        ],
        'web.qunit_suite_tests': [
        ],
        'web.assets_qweb': [
        ],
    },
}
