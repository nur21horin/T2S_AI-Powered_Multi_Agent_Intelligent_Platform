# Authentication API contract

All routes use `/api/v1/auth`. Success responses return the resource directly;
errors use the shared `{"error": {"code", "message", "details", "request_id}}`
shape. Browser requests that establish or use authentication cookies must use
`credentials: "include"`. Configure the frontend origin in
`CORS_ALLOWED_ORIGINS`.

## Endpoints

| Method and path | Request | Result |
|---|---|---|
| `POST /register` | `email`, `full_name`, `password` | `201` safe user object; always creates a `STUDENT` and sends verification email |
| `POST /login` | `email`, `password` | Access JWT, CSRF token, safe user object; sets refresh and CSRF cookies |
| `POST /refresh` | CSRF header and cookies | Rotated access JWT, CSRF token, safe user object; rotates cookies |
| `POST /logout` | CSRF header and cookies | Revokes refresh-token family and clears cookies |
| `GET /csrf` | Cookies | Returns current CSRF token for a page reload; requires allowed `Origin` |
| `GET /me` | Bearer access JWT | Safe current-user object |
| `POST /email/verify` | `token` | Verifies the email; token is single-use and expires |
| `POST /email/verification/request` | `email` | Generic response; sends another verification email where applicable |
| `POST /password/forgot` | `email` | Generic response to reduce account enumeration |
| `POST /password/reset` | `token`, `new_password` | Consumes a reset token and revokes refresh sessions |
| `POST /password/change` | Bearer token, `current_password`, `new_password` | Changes password and revokes refresh sessions |

Passwords must be 12–128 characters. Email addresses are validated and
normalized. Registration ignores any client-supplied role and assigns
`STUDENT` on the server.

## Browser token flow

1. Call `POST /login` with JSON credentials and browser credentials enabled.
   The response contains `access_token` and `csrf_token`. The refresh token is
   set only as an HttpOnly cookie; the CSRF token is also set in a signed,
   JavaScript-readable cookie.
2. Keep the access JWT in application memory and send it as
   `Authorization: Bearer <access_token>` for authenticated requests. Do not
   put either token in `localStorage`.
3. Call `POST /refresh` with `credentials: "include"`, the current CSRF token in
   `X-CSRF-Token`, and the browser-supplied `Origin`. Store the returned access
   and CSRF tokens in memory; the refresh cookie rotates automatically.
4. After a page reload, call `GET /csrf` with credentials enabled and the
   browser-supplied `Origin`, then use the returned CSRF token for refresh or
   logout.
5. Call `POST /logout` with credentials and the CSRF header to revoke the
   refresh family and clear the cookies.

The refresh cookie defaults to `HttpOnly`, path `/api/v1/auth`, and
`SameSite=Lax`. `Secure` is forced in production and for `SameSite=None`.
`COOKIE_DOMAIN`, `COOKIE_PATH`, `COOKIE_SAMESITE`, and cookie names are
configurable. Refresh/logout and login require an exact allowed origin; CSRF
validation pairs the signed cookie with `X-CSRF-Token`.

## Email delivery configuration

Email links target the frontend routes `/auth/verify-email?token=...` and
`/auth/reset-password?token=...`. Configure `FRONTEND_BASE_URL`, `SMTP_HOST`,
`SMTP_PORT`, `EMAIL_FROM`, and secure SMTP (`SMTP_STARTTLS=true` or
`SMTP_USE_SSL=true`). Add SMTP credentials when required by the provider.
Email-dependent endpoints return a safe `503` if mail is unavailable; password
recovery does not disclose whether an account exists.
