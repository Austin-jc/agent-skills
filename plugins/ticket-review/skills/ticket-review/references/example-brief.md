# Ticket Brief — BILL-482 Block checkout for clients with overdue invoices

## 1. At a glance
- Type: change to an existing feature (checkout).
- Request: stop clients from completing checkout while they have an invoice more than thirty days overdue, and show them how much they owe.
- Business reason: clients with unpaid invoices keep placing new orders, which grows the money the company is owed and may never collect.
- Rough size: a few days.

## 2. Words you need to know
- Client: a company that has a signed contract with us and can place orders through the storefront.
- Client account: the billing relationship for a client. In this codebase one client has exactly one account; the ticket uses the two words interchangeably.
- Invoice: a bill sent to a client for an order. It has a due date and a status of paid, partly paid, or unpaid.
- Overdue invoice: an invoice that is unpaid or partly paid and whose due date is in the past. The ticket sets the threshold at thirty days past due.
- Purchasing coordinator: the person at the client company who places orders. Not an employee of ours.
- Storefront: the customer-facing web application where orders are placed.
- Payment portal: the separate page where a client can pay outstanding invoices by card or bank transfer.
- Internal test account: a client account owned by our own support team, used for placing test orders.

## 3. Why this exists
- The business process: clients place orders through the storefront checkout many times a day; finance sends invoices afterward and the collections team chases unpaid ones at month end.
- The friction: nothing stops a client who has not paid old invoices from placing new orders, so the amount owed keeps growing while collections is still chasing the old amount.
- Who runs into it: the finance and collections team, who discover the new orders at month-end reconciliation.
- Cost: the ticket states that exposure to unpaid debt grew by about forty thousand dollars last quarter. Currency is not stated in the ticket.
- Cost of inaction: the owed amount keeps compounding with every new order from a delinquent client, and collections has more to chase each month.
- Who asked: the finance and collections team. They expect delinquent clients to be stopped at checkout and pointed to the payment portal.
- Bigger picture: this is related to BILL-470, which adds reminder emails for overdue invoices. That ticket nudges clients; this one enforces. This ticket does not depend on it.

## 4. Before and after
- Before: a purchasing coordinator at a client with a two-month-old unpaid invoice adds items to the cart, opens checkout, and clicks Complete Order. The order goes through. At month end, the collections team finds both the old invoice and the new order unpaid, and has to chase both.
- After: the same coordinator opens checkout and sees a red notice naming the overdue amount with a link to the payment portal. The Complete Order button is greyed out. The coordinator pays the old invoice through the portal, comes back, and can then complete the order.

## 5. Scope and anti-scope
- Asked: when a client reaches the checkout payment page, check for invoices more than thirty days overdue; if any exist, disable the Complete Order button and show a notice with the total overdue amount and a link to the payment portal.
- Included: the check itself, the notice, the disabled button, and an exemption for internal test accounts.
- Must not change: the card processing logic, and how invoices are generated. Both are named in the ticket.
- Must also leave alone, from reading the code: the cart page and the order confirmation page, which share nothing with this check, and the existing invoice listing query, which other screens depend on.

## 6. Triggers, inputs, outputs, and failure
- Trigger: the client opens the checkout payment page.
- Inputs: which client is logged in, and that client's invoices with their status, due date, and remaining balance.
- Outputs, when clear: the normal checkout page with an active Complete Order button.
- Outputs, when overdue: a notice showing the total overdue amount, a link to the payment portal, and a disabled Complete Order button.
- Failure: if the overdue check itself fails, the safe behavior is to keep the button disabled and show an error, rather than let the order through. The ticket does not say this; it is an assumption.

## 7. The work involved
- Add a lookup in the invoice repository that finds all unpaid or partly paid invoices for the client, keeps those due more than thirty days ago, and totals the remaining balance. Needed because nothing currently calculates an overdue balance. Lives in `src/repositories/invoice_repository.py`.
- Add a rule in the checkout service that says the client is blocked when that total is above zero, and exempts internal test accounts. Needed so the decision is made on the server and cannot be bypassed from the browser. Lives in `src/services/checkout_service.py`.
- Change the checkout totals endpoint to run that rule before returning totals, and return a blocked response with the amount instead when blocked. Needed because this endpoint is what the page already calls on load. Lives in `src/api/checkout.py`.
- On the checkout page, show the notice card and disable the button when the response says blocked. Needed so the coordinator sees why they cannot proceed. Lives in `src/components/checkout/CheckoutPage.tsx`.
- Uncertain: whether the thirty-day threshold should be a setting or fixed. Proposed as a setting with a default of thirty so finance can adjust it without a code change.

## 8. What done looks like
- A client with no overdue invoices reaches checkout and sees an active Complete Order button and no notice.
- A client with an invoice thirty-five days past due reaches checkout and sees the notice with the exact overdue amount and a button that cannot be clicked.
- An internal test account with an overdue invoice checks out normally.
- If the overdue check fails, the order cannot be completed and the coordinator sees an error.

## 9. Assumptions, open questions, and what could break
- Assumption: "thirty days overdue" means thirty days after the invoice due date, not thirty days after the invoice was issued. Please confirm with finance.
- Assumption: partly paid invoices count as overdue for their remaining balance. Please confirm.
- Assumption: on a failed check, blocking is safer than allowing. Please confirm.
- Open question: should the notice show each overdue invoice or only the total? The ticket says total. Finance could answer.
- Could break: any other screen that uses the checkout totals endpoint would now receive a blocked response it does not expect. From the code, only the checkout page calls it, but this should be checked at review.

## 10. Self-check
- Someone with no knowledge of this business could explain in two sentences why this ticket exists.
- The walkthrough uses a real role and a concrete example.
- Every task states why it is needed and where it lives.
- Every business term is defined in section two. No abbreviation appears unexplained.
- Nothing assumed is presented as fact.
