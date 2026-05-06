# CTF Web Challenge Hints

Use these hints in order. Try the next hint only if you are stuck.


## 2) SQL Injection Login

Hint 1:
The login check is vulnerable to input that changes query logic.

Hint 2:
Try using a quote (`'`) in the password field and observe behavior.

Hint 3:
Use a classic authentication bypass payload that makes a condition always true.

## 3) XSS Discovery

Hint 1:
The comment input is reflected into the page.

Hint 2:
Test whether HTML is being rendered instead of escaped.

Hint 3:
If you can execute JavaScript from the comment, inspect global objects on `window` and look for challenge data.

## 4) IDOR Notes API

Hint 1:
You can request notes by numeric ID.

Hint 2:
Watch the browser network request and identify the API route pattern.

Hint 3:
Change only the object ID and test whether authorization is enforced for other users' notes.

## General CTF Workflow Tip

1. Map all user-controlled inputs.
2. Observe reflection or server responses.
3. Change one variable at a time.
4. Use browser devtools (Network, Console, Elements).
5. Keep notes of IDs, endpoints, and payload attempts.
