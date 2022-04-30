# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ContainerTaskType(models.Model):
    _name = 'container.task.type'
    _description = 'Task Stage'
    _order = 'sequence, id'

    def _get_default_container_ids(self):
        default_container_id = self.env.context.get('default_container_id')
        return [default_container_id] if default_container_id else None

    name = fields.Char(
        string='Stage Name',
        required=True,
        translate=True
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
    task_checklist_ids = fields.Many2many(
        'container.task.checklist',
        string='Check List'
    )
    fold = fields.Boolean(
        string='Folded in Pipeline',
        help='This stage is folded in the kanban view when there '
             'are no records in that stage to display.'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    description = fields.Text(
        translate=True
    )
    sequence = fields.Integer(
        default=1
    )
    container_ids = fields.Many2many(
        'res.container.folder',
        string='Folders',
        default=_get_default_container_ids
    )
    is_closed = fields.Boolean(
        'Closing Stage',
        help="Tasks in this stage are considered as closed."
    )
    legend_blocked = fields.Char(
        string='Red Kanban Label',
        default=lambda s: _('Blocked'),
        translate=True,
        required=True,
    )
    legend_done = fields.Char(
        'Green Kanban Label',
        default=lambda s: _('Ready'),
        translate=True,
        required=True,
    )
    legend_normal = fields.Char(
        string='Grey Kanban Label',
        default=lambda s: _('In Progress'),
        translate=True,
        required=True
    )
    deadline = fields.Integer(
        string='Deadline (Days)',
        default=10
    )