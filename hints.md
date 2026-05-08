# CTF Web Challenge Hints

## 1) Hidden Admin Panel

Hint 1:
Check the public files and look for discovery clues like robots.txt.

Hint 2:
Hidden paths are often named plainly. Try likely admin-style routes.

Hint 3:
If a page seems missing, verify whether it is blocked from the public entry point or just not linked.

## 2) SQL Injection Login

Hint 1:
Focus on how the login form checks the username and password.

Hint 2:
Try input that changes the meaning of the authentication condition instead of matching real credentials.

Hint 3:
Look for classic always-true patterns and comments that terminate the rest of the query.


## 3) XSS Discovery

Hint 1:
The comment input is reflected into the page.

Hint 2:
Test whether HTML is being rendered instead of escaped.

Hint 3:
If you can execute JavaScript from the comment, inspect global objects on `window` and look for challenge data.

## 4) IDOR Notes API

Hint 1:
Watch the network requests when loading a note. The note ID is part of the URL.

Hint 2:
If one ID works, nearby IDs may belong to other users.

Hint 3:
The bug is about object-level authorization, so changing the ID is the key test.

## 5) Compartmentalized Vault

Hint 1:
The UI only shows public compartments, but the API accepts a compartment value from the request.

Hint 2:
The backend checks the compartment string before it canonicalizes the path.

Hint 3:
Try a path traversal style compartment value that still starts with a public prefix before normalization.

## General CTF Workflow Tip

1. Map all user-controlled inputs.
2. Observe reflection or server responses.
3. Change one variable at a time.
4. Use browser devtools (Network, Console, Elements).
5. Keep notes of IDs, endpoints, and payload attempts.
