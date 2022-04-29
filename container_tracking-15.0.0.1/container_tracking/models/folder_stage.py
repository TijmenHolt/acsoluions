# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Stage(models.Model):
    _name = "folder.stage"
    _description = "Folder Stages"
    _rec_name = 'name'
    _order = "sequence, name, id"

    name = fields.Char(
        string='Stage Name',
        required=True,
        translate=True
    )
    active = fields.Boolean(
        default=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=1,
        help="Used to order stages. Lower is better."
    )
    fold = fields.Boolean(
        string='Folded in Pipeline',
        help='This stage is folded in the kanban view when there '
             'are no records in that stage to display.'
    )
    end = fields.Boolean(
        string='End of Stage'
    )
    folder_checklist = fields.Many2many(
        'folder.checklist',
        string='Check List (Stage)'
    )


class FolderChecklist(models.Model):
    _name = 'folder.checklist'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Checklist for the folder'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    description = fields.Html(
        string='Description',
        translate=True
    )
    doc_count = fields.Integer(
        compute='_compute_attached_docs_count',
        string="Number of documents attached"
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    stages = fields.Many2many(
        'folder.stage',
        string='Stages'
    )

    def attachment_tree_view(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]

        action['domain'] = str([
            '|',
            '&',
            ('res_model', '=', 'folder.checklist'),
            ('res_id', 'in', self.ids),
            '&',
            ('res_model', '=', 'folder.checklist'),
            ('res_id', 'in', self.ids)
        ])
        action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        return action

    def _compute_attached_docs_count(self):
        Attachment = self.env['ir.attachment']
        for checklist in self:
            checklist.doc_count = Attachment.search_count([
                '&',
                ('res_model', '=', 'folder.checklist'), ('res_id', '=', checklist.id)
            ])
