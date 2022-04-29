# -*- coding: utf-8 -*-

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    folder_id = fields.Many2one(
        'res.container.folder',
        related='move_id.folder_id',
        store=True,
    )
    transport_type = fields.Selection(
        related='folder_id.transport_type',
        store=True
    )
    container_id = fields.Many2one(
        'res.container.task',
        string='Container',
        copy=True
    )
    arrival_date = fields.Date(
        related='container_id.transport_id.arrival',
        string='Arrival date',
        store=True
    )
    qty_to_done = fields.Float(
        string='Qty to done',
        copy=False
    )

    def _do_unreserve_containter(self):
        self.container_id = False
