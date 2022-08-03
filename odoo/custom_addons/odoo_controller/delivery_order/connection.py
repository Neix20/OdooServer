import pyodbc
import logging

# Global Variable
db_ssms_host = "47.254.234.86"
db_ssms_name = "NTL" 
db_ssms_username = "NTL"
db_ssms_pwd = "ILoveVigtech88!"

conn = pyodbc.connect(
    'Driver={SQL Server Native Client 11.0};'
    f'Server={db_ssms_host};'
    f'Database={db_ssms_name};'
    f'uid={db_ssms_username};'
    f'pwd={db_ssms_pwd}'
)


def update_do_status(id):
    cursor = conn.cursor()

    s_sta_id = 15

    cursor.execute(f"SELECT * FROM TNtlOrder WHERE odoo_sales_no='{id}';")

    obj_list = [_obj for _obj in cursor]

    for _obj in obj_list:
        obj = _obj

        # Update Status To Sale
        obj[12] = s_sta_id

        # Generate List from Values of Order Info
        ls = list(map(str, [*obj]))

        # Join Order Info into single query statement
        stmt = "', '".join(ls)

        # Replace None with Null
        stmt = stmt.replace("'None'", "NULL")

        print(f"EXEC NSP_TNtlOrder_Update '{stmt}';")

        # Execute Update Query With Value
        cursor.execute(f"EXEC NSP_TNtlOrder_Update '{stmt}';")
        cursor.commit()

        logging.info(f"EXEC NSP_TNtlOrder_Update '{stmt}';")

if __name__ == '__main__':
    update_do_status("")
