# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from builtins import super

from odoo import fields, models, _, api
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
import json


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    folder_id = fields.Many2one(
        'res.container.folder',
        related='purchase_id.folder_id',
        store=True,
    )
    show_update_container = fields.Boolean(
        string='Has Cancel Changed',
        compute='_show_update_container',
        store=True
    )

    @api.depends('move_line_ids_without_package.qty_to_done', 'move_line_ids_without_package.qty_done')
    def _show_update_container(self):
        for picking in self:
            if any(picking.move_line_ids_without_package.filtered(
                    lambda a: a.container_id and a.qty_done == 0 and a.qty_to_done != 0)):
                picking.show_update_container = True
            else:
                picking.show_update_container = False

    def update_line_container(self):
        for line in self.move_line_ids_without_package.filtered(
                lambda a: a.container_id and a.qty_done == 0 and a.qty_to_done != 0):
            line.qty_done = line.qty_to_done

    def do_unreserve(self):
        res = super(StockPicking, self).do_unreserve()
        for picking in self:
            picking.move_line_ids_without_package._do_unreserve_containter()
        return res

    def action_put_in_container(self):
        self.ensure_one()
        if self.state not in ('done', 'cancel'):
            picking_move_lines = self.move_line_ids
            if (
                    not self.picking_type_id.show_reserved
                    and not self.env.context.get('barcode_view')
            ):
                picking_move_lines = self.move_line_nosuggest_ids

            move_line_ids = picking_move_lines.filtered(
                lambda ml: float_compare(ml.qty_done, 0.0, precision_rounding=ml.product_uom_id.rounding) > 0
                           and not ml.container_id
            )

            if not move_line_ids:
                move_line_ids = picking_move_lines.filtered(
                    lambda ml: float_compare(ml.product_uom_qty, 0.0,
                                             precision_rounding=ml.product_uom_id.rounding) > 0 and float_compare(
                        ml.qty_done, 0.0,
                        precision_rounding=ml.product_uom_id.rounding) == 0
                )

            if move_line_ids:
                ctx = self._context.copy()

                if not self.folder_id:
                    raise UserError(_("Please Make sure to have your folder."))

                stage_ids = self.folder_id.mapped('type_ids').filtered(lambda a: not a.is_closed)
                if not stage_ids:
                    raise UserError(_("Please Create your stages before."))

                ctx.update(
                    {
                        'folder_id': self.folder_id.id,
                        'default_folder_id': self.folder_id.id,
                        'stage_id': stage_ids.ids,
                        'default_stage_ids': stage_ids.ids,
                        'picking_id': self.id,
                        'default_picking_id': self.id,
                        'move_line_ids': move_line_ids.ids,
                        'default_move_line_ids': move_line_ids.ids
                    }
                )
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'put.in.container',
                    'target': 'new',
                    'context': ctx,

                }
            else:
                raise UserError(_("Please add 'Done' quantities to the picking to create a new container."))

    ########################################
    ###########################

    def button_validate(self):
        ctx = self.env.context

        if ctx.get('no_action_generate_container_wizard'):
            return super().button_validate()

        if ctx.get('folder_id') or self.folder_id:
            return self._action_generate_container_wizard()

        return super().button_validate()

    def _action_generate_container_wizard(self):
        view = self.env.ref('container_tracking.view_res_container_confirmation')
        container_ids = self.move_line_ids_without_package.mapped('container_id').ids
        return {
            'name': _('Select Containers'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'res.container.confirmation',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(self.env.context, default_picking_id=self.id, default_folder_id=self.folder_id.id,
                            default_container_ids=container_ids,
                            default_containers=container_ids
                            )

        }

    def _create_backorder(self):
        """ This method is called when the user chose to create a backorder. It will create a new
        picking, the backorder, and move the stock.moves that are not `done` or `cancel` into it.
        """
        ctx = self.env.context
        if not ctx.get('lines'):
            return super()._create_backorder()

        backorders = self.env['stock.picking']
        for picking in self:
            # stock.move
            moves_to_backorder = picking.move_lines.filtered(lambda x: x.state not in ('done', 'cancel'))
            if moves_to_backorder:
                purchase_id = picking.purchase_id and picking.purchase_id.id or False
                backorder_picking = picking.copy({
                    'name': '/',
                    'move_lines': [],
                    'move_line_ids': [],
                    'backorder_id': picking.id,
                    'purchase_id': purchase_id,
                })
                picking.message_post(
                    body=_(
                        'The backorder <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> has been created.') % (
                             backorder_picking.id, backorder_picking.name))

                moves_to_backorder.write({'picking_id': backorder_picking.id})
                moves_to_backorder.mapped('package_level_id').write({'picking_id': backorder_picking.id})
                moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})

                #backorder_picking.action_assign()
                NewLine = self.env['stock.move.line'].browse(ctx.get('lines'))
                for move_line in moves_to_backorder.mapped('move_line_ids'):
                    lines = NewLine.filtered(lambda a: a.product_id.id == move_line.product_id.id)
                    if not lines:
                        continue
                    move_line.write(
                        {
                            'qty_done': lines[0].qty_to_done,
                            'container_id': lines[0].container_id and lines[0].container_id.id or False,
                        }
                    )
                    if len(lines) > 1:
                        for line in lines[1:]:
                            line.write(
                                {
                                    'qty_done': line.qty_to_done,
                                    'move_id': move_line.move_id.id,
                                    'picking_id': backorder_picking.id,
                                }
                            )
                backorders |= backorder_picking
                return backorders
