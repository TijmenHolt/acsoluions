# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResContainerType(models.Model):
    _name = 'res.container.type'
    _description = 'Res container'
    _order = 'sequence'

    name = fields.Char(
        string='Container Type',
        required=True,
        translate=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        index=True,
        required=True
    )


class ResContainer(models.Model):
    _name = 'res.container'
    _description = 'Res container'
    _order = 'sequence'

    name = fields.Char(
        string='Container',
        required=True,
        copy=False,
        index=True,
        translate=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        index=True,
        required=True
    )
    type_id = fields.Many2one(
        'res.container.type',
        string='Container Type',
        required=True
    )
    size = fields.Float(
        string='Size'
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string="UOM",
        required=True
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="If unchecked, it will allow you to hide the container without removing it."
    )
    #
    image_1920 = fields.Image(
        string='Image',
        max_width=1920,
        max_height=1920
    )
    image_1024 = fields.Image(
        string='Image 1024',
        related='image_1920',
        max_width=1024,
        max_height=1024,
        store=True
    )
    image_512 = fields.Image(
        string='Image 512',
        related='image_1920',
        max_width=512,
        max_height=512,
        store=True
    )
    image_256 = fields.Image(
        string='Image 256',
        related='image_1920',
        max_width=256,
        max_height=256,
        store=True
    )
    image_128 = fields.Image(
        string='Image 128',
        related='image_1920',
        max_width=128,
        max_height=128,
        store=True
    )
