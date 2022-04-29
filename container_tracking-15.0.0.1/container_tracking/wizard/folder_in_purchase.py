# -*- coding: utf-8 -*-

from odoo import api, fields, models

class FolderInPurchase(models.TransientModel):
    _name = 'folder.in.purchase'
    _description = 'Link The Folder to Purchase & picking'

    folder_id = fields.Many2one(
        'res.container.folder',
        string='Folder',
        required=True
    )

    def action_apply(self):
        purchases = self.env['purchase.order'].browse(self._context.get('active_ids', []))
        for purchase in purchases.filtered(lambda a: not a.folder_id):
            purchase.write(
                {
                    'folder_id': self.folder_id.id
                }
            )