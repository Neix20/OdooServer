import logging
import psycopg2
import pyodbc

# Global Variable
db_ssms_host = "47.254.234.86"
db_ssms_name = "NTL" 
db_ssms_username = "NTL"
db_ssms_pwd = "ILoveVigtech88!"

db_psql_host = "localhost"
db_psql_name = "odoo_new"
db_psql_username = "txe1"
db_psql_pwd = "arf11234"

# Connect with NTL database
conn_mssql = pyodbc.connect(
    'Driver={SQL Server Native Client 11.0};'
    f'Server={db_ssms_host};'
    f'Database={db_ssms_name};'
    f'uid={db_ssms_username};'
    f'pwd={db_ssms_pwd}'
)

# Creating the ntl cursor object
cursor_ntl = conn_mssql.cursor()

# Connect with Odoo database
conn_psql = psycopg2.connect(
    database=db_psql_name,
    user=db_psql_username,
    password=db_psql_pwd,
    host=db_psql_host,
    port='5432'
)

# Creating the odoo cursor object
cursor_odoo = conn_psql.cursor()


def update_order_odoo(order_id, SO_id, SO_name):
    """
        update odoo id on ntl database
    :param order_id:
    :param SO_id:
    :param SO_name:
    """
    try:
        cursor_ntl.execute(f"SELECT * FROM TNtlOrder WHERE id={order_id}")
        order_info = ""

        for i in cursor_ntl:
            order_info = i

        # Update Odoo Reference Number
        order_info[8] = SO_id
        order_info[9] = SO_name

        # Generate List from Values of Order Info
        ls = list(map(str, [*order_info]))

        # Join Order Info into single query statement
        stmt = "', '".join(ls)

        # Replace None with Null
        stmt = stmt.replace("'None'", "NULL")

        # Execute Update Query With Value
        cursor_ntl.execute(f"EXEC NSP_TNtlOrder_Update '{stmt}';")
        cursor_ntl.commit()

        logging.info(f"EXEC NSP_TNtlOrder_Update '{stmt}';")
    except Exception as e:
        return e


if __name__ == '__main__':
    update_order_odoo("", "", "")
