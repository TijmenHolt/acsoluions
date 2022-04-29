# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class ResTransport(models.Model):
    _name = 'res.transport'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Res transport'

    def _reference_sequence(self):
        return self.env['ir.sequence'].next_by_code('res.transport') or _('New')

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        transport_type = self.env.context.get('default_transport_type')
        if not transport_type:
            return False
        return self.stage_find(transport_type, [('fold', '=', False), ('is_closed', '=', False)])

    def stage_find(self, transport_type, domain=[], order='sequence'):
        search_domain = [('transport_type', '=', transport_type)]
        # perform search, return the first found
        return self.env['container.task.type'].search(search_domain, order=order, limit=1).id

    name = fields.Char(
        string='Name',
        required=True
    )
    reference = fields.Char(
        string='Reference',
        default=_reference_sequence
    )
    transport_type = fields.Selection(
        [
            ('ship', 'Boat'),
            ('plane', 'Airplane'),
            ('truck', 'Tuck'),
            ('train', 'Train'),
        ], string='Transport type',
        required=True
    )
    departure = fields.Date(
        string='Departure',
        required=True,
        default=fields.Date.today
    )
    arrival = fields.Date(
        string='Arrival',
        required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date())
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    color = fields.Integer(
        string='Color Index'
    )
    container_ids = fields.One2many(
        'res.container.task',
        'transport_id',
        string='Containers'
    )
    container_count = fields.Integer(
        compute='_container_count',
        string='Container count',
        store=True
    )
    product_ids = fields.Many2many(
        'product.product',
        compute='_container_product_id',
        store=True
    )
    stage_id = fields.Many2one(
        'container.task.type',
        string='Stage',
        compute='_compute_stage_id',
        group_expand='_read_group_stage_ids',
        store=True, readonly=False, ondelete='restrict', tracking=True, index=True,
        default=_get_default_stage_id,
        domain="[('transport_type', '=', transport_type)]", copy=False
    )
    folder_id = fields.Many2one(
        'res.container.folder',
        string='Folder',
        ondelete='cascade',
        index=True,
        copy=False
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='folder_id.partner_id',
        store=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company.id
    )
    
    @api.depends('container_ids')
    def _container_count(self):
        for rec in self:
            rec.container_count = len(rec.container_ids.ids)

    def action_view_container(self):
        """ This function returns an action that display existing Containers.
        """
        action = self.env.ref('container_tracking.res_container_task_boat_action')
        result = action.read()[0]
        # override the context to get rid of the default filtering on operation type
        result['context'] = {}
        pick_ids = self.mapped('container_ids')
        result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)

        return result

    @api.depends('container_ids.package_level_ids_details', 'container_ids.package_level_ids_details.product_id')
    def _container_product_id(self):
        for rec in self:
            rec.product_ids = rec.container_ids.mapped('package_level_ids_details').mapped('product_id').ids

    @api.depends('transport_type')
    def _compute_stage_id(self):
        for rec in self:
            if rec.transport_type:
                if rec.transport_type != rec.stage_id.transport_type:
                    rec.stage_id = rec.with_context(transport_type=rec.transport_type).stage_find(rec.transport_type, [
                        ('fold', '=', False), ('is_closed', '=', False)])
            else:
                rec.stage_id = False

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        ctx = self._context
        search_domain = [('id', 'in', stages.ids)]
        if 'default_folder_id' in self.env.context:
            folder_id = self.env['res.container.folder'].browse(ctx.get('default_folder_id'))
            search_domain = ['|', ('transport_type', '=', folder_id.transport_type)] + search_domain

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
