# Public UI design contract

The existing project uses Playwright Test with TypeScript and a configured local
`baseURL`. The approved fixture `/checkout.html` has a Pay button and live status.
While a POST `/api/pay` request is pending, show Processing and disable Pay. For a
2xx response show Order confirmed. For a non-2xx or rejected request show Payment
failed. Try again. Re-enable Pay after either outcome. A later retry may succeed.
No real payment, production data or credential is allowed in the test environment.

Case requests may ask for frontend-only integration design using an intercepted
`/api/pay` route or a true E2E design that needs a local provider and queryable
order store. The HTML implements only the former boundary; a mocked response does
not prove persistence. Do not invent a backend query endpoint or claim a live E2E
test is runnable without it. Design only: do not run a browser or start a service.
Playwright dependencies and a runnable web-server configuration are not included
in this authored source fixture; this phase can verify markup/JavaScript syntax,
not browser behavior or dependency compatibility.
