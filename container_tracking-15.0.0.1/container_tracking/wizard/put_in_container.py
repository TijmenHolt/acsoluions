# -*- coding: utf-8 -*-


from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class MovePutInContainer(models.TransientModel):
    _name = 'put.in.container'
    _description = 'Put Move line in container'
    _order = 'id desc'

    folder_id = fields.Many2one(
        'res.container.folder',
        string='Folder',
        required=True
    )
    stage_ids = fields.Many2many(
        'container.task.type',
        string='Stage',
        required=True
    )
    container_id = fields.Many2one(
        'res.container.task',
        string='Container',
        required=True
    )
    picking_id = fields.Many2one(
        'stock.picking',
        string='Stock Picking',
        required=True
    )
    move_line_ids = fields.Many2many(
        'stock.move.line',
        string='Stock move line',
        required=True
    )


    def action_apply(self):
        containers = False
        for pick in self:
            move_lines_to_pack = self.env['stock.move.line']
            container = pick.container_id

            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_is_zero(pick.move_line_ids[0].qty_done, precision_digits=precision_digits):
                for line in pick.move_line_ids:
                    line.qty_done = line.product_uom_qty

            for ml in pick.move_line_ids:
                if float_compare(
                        ml.qty_done,
                        ml.product_uom_qty,
                        precision_rounding=ml.product_uom_id.rounding
                ) >= 0:
                    move_lines_to_pack |= ml
                else:
                    quantity_left_todo = float_round(
                        ml.product_uom_qty - ml.qty_done,
                        precision_rounding=ml.product_uom_id.rounding,
                        rounding_method='UP'
                    )
                    done_to_keep = ml.qty_done
                    new_move_line = ml.copy(
                        default={
                            'product_uom_qty': 0,
                            'qty_done': ml.qty_done
                        }
                    )
                    vals = {
                        'product_uom_qty': quantity_left_todo,
                        'qty_done': 0.0
                    }
                    if pick.picking_id.picking_type_id.code == 'incoming':
                        if ml.lot_id:
                            vals['lot_id'] = False
                        if ml.lot_name:
                            vals['lot_name'] = False
                    ml.write(vals)
                    new_move_line.write(
                        {
                            'product_uom_qty': done_to_keep
                        }
                    )
                    move_lines_to_pack |= new_move_line

            move_lines_to_pack.write({
                'container_id': container.id,
            })
        return container