# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError, RedirectWarning
from datetime import date, datetime, timedelta
from lxml import etree

AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]


class ContainerTaskChecklist(models.Model):
    _name = 'container.task.checklist'
    _description = 'Checklist for the task'

    name = fields.Char(
        string='Name',
        required=True
    )
    description = fields.Char(
        string='Description'
    )


class ResContainerFolder(models.Model):
    _name = 'res.container.folder'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Res container folder'
    _order = "priority desc, id desc"
    _check_company_auto = True

    def action_print(self):
        return

    def attachment_tree_view(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['domain'] = str([
            '|',
            '&',
            ('res_model', '=', 'res.container.folder'),
            ('res_id', 'in', self.ids),
            '&',
            ('res_model', '=', 'res.container.task'),
            ('res_id', 'in', self.task_ids.ids)
        ])
        action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        return action

    def _compute_attached_docs_count(self):
        Attachment = self.env['ir.attachment']
        for project in self:
            project.doc_count = Attachment.search_count([
                '|',
                '&',
                ('res_model', '=', 'res.container.folder'), ('res_id', '=', project.id),
                '&',
                ('res_model', '=', 'res.container.task'), ('res_id', 'in', project.task_ids.ids)
            ])

    def _get_default_favorite_user_ids(self):
        return [(6, 0, [self.env.uid])]

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        return self.env['folder.stage'].search([], limit=1).id

    def _get_default_transition_stage(self):
        """ Gives default transition """
        return self.env['container.task.type'].search(
            [
                ('transport_type', '!=', False),
                ('transport_type', '=', self.transport_type)
            ]
        ).ids

    @api.onchange('transport_type')
    def onchange_transport_type(self):
        for record in self:
            record.type_ids = [(5, 0, 0)] + [(6, 0, self._get_default_transition_stage())]

    name = fields.Char(
        string='Name',
        required=True,
        copy=False,
        index=True,
        translate=True
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    transport_type = fields.Selection(
        [
            ('ship', 'Boat'),
            ('plane', 'Airplane'),
            ('truck', 'Tuck'),
            ('train', 'Train'),
        ], string='Transport type',
        required=True,
        tracking=3
    )
    kanban_state = fields.Selection([
        ('grey', 'No next activity planned'),
        ('red', 'Next activity late'),
        ('green', 'Next activity is planned')],
        string='Kanban State',
        compute='_compute_kanban_state'
    )
    priority = fields.Selection(
        AVAILABLE_PRIORITIES,
        string='Priority',
        index=True,
        default=AVAILABLE_PRIORITIES[0][0]
    )
    doc_count = fields.Integer(
        compute='_compute_attached_docs_count',
        string="Number of documents attached"
    )
    is_favorite = fields.Boolean(
        compute='_compute_is_favorite',
        inverse='_inverse_is_favorite',
        string='Show Folder on dashboard',
        help="Whether this project should be displayed on your dashboard."
    )
    favorite_user_ids = fields.Many2many(
        'res.users',
        default=_get_default_favorite_user_ids,
        string='Members'
    )
    color = fields.Integer(
        string='Color Index'
    )
    code = fields.Char(
        string='Reference',
        default=True
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        required="True"
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        tracking="1"

    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        required="True"

    )
    partner_email = fields.Char(
        string='Email',
        related='partner_id.email',
        store=True
    )
    partner_phone = fields.Char(
        string='Phone',
        related='partner_id.phone',
        store=True
    )
    stage_id = fields.Many2one(
        'folder.stage',
        string='Stage',
        index=True,
        group_expand='_read_group_stage_ids',
        copy=False,
        ondelete='restrict',
        default=_get_default_stage_id,
        tracking=2
    )
    end_state = fields.Boolean(
        related='stage_id.end',
        store=True
    )
    expected_depense = fields.Monetary(
        'Expected depense',
        currency_field='company_currency'
    )
    company_currency = fields.Many2one(
        "res.currency",
        string='Currency',
        related='company_id.currency_id'
    )
    currency_id = fields.Many2one(
        "res.currency",
        string='Currency',
        related='partner_id.currency_id',
        store=True
    )
    sequence = fields.Integer(
        default=10
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id
    )
    type_ids = fields.Many2many(
        'container.task.type',
        string='Tasks Stages',
        # default=_get_default_transition_stage
    )
    checklist_related = fields.Many2many(
        'folder.checklist',
        string='Checklists related',
        compute='_folder_checklist',
    )
    checklist_progress = fields.Float(
        compute='_checklist_progress',
        string='Progress',
        store=True,
        default=0.0
    )
    max_rate = fields.Integer(
        string='Maximum rate',
        default=100
    )
    checklist_ids = fields.Many2many(
        'folder.checklist',
        string='Checklists'
    )
    task_ids = fields.One2many(
        'res.container.task',
        'folder_id',
        string='Tasks',
        domain=[('stage_id', '=', False)]
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        compute='_chekclist_attachment',
    )
    transport_ids = fields.Many2many(
        'res.transport',
        string='Transports'
    )
    supplier_purchase_count = fields.Integer(
        compute='_compute_supplier_purchase_count',
        string='# Purchase Orders',
        compute_sudo=True
    )
    amount_total = fields.Monetary(
        compute='_compute_amount_total',
        string='# Amount Total',
        currency_field='company_currency',
        compute_sudo=True
    )
    country_source = fields.Many2one(
        'res.country',
        string='Country Source',
        related='partner_id.country_id',
        store=True
    )
    country_source_image_url = fields.Char(
        related='country_source.image_url'
    )
    country_destination = fields.Many2one(
        'res.country',
        string='Country Destination',
        default=lambda self: self.env.user.company_id.country_id.id
    )
    country_destination_image_url = fields.Char(
        related='country_destination.image_url',
    )
    container_count = fields.Integer(
        compute='_compute_container_count',
        string="Container Count"
    )

    def _compute_container_count(self):
        container_data = self.env['res.container.task'].read_group(
            [
                ('folder_id', 'in', self.ids), '|', '&',
                ('stage_id.is_closed', '=', False),
                ('stage_id.fold', '=', False),
                ('stage_id', '=', False)
            ], ['folder_id'], ['folder_id']
        )
        result = dict((data['folder_id'][0], data['folder_id_count']) for data in container_data)
        for container in self:
            container.container_count = result.get(container.id, 0)

    def create_folder(self):
        return

    def action_view_purchases(self):
        action = {
            'name': _('Purchase Order(s)'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'target': 'current',
        }
        purchase_order_ids = self.env['purchase.order'].sudo().search(
            [
                ('folder_id', '=', self.id)
            ]
        )
        if len(purchase_order_ids) == 1:
            action['res_id'] = purchase_order_ids[0].id
            action['view_mode'] = 'form'
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', purchase_order_ids.ids)]
            action['context'] = {'folder_id': self.id, 'default_folder_id': self.id}

        return action

    def _compute_supplier_purchase_count(self):
        container_data = self.env['purchase.order'].read_group(
            [
                ('folder_id', 'in', self.ids)
            ], ['folder_id'], ['folder_id']
        )
        result = dict((data['folder_id'][0], data['folder_id_count']) for data in container_data)
        for container in self:
            container.supplier_purchase_count = result.get(container.id, 0)

    def _compute_amount_total(self):
        amount_total = 0.0
        for folder_id in self:
            supplier_purchase_groups = self.env['purchase.order'].search(
                [('folder_id', '=', folder_id.id)]
            )

            for order in supplier_purchase_groups:
                amount_total += folder_id.company_currency._convert(
                    order.amount_total,
                    order.currency_id,
                    order.company_id,
                    order.date_order
                )
            folder_id.update({
                'amount_total': amount_total,
            })

    @api.depends('stage_id')
    def _chekclist_attachment(self):
        AttObj = self.env['ir.attachment']
        for rec in self:
            atts = AttObj.search(
                [
                    ('res_model', '=', 'folder.checklist'),
                    ('res_id', 'in', rec.checklist_related.ids)
                ]
            )
            rec.attachment_ids = atts

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):

        res = super(
            ResContainerFolder, self
        ).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu
        )

        if view_type in ['kanban', ]:
            doc = etree.XML(res['arch'])
            for field in res['fields']:
                if field in 'checklist_progress':
                    # for node in doc.xpath(
                    # "//field[@name='%s']" % field):
                    # new_field = ' '
                    # node.set('string', _(new_field))
                    # res['arch'] = etree.tostring(doc, encoding='unicode')
                    res['fields']['checklist_progress']['string'] = ''
        return res

    @api.depends('checklist_ids', 'stage_id', 'checklist_related')
    def _checklist_progress(self):
        for rec in self:
            total_len = len(rec.checklist_related)
            if total_len != 0:
                check_list_len = len(rec.checklist_ids.filtered(lambda x: x.id in rec.checklist_related.ids))
                rec.checklist_progress = (check_list_len * 100) / total_len
            else:
                rec.checklist_progress = 0

    @api.depends('stage_id')
    def _folder_checklist(self):
        for record in self:
            record.checklist_related = record.stage_id.mapped('folder_checklist')

    def action_purchase_quotations_new(self):
        purchase_action = self.env.ref('container_tracking.purchase_action_quotations_new')
        action = purchase_action.read()[0]
        action['context'] = {
            'search_default_folder_id': self.id,
            'default_folder_id': self.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_origin': self.code,
            'default_company_id': self.company_id.id or self.env.company.id,
        }
        return action

    @api.depends('activity_date_deadline')
    def _compute_kanban_state(self):
        today = date.today()
        for folder in self:
            kanban_state = 'grey'
            if folder.activity_date_deadline:
                folder_date = fields.Date.from_string(folder.activity_date_deadline)
                if folder_date >= today:
                    kanban_state = 'green'
                else:
                    kanban_state = 'red'
            folder.kanban_state = kanban_state

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['folder.stage'].search([])
        return stage_ids

    def unlink(self):
        # Check Folder if empty
        for folder in self:
            if folder.container_count:
                raise UserError(_('You cannot delete a Folder containing containers. '
                                  'You can either archive it or first delete all of its containers.')
                                )
        return super().unlink()

    @api.model
    def create(self, vals):
        vals['code'] = self.env['ir.sequence'].next_by_code('res.container.folder') or _('New')
        res = super().create(vals)
        transport_ids = res.mapped('transport_ids').write({'folder_id': res.id})
        return res

    def write(self, vals):
        result = super().write(vals)
        if 'transport_ids' in vals:
            for record in self:
                record.mapped('transport_ids').write({'folder_id': record.id})
        return result

    def _compute_is_favorite(self):
        for folder in self:
            folder.is_favorite = self.env.user in folder.favorite_user_ids

    def _inverse_is_favorite(self):
        favorite_folders = not_fav_folders = self.env['res.container.folder'].sudo()
        for folder in self:
            if self.env.user in folder.favorite_user_ids:
                favorite_folders |= folder
            else:
                not_fav_folders |= folder

        # Folder User has no write access for folder.
        not_fav_folders.write({'favorite_user_ids': [(4, self.env.uid)]})
        favorite_folders.write({'favorite_user_ids': [(3, self.env.uid)]})
