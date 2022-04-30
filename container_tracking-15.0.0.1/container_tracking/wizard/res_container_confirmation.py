# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResContainerConfirmation(models.TransientModel):
    _name = 'res.container.confirmation'
    _description = 'Container confirmation Wizard'

    folder_id = fields.Many2one(
        'res.container.folder',
        string='Folder',
        required=True
    )
    picking_id = fields.Many2one(
        'stock.picking',
        string='Picking',
        required=True
    )
    container_ids = fields.Many2many(
        'res.container.task',
        string='Containers',
        required=True
    )
    containers = fields.Many2many(
        'res.container.task',
        'res_container_rel',
        string='Containers',
        required=True
    )

    def action_apply(self):
        for confirmation in self:
            lines = confirmation.picking_id.move_line_ids_without_package.filtered(
                lambda a: a.container_id and a.container_id.id not in confirmation.container_ids.ids
            )
            newlines = []
            for line in lines:
                backorder_picking = line.copy({
                    'move_id': False,
                    'picking_id': False,
                    'qty_to_done': line.qty_done,
                    'container_id': line.container_id and line.container_id.id or False
                })
                line.write(
                    {
                        'qty_to_done': line.qty_done,
                        'qty_done': 0,

                    }
                )
                newlines.append(backorder_picking.id)

            return confirmation.picking_id.with_context(no_action_generate_container_wizard=True,
                                                        lines=newlines).button_validate()
