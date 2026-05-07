# CTF Web Challenge Hints


## 3) XSS Discovery

Hint 1:
The comment input is reflected into the page.

Hint 2:
Test whether HTML is being rendered instead of escaped.

Hint 3:
If you can execute JavaScript from the comment, inspect global objects on `window` and look for challenge data.

## 4) IDOR Notes API

## General CTF Workflow Tip

1. Map all user-controlled inputs.
2. Observe reflection or server responses.
3. Change one variable at a time.
4. Use browser devtools (Network, Console, Elements).
5. Keep notes of IDs, endpoints, and payload attempts.
