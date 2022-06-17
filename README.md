# Salary-detector
An algorithm to detect salaries based on customer's transactional data. Optimised for speed by enabling multicore processing.
This is particularly useful in the financial sector where customers use their checking (salary accounts) for other transactions. Thus making it harder for financial service providers to offer curated offering based on accurate earnings of the customers.
The output contains:
Label		Avg Salary  Pension Inflow	Avg Inflow	Trans Group	inflowCount	inflowPrevMonth	Record_count	possibleGroups
-  Label: A classification as either salaried, non-salaried or pensioner.
-  Duration: The duration under review for the customer
-  Pension Inflow: If the customer is a pension recipient and how much is received.
-  Inflow	Avg: Average inflow if a customer is classified as salaried
-  Trans Group: A customer can belong to multiple transaction groups based on their inflow amountss. 
-  InflowCount: The total credit inflows received in the period under review for that salary range/group
-  InflowPrevMonth: If a salary was received in the most recent month
-  Record_count: The total credit inflows received in the period under review
-  PossibleGroups: How many groups the customer falls in based on the salary range per customer

The majority of the work is in the helper function which has been properly documented to explain the role each function plays in the solution

The getBreakdown_Total allows for review of the inflows and why each account was classified as salaried, nonsalaried or pensioned
