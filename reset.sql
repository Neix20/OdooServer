-- Run At MSSQL To Reset Everything
DELETE FROM dbo.TNtlJobBatch;
DELETE FROM dbo.TNtlJobOrder;
DELETE FROM dbo.TNtlJobOrderItem;

DELETE FROM dbo.TNtlSummaryItem;

DELETE FROM dbo.TNtlOrder;
DELETE FROM dbo.TNtlOrderItem;

DELETE FROM dbo.TNtlCustomer;
DELETE FROM dbo.TNtlCustomerChat;

DELETE FROM dbo.TNtlSeleniumLog;
