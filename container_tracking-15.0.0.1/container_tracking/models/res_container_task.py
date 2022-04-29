# -*- coding: utf-8 -*-


from odoo import api, fields, models, _, SUPERUSER_ID


class ContainerTask(models.Model):
    _name = 'res.container.task'
    _description = 'Container Task'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "priority desc, sequence, id desc"

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        folder_id = self.env.context.get('default_folder_id')
        if not folder_id:
            return False
        return self.stage_find(folder_id, [('fold', '=', False), ('is_closed', '=', False)])

    @api.model
    def _default_company_id(self):
        if self._context.get('default_folder_id'):
            return self.env['res.container.folder'].browse(self._context['default_folder_id']).company_id
        return self.env.user.company_id

    name = fields.Char(
        string='Name',
        required=True,
        translate=True
    )
    folder_id = fields.Many2one(
        'res.container.folder',
        string='Folder',
        required=True,
        index=True,
        tracking=True,
        check_company=True,
        change_default=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=_default_company_id
    )
    transport_ids = fields.Many2many(
        'res.transport',
        related='folder_id.transport_ids'
    )
    transport_id = fields.Many2one(
        'res.transport',
        string='Transport',
        required=True
    )
    transport_type = fields.Selection(
        [
            ('ship', 'Boat'),
            ('plane', 'Airplane'),
            ('truck', 'Tuck'),
            ('train', 'Train'),
        ],
        related='transport_id.transport_type',
        store=True
    )

    end_state = fields.Boolean(
        related='folder_id.end_state',
        store=True
    )
    container_id = fields.Many2one(
        'res.container',
        string='Container',
        required=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='folder_id.partner_id',
        store=True
    )
    color = fields.Integer(
        string='Color Index'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    description = fields.Html(
        string='Description'
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
        ('2', 'Urgent'),

    ], default='0',
        index=True,
        string="Priority"
    )
    sequence = fields.Integer(
        string='Sequence',
        index=True,
        default=10
    )
    stage_id = fields.Many2one(
        'container.task.type',
        string='Stage',
        related='transport_id.stage_id',
        store=True,
        group_expand='_read_group_stage_ids',

    )
    # stage_id = fields.Many2one(
    #     'container.task.type', string='Stage', compute='_compute_stage_id',
    #     store=True, readonly=False, ondelete='restrict', tracking=True, index=True,
    #     default=_get_default_stage_id,
    #     domain="[('container_ids', '=', folder_id)]", copy=False
    # )
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready'),
        ('blocked', 'Blocked')],
        string='Kanban State',
        copy=False,
        default='normal',
        required=True
    )
    date_deadline = fields.Date(
        string='Deadline',
        index=True,
        copy=False,
        tracking=True
    )
    package_level_ids_details = fields.One2many(
        'stock.move.line',
        'container_id',
        domain=[('picking_id', '!=', False), '|', ('product_qty', '=', 0.0), ('qty_done', '!=', 0.0)],
        readonly=True,
        string='Move'
    )
    picking_ids = fields.Many2many(
        'stock.picking',
        string='Pickings',
        compute='_compute_picking_ids',
        store=True
    )
    picking_count = fields.Integer(
        string='Picking count',
        compute='_compute_picking_ids',
        store=True
    )

    def action_view_picking(self):
        """ This function returns an action that display existing picking orders.
        """
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        # override the context to get rid of the default filtering on operation type
        result['context'] = {}
        pick_ids = self.mapped('picking_ids')
        # choose the view_mode accordingly
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = pick_ids.id
        return result
        
        
    @api.depends('package_level_ids_details', 'package_level_ids_details.picking_id')
    def _compute_picking_ids(self):
        for container in self:
            container.picking_ids = container.package_level_ids_details.mapped('picking_id')
            container.picking_count = len(container.picking_ids.ids)

    @api.depends('name', 'container_id')
    def name_get(self):
        res = []
        for container in self:
            name = container.name
            if container.container_id:
                name = "[%s] %s _(%s)" % (container.container_id.name, name, str(container.container_id.size))
            res += [(container.id, name)]
        return res

    @api.depends('folder_id')
    def _compute_stage_id(self):
        for rec in self:
            if rec.folder_id:
                if rec.folder_id not in rec.stage_id.container_ids:
                    rec.stage_id = rec.stage_find(rec.folder_id.id, [
                        ('fold', '=', False), ('is_closed', '=', False)])
            else:
                rec.stage_id = False

    def stage_find(self, section_id, domain=[], order='sequence'):
        """ Override of the base.stage method
            Parameter of the stage search taken from the lead:
            - section_id: if set, stages must belong to this section or
              be a default stage; if not set, stages must be default
              stages
        """
        # collect all section_ids
        section_ids = []
        if section_id:
            section_ids.append(section_id)
        section_ids.extend(self.mapped('folder_id').ids)
        search_domain = []
        if section_ids:
            search_domain = [('|')] * (len(section_ids) - 1)
            for section_id in section_ids:
                search_domain.append(('container_ids', '=', section_id))
        search_domain += list(domain)
        # perform search, return the first found
        return self.env['container.task.type'].search(search_domain, order=order, limit=1).id

    @api.model_create_multi
    def create(self, vals_list):
        default_stage = dict()
        for vals in vals_list:
            folder_id = vals.get('folder_id') or self.env.context.get('default_folder_id')
            if folder_id and not "company_id" in vals:
                vals["company_id"] = self.env["res.container.folder"].browse(
                    folder_id
                ).company_id.id or self.env.user.company_id.id
            if folder_id and "stage_id" not in vals:
                # 1) Allows keeping the batch creation of tasks
                # 2) Ensure the defaults are correct (and computed once by project),
                # by using default get (instead of _get_default_stage_id or _stage_find),
                if folder_id not in default_stage:
                    default_stage[folder_id] = self.with_context(
                        default_folder_id=folder_id
                    ).default_get(['stage_id']).get('stage_id')
                vals["stage_id"] = default_stage[folder_id]

        tasks = super().create(vals_list)
        return tasks

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        ctx = self.env.context
        search_domain = [('id', 'in', stages.ids)]
        if 'default_folder_id' in ctx:
            folder_id = self.env['res.container.folder'].browse(ctx.get('default_folder_id'))
            search_domain = ['|', ('transport_type', '=', folder_id.transport_type)] + search_domain

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
