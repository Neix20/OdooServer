from datetime import datetime
import logging

import pyodbc

# Global Variable
db_ssms_host = "47.254.234.86"
db_ssms_name = "NTL" 
db_ssms_username = "NTL"
db_ssms_pwd = "ILoveVigtech88!"

conn = pyodbc.connect(
    'Driver={SQL Server Native Client 11.0};'
    f'Server={self.db_ssms_host};'
    f'Database={self.db_ssms_name};'
    f'uid={self.db_ssms_username};'
    f'pwd={self.db_ssms_pwd}'
)


def update_complete_time(sku):
    cursor = conn.cursor()

    inc_sta_id = 12
    c_sta_id = 11

    # Get TNtlSummaryItem 
    cursor.execute(f"SELECT * FROM dbo.TNtlSummaryItem WHERE sku='{sku}' AND status_id={inc_sta_id};")

    obj_list = [_obj for _obj in cursor]

    for _obj in obj_list:

        # Get TNtlSummaryItem Obj
        obj = _obj

        # Update Completed Date
        obj[8] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update Status ID
        obj[9] = c_sta_id

        # Generate List from Values of Order Info
        ls = list(map(str, [*obj]))

        # Join Order Info into single query statement
        stmt = "', '".join(ls)

        # Replace None with Null
        stmt = stmt.replace("'None'", "NULL")

        # Execute Update Query With Value
        cursor.execute(f"EXEC NSP_TNtlSummaryItem_Update '{stmt}';")
        cursor.commit()

        logging.info(f"EXEC NSP_TNtlSummaryItem_Update '{stmt}';")


if __name__ == '__main__':
    update_complete_time("FGSTSB150")
