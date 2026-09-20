# Change Report — BILL-482 Block checkout for clients with overdue invoices

## 1. Summary, and asked versus built
- Checkout now refuses to complete an order when the client has an unpaid invoice more than thirty days past its due date, and tells the purchasing coordinator how much is owed.
- A red notice with a link to the payment portal appears on the checkout page in that situation, and the Complete Order button is greyed out.
- Internal test accounts are exempt so the support team can keep placing test orders.
- Block overdue clients at checkout: delivered fully.
- Show the overdue amount and a payment link: delivered fully.
- Exempt internal test accounts: delivered fully.
- Not asked for but added: a database index on invoice due dates, because the new lookup would otherwise scan every invoice for the client.
- Nothing crossed the anti-scope fence; card processing and invoice generation are untouched.

## 2. How it works, end to end
- The purchasing coordinator opens the checkout page. The page asks the checkout totals endpoint for order totals, exactly as it did before.
- The checkout totals endpoint now first asks the invoice repository for the client's overdue balance.
- The invoice repository runs a lookup that finds every invoice for that client, keeps only the unpaid and partly paid ones whose due date is more than thirty days ago, and adds up what is still owed.
- If the total is zero, or the account is an internal test account, the endpoint returns totals as before and the page behaves as it always has.
- If the total is above zero, the endpoint stops and returns a "blocked because overdue" response instead of totals.
- The page sees the blocked response, shows the red notice with the amount and a Pay Now link, and disables the Complete Order button.
- The button stays disabled until the coordinator reloads the page and the endpoint returns a clear response.

## 3. User interface
- Which screen: the checkout page in the storefront.
- How to get there: log in as a client, add any item to the cart, open the cart, then click Proceed to Checkout.
- Before: the payment section showed the order total and an active Complete Order button, always.
- After: when the account is overdue, a red notice card sits directly above the payment section reading "Your account has an overdue balance. Please settle outstanding invoices before placing new orders." with a Pay Now link, and the Complete Order button below it is greyed out and cannot be clicked.
- While the overdue check is loading, the button is disabled and no notice is shown yet; if the check fails, the button stays disabled and a generic error message appears.
- Conditional: the notice only appears when the overdue balance is above zero, and never for internal test accounts.

## 4. Endpoints and service interfaces
- Changed: the checkout totals endpoint (GET, path /checkout/totals). It used to always return order totals; it now returns a blocked status and the overdue amount instead when the client is overdue. The checkout page is its only caller and has been updated to handle the blocked response.
- Added: an overdue balance endpoint (GET, path /checkout/overdue) that returns the client's overdue amount, so the page can show the figure without recalculating totals.

## 5. Business rules and logic
- New validation: before returning totals, the endpoint checks whether the client's overdue balance is above zero and, if so, refuses with a blocked response and the amount.
- New rule: accounts flagged as internal test accounts skip the check entirely.
- The number of days that counts as overdue is read from a setting and defaults to thirty.
- No existing rules were changed and no refactoring was done; behavior is unchanged everywhere outside the new check.

## 6. Data
- New lookup in the invoice repository: links the client to their invoices, keeps only invoices with status unpaid or partly paid, keeps only those due more than the grace period ago, and returns the sum of the remaining balances. It answers the question "how much does this client owe that is more than thirty days late?"
- New index on the invoices table covering client and due date, added so that lookup reads only the client's rows rather than scanning the whole table.
- The migration only creates the index; it moves no data and reverses safely by dropping the index.
- No new facts are stored.

## 7. Configuration and flags
- New setting `CHECKOUT_OVERDUE_GRACE_DAYS` controls how many days late an invoice must be before checkout is blocked. Defaults to thirty; no environment needs to set it unless finance wants a different grace period.
- No feature flags were added, so the new behavior is on as soon as this is deployed.

## 8. Tests, and where to find everything
- A test confirming checkout is blocked when an account has an overdue balance.
- A test confirming an internal test account is not blocked even with an overdue balance.
- Not covered by tests and needing a manual check: the screen states (notice, disabled button, loading, error) and the new endpoint.
- `src/api/checkout.py` — the checkout endpoints; now performs the overdue check and exposes the overdue amount.
- `src/services/checkout_service.py` — new; holds the blocked-or-not rule and the internal-account exemption.
- `src/repositories/invoice_repository.py` — invoice data access; gained the overdue balance lookup.
- `migrations/0042_add_invoice_due_date_index.sql` — new; adds the index on client and due date.
- `src/components/checkout/CheckoutPage.tsx` — the checkout screen; gained the notice card and the disabled-button behavior.
- `tests/test_checkout.py` — new; the two tests above.

## 9. Manual verification recipe, and what was not done
1. Log in with a test client account that has no overdue invoices, add an item to the cart, and proceed to checkout. You should see the normal payment section with an active Complete Order button and no red notice.
2. Log in with a test client account that has an unpaid invoice dated at least thirty-five days ago. Proceed to checkout. You should see the red notice naming the exact overdue amount and a Complete Order button that is greyed out and does nothing when clicked.
3. Click the Pay Now link in the notice. You should land on the payment portal.
4. Log in with an internal test account that has an overdue invoice. Checkout should behave exactly as in step one.
5. Failure case: temporarily point the invoice repository at an empty database and proceed to checkout. The button should stay disabled and a generic error message should appear rather than allowing the order through.
- Not done: the ticket mentioned the overdue reminder emails as related work; nothing about emails was touched. Follow-up worth its own ticket: let finance change the grace period from the admin screen instead of a setting.

## 10. Risk, watch list, and self-check
- Most likely to go wrong: a client with many invoices could see checkout slow down if the new index is not applied before the code goes live. Run the migration first.
- Spot-check after release: normal checkout for clients in good standing, and the internal test account flow used by support.
- Watch on day one: the count of blocked checkout responses in the logs; a sudden spike means the grace period or the status filter is wrong.
- Self-check: this report was written from the diff between the feature branch and main; every hop is traced in section two; no code is pasted; the screen change has a click path; every deviation is listed in section one; no abbreviation is unexplained.
