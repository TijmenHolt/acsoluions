# -*- coding: utf-8 -*-

from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    folder_id = fields.Many2one(
        'res.container.folder',
        related='picking_id.folder_id',
        store=True,
    )
    # container_id = fields.Many2one(
    #     'res.container.task',
    #     copy=True
    # )

    @api.depends('product_id', 'has_tracking', 'move_line_ids', 'folder_id')
    def _compute_show_details_visible(self):
        """ According to this field, the button that calls `action_show_details` will be displayed
        to work on a move from its picking form view, or not.
        """
        has_package = self.user_has_groups('stock.group_tracking_lot')
        multi_locations_enabled = self.user_has_groups('stock.group_stock_multi_locations')
        consignment_enabled = self.user_has_groups('stock.group_tracking_owner')

        show_details_visible = multi_locations_enabled or has_package

        for move in self:
            if not move.product_id:
                move.show_details_visible = False
            elif move.folder_id:
                move.show_details_visible = True
            else:
                move.show_details_visible = ((show_details_visible or move.has_tracking != 'none') and
                                             (move.state != 'draft' or (move.picking_id.immediate_transfer and move.state == 'draft')) and
                                             move.picking_id.picking_type_id.show_operations is False)
