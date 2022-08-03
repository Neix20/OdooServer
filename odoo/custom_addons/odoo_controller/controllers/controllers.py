# -*- coding: utf-8 -*-
from odoo import http
from datetime import datetime
import json
import logging

import psycopg2
import pyodbc

from odoo.custom_addons.odoo_controller.sales_order.connection import *
from odoo.custom_addons.odoo_controller.manufacturing_order.connection import *
from odoo.custom_addons.odoo_controller.delivery_order.connection import *

class OdooController(http.Controller):
    # Global Variable
    db_ssms_driver = "SQL Server Native Client 11.0"
    db_ssms_host = "47.254.234.86"
    db_ssms_name = "NTL" 
    db_ssms_username = "NTL"
    db_ssms_pwd = "ILoveVigtech88!"

    db_psql_host = "localhost"
    db_psql_name = "odoo15"
    db_psql_username = "txe1"
    db_psql_pwd = "arf11234"

    @http.route('/odoo_controller/odoo_controller', auth='public')
    def index(self):
        stmt = ""

        # Get Customer ID
        customer_models = http.request.env['res.partner'].search(
            [('name', '=', 'Deco Addict')]
        )

        cust_obj = customer_models
        stmt += f"{cust_obj['id']},&nbsp;{cust_obj['name']}<br/>"

        sku_list = ["DESK0005", "DESK0006"]

        # Get All Product
        product_models = http.request.env['product.product'].search(
            [("default_code", "in", sku_list)]
        )

        for obj in product_models:
            # Get UOM ID
            product_tmpl = http.request.env['product.template'].search(
                [("id", "=", obj["product_tmpl_id"]["id"])]
            )

            uom_id = product_tmpl['uom_id']['id']

            stmt += f"{obj['id']},&nbsp;{obj['default_code']}&nbsp;UOM ID={uom_id}<br/>"

        return stmt

    @http.route('/odoo_controller/addSO', type='json', auth='public', methods=['POST'])
    def add_sales(self):
        response = http.request.jsonrequest

        # Get Customer ID
        cust_name = response["customer"]

        customer_models = http.request.env['res.partner'].sudo().search(
            [('name', '=', cust_name)]
        )

        cust_obj = customer_models

        # Create New Sale Order Line
        sale_order_line_list = []

        product_list = response["product"]

        for product in product_list:
            sku = product['sku']
            qty = int(product['qty'])
            width = int(product['width'])
            height = int(product['height'])

            # Get Product
            product_models = http.request.env["product.product"].sudo().search(
                [('default_code', '=', sku)]
            )

            obj = product_models[0]

            # Get UOM ID
            product_tmpl = http.request.env['product.template'].sudo().search(
                [("id", "=", obj["product_tmpl_id"]["id"])]
            )

            uom_id = product_tmpl["uom_id"]["id"]

            sale_order_line_list.append(
                (0, 0, {
                    'product_id': obj["id"],
                    'product_uom': uom_id,
                    'product_uom_qty': qty
                })
            )

            sale_order_line_list.append(
                (0, 0, {
                    'name': f"[{sku}] {product_tmpl['name']}|{height}cm|{qty}",
                    'display_type': 'line_note'
                })
            )

        # Create New Sale Order
        sale_order = http.request.env['sale.order'].sudo().create(
            [{
                'partner_id': cust_obj['id'],
                'validity_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'order_line': sale_order_line_list
            }]
        )

        # Get Odoo ID and Odoo Reference
        so_id = sale_order['id']
        so_name = sale_order['name']

        # Update in NTLSystem
        conn = pyodbc.connect(
            f'Driver={self.db_ssms_driver};'
            f'Server={self.db_ssms_host};'
            f'Database={self.db_ssms_name};'
            f'uid={self.db_ssms_username};'
            f'pwd={self.db_ssms_pwd}'
        )

        # Creating the ntl cursor object
        cursor = conn.cursor()

        cursor.execute(
            "SELECT TOP 1 c.name \"Platform\", a.id "
            "FROM dbo.TNtlOrder a "
            "LEFT JOIN dbo.TNtlCustomer b "
            "ON a.customer_id = b.id "
            "LEFT JOIN dbo.TNtlPlatform c "
            "ON b.platform_id = c.id "
            "WHERE odoo_sales_no IS NULL "
            "ORDER BY a.id DESC;"
        )

        for (name, _id) in cursor:
            update_order_odoo(_id, so_id, so_name)

        # Confirm Sale Order
        sale_order.action_confirm()

        return json.dumps({
            "id": so_id,
            "name": so_name
        })

    @http.route('/odoo_controller/replenishStock', type='json', auth='public', methods=['POST'])
    def replenish_stock(self, **kwargs):
        resp = http.request.jsonrequest

        product_list = resp["product"]
        company_name = resp['company_name']

        # Get Company ID
        company_obj = http.request.env['res.company'].sudo().search(
            [('name', '=', company_name)]
        )

        for sku in product_list:
            # Get Product
            product_obj = http.request.env['product.product'].sudo().search(
                [("default_code", "=", sku)]
            )[0]

            # Replenish Stock
            stock_quant_obj = http.request.env['stock.quant'].sudo().create(
                [{
                    "product_id": product_obj['id'],
                    "company_id": company_obj['id'],
                    "location_id": 8,
                    "quantity": 50
                }]
            )

            neg_stock_quant_obj = http.request.env['stock.quant'].sudo().create(
                [{
                    "product_id": product_obj['id'],
                    "company_id": company_obj['id'],
                    "location_id": 14,
                    "quantity": -50
                }]
            )

        return resp

    @http.route('/odoo_controller/genBOM', type='json', auth='public', methods=['POST'])
    def gen_bom(self, **kwargs):
        # 1. Get All unique FG SKU (30)
        # 2. Remove First 2 characters, Link to WP (30)
        # 3. Create New WP Link to RM

        resp = http.request.jsonrequest

        sku_ls = resp["sku"]

        for sku in sku_ls:

            # Remove First 2 Characters
            sku = sku[2:]

            # Get Product Template Object
            fg_tmpl_obj = http.request.env['product.template'].sudo().search(
                    [("default_code", "=", "FG" + sku)]
            )[0]        


            wp_tmpl_obj = http.request.env['product.template'].sudo().search(
                    [("default_code", "=", "WP" + sku)]
            )[0]        

            wp_prod_obj = http.request.env["product.product"].sudo().search(
                    [("default_code", "=", "WP" + sku)]
            )[0]

            rm_tmpl_obj = http.request.env['product.template'].sudo().search(
                    [("default_code", "=", "RM" + sku)]
            )[0]        
            
            rm_prod_obj = http.request.env['product.product'].sudo().search(
                    [("default_code", "=", "RM" + sku)]
            )[0]        

            uom = resp["uom"]

            uom_obj = http.request.env["uom.uom"].sudo().search(
                    [("name", "=", uom)]
            )[0]

            wp_bom_obj = http.request.env["mrp.bom"].sudo().create(
                    [{
                        "product_tmpl_id": wp_tmpl_obj["id"],                
                        "product_qty": 50,
                        "product_uom_id": uom_obj["id"]
                    }]
            )

            wp_bom_line = http.request.env["mrp.bom.line"].sudo().create(
                    [{
                        "product_id": rm_prod_obj["id"],
                        "product_tmpl_id": rm_tmpl_obj["id"],
                        "product_qty": 1,
                        "bom_id": wp_bom_obj["id"]
                    }]
            )

            fg_bom_obj = http.request.env["mrp.bom"].sudo().create(
                    [{
                        "product_tmpl_id": fg_tmpl_obj["id"],
                        "product_qty": 1,
                        "product_uom_id": uom_obj["id"]
                    }]
            )

            fg_bom_line = http.request.env["mrp.bom.line"].sudo().create(
                    [{
                        "product_id": wp_prod_obj["id"],
                        "product_tmpl_id": wp_tmpl_obj["id"],
                        "product_qty": 1,
                        "bom_id": fg_bom_obj["id"]
                    }]
            )

        return resp

    @http.route('/odoo_controller/addDO', type='json', auth='public', methods=['POST'])
    def add_delivery_order(self, **kwargs):
        resp = http.request.jsonrequest

        # Get Sales
        order_code = resp['sale_order']

        sale_order_obj = http.request.env['sale.order'].sudo().search(
            [("name", "=", order_code)]
        )[0]

        print(sale_order_obj['id'])

        # Get Stock Picking Type Object
        stock_picking_type_obj = http.request.env["stock.picking.type"].sudo().search(
            [("name", "=", "Delivery Orders")]
        )[0]

        # Update Stock Picking
        stock_picking_obj = http.request.env['stock.picking'].sudo().search(
            [("sale_id", "=", sale_order_obj["id"])]
        )[0]

        print(stock_picking_obj["name"])

        # Confirm Stock Picking Delivery Order
        stock_picking_obj.action_confirm()

        # Update TNtlOrder
        update_do_status(order_code)

        return resp

    def get_warehouse_qty(self, sku):
        conn_psql = psycopg2.connect(
            database=self.db_psql_name,
            user=self.db_psql_username,
            password=self.db_psql_pwd,
            host=self.db_psql_host,
            port='5432'
        )

        cursor_odoo = conn_psql.cursor()

        cursor_odoo.execute(
            f"""
            SELECT b.default_code,
            SUM(a.quantity-a.reserved_quantity)
            FROM public.stock_quant a
            LEFT JOIN public.product_product b
            ON a.product_id = b.id
            WHERE 1=1
            AND a.location_id=8
            AND b.default_code='{sku}'
            GROUP BY b.default_code;
            """
        )

        warehouse_obj = cursor_odoo.fetchone()
        return float(warehouse_obj[1])

    def get_bom_qty(self, sku):
        conn_psql = psycopg2.connect(
            database=self.db_psql_name,
            user=self.db_psql_username,
            password=self.db_psql_pwd,
            host=self.db_psql_host,
            port='5432'
        )

        cursor_odoo = conn_psql.cursor()

        cursor_odoo.execute(
            f"""
            SELECT b.product_qty
            FROM product_product a
            LEFT JOIN mrp_bom b
            ON a.id = b.product_tmpl_id
            WHERE 1=1
            AND a.default_code='{sku}';
            """
        )

        obj = cursor_odoo.fetchone()
        return float(obj[0])

    @http.route('/odoo_controller/addMO', type='json', auth='public', methods=['POST'])
    def add_manufacture_order(self, **kwargs):
        resp = http.request.jsonrequest

        # Microsoft SQL Cursor
        conn_mssql = pyodbc.connect(
            f'Driver={self.db_ssms_driver};'
            f'Server={self.db_ssms_host};'
            f'Database={self.db_ssms_name};'
            f'uid={self.db_ssms_username};'
            f'pwd={self.db_ssms_pwd}'
        )

        cursor_ntl = conn_mssql.cursor()

        # Postgres Cursor
        conn_psql = psycopg2.connect(
            database=self.db_psql_name,
            user=self.db_psql_username,
            password=self.db_psql_pwd,
            host=self.db_psql_host,
            port='5432'
        )

        cursor_odoo = conn_psql.cursor()

        # Stock Name
        stock_name = resp['stock_name']
        company_name = resp['company_name']
        product_ls = resp['product']

        # Get Location ID
        location_obj = http.request.env['stock.location'].sudo().search(
            [("name", "=", stock_name)]
        )[0]

        # Get Company ID
        company_obj = http.request.env['res.company'].sudo().search(
            [("name", "=", company_name)]
        )[0]

        print(company_obj['name'])

        # Loop Through Product List
        for product in product_ls:
            sku = product['sku']
            qty = float(product['qty'])

            # Remove First 2 Characters from SKU Code
            sku = sku[2:]

            # 1. Create Manufacture Order
            manufacture_qty = qty
            warehouse_qty = self.get_warehouse_qty("FG" + sku)

            if manufacture_qty > warehouse_qty:
                diff = manufacture_qty - warehouse_qty
                bom_qty = self.get_bom_qty("WP" + sku)
                # Use Matthew Formula
                
                if (diff / bom_qty) > 1:
                    # Create WP
                    print("Hello World")

                    # Get Product
                    wp_prod_obj = http.request.env['product.product'].sudo().search(
                        [("default_code", "=", "WP" + sku)]
                    )[0]

                    # Generate Manufacture Order
                    bom_description = self.get_bom_description(wp_prod_obj['id'])

                    self.assemble_product(wp_prod_obj['id'], 50, location_obj, location_obj, company_obj)


            # 2. Create Finished Goods
            fp_prod_obj = http.request.env['product.product'].sudo().search(
                [("default_code", "=", "FG" + sku)]
            )[0]

            # Generate Manufacture Order
            bom_description = self.get_bom_description(fp_prod_obj['id'])

            self.assemble_product(fp_prod_obj['id'], manufacture_qty, location_obj, location_obj, company_obj)

            # Mark TNtlSummaryItem Status As Complete
            # update_complete_time(sku)

        return resp

    def get_bom_description(self, product_id):
        onchange_res = http.request.env['mrp.production'].sudo().onchange(
            {
                'product_id': product_id,
            },
            'product_id',
            {
                'company_id': '1',
                'product_id': '1',
                'product_qty': '1',
                'product_uom_id': '1',
                'bom_id': '1',
                'move_finished_ids': '1',
                'move_finished_ids.product_id': '1',
                'move_finished_ids.product_uom': '1',
                'move_finished_ids.product_uom_qty': '1',
                'move_finished_ids.location_id': '1',
                'move_finished_ids.location_dest_id': '1',
                'move_finished_ids.name': '',
                'move_raw_ids': '1',
                'move_raw_ids.product_id': '1',
                'move_raw_ids.name': '',
                'move_raw_ids.bom_line_id': '',
                'move_raw_ids.location_id': '1',
                'move_raw_ids.location_dest_id': '1',
                'move_raw_ids.product_uom_qty': '1',
                'move_raw_ids.product_uom': '1',
            }
        )

        return onchange_res['value']

    def assemble_product(self, product_id, qty, part_source_location, destination_location, company, origin=None):
        bom_description = self.get_bom_description(product_id)

        # Get Product ID of Material
        bom_line_obj = bom_description["move_raw_ids"][1]
        bom_line_prod_id = bom_line_obj[2]["product_id"][0]

        bom_line_prod_obj = http.request.env["product.product"].sudo().search(
            [("id", "=", bom_line_prod_id)]
        )

        manufacturing_order = http.request.env['mrp.production'].sudo().create(
            [{
                'product_id': product_id,
                'product_qty': qty,
                'product_uom_id': bom_description['product_uom_id'][0],
                'product_uom_qty': qty,
                'qty_produced': qty,
                'origin': origin,
                'move_finished_ids': [
                    [0, '', {
                        'product_id': move_finished_id[2]['product_id'][0],
                        'product_uom': move_finished_id[2]['product_uom'][0],
                        'product_uom_qty': move_finished_id[2]['product_uom_qty'],
                        'location_id': move_finished_id[2]['location_id'][0],
                        'location_dest_id': destination_location['id'],
                        'name': move_finished_id[2]['name'],
                        'byproduct_id': False
                    }]
                    for move_finished_id in bom_description['move_finished_ids'][1:]
                ],
                'move_raw_ids': [
                    [0, '', {
                        'product_id': move_raw_id[2]['product_id'][0],
                        'bom_line_id': move_raw_id[2]['bom_line_id'][0],
                        'product_uom': move_raw_id[2]['product_uom'][0],
                        'product_uom_qty': move_raw_id[2]['product_uom_qty'],
                        'location_id': part_source_location['id'],
                        'location_dest_id': move_raw_id[2]['location_dest_id'][0],
                        'name': move_raw_id[2]['name']
                    }]
                    for move_raw_id in bom_description['move_raw_ids'][1:]
                ]
            }]
        )

        manufacturing_order.sudo().action_confirm()

        # Create New Lot
        bom_lot = http.request.env['stock.production.lot'].sudo().create(
            [{
                'product_id': bom_line_prod_id,
                'company_id': company["id"]
            }]
        )[0]

        parent_lot = http.request.env['stock.production.lot'].sudo().create(
            [{
                'product_id': product_id,
                'company_id': company["id"]
            }]
        )[0]

        manufacturing_order.sudo().update({
            'lot_producing_id': parent_lot["id"]
        })

        immediate_production = http.request.env['mrp.immediate.production'].sudo().create({
            'immediate_production_line_ids': [
                [0, '', {
                    'production_id': manufacturing_order.id,
                    'to_immediate': True
                }]
            ]
        })

        immediate_production.sudo().process()

        # Get Stock Move Based on Product ID
        stock_move_obj = http.request.env["stock.move"].sudo().search(
            [("product_id", "=", bom_line_prod_id)]
        )[0]

        # Search Existing Stock Move Line Based on Stock Move ID
        stock_move_line_obj = http.request.env["stock.move.line"].sudo().search(
            [("move_id", "=", stock_move_obj["id"])]
        )[0]

        # Update Stock Move Line with Lot ID
        stock_move_line_obj.sudo().update({
            'lot_id': bom_lot["id"]
        })

        # manufacturing_order.sudo().button_mark_done()

        print(f"Successfully generated Manufactured Order {manufacturing_order['name']}!")
