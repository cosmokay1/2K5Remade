# 2k5.cosmokay.com

Requested destination: franchise browser interface/API plus a project/package
section. Current scope implemented: an authenticated HTTP origin for stored
franchise inspection and contract previews. Browser UI, verified live-model negotiation,
draft transactions and downloadable playable packages remain unfinished.

## Live Cloudflare route (October 13, 2026)

The reconnected plugin successfully created remotely configured tunnel `llm-2k5`
(`dc5e0635-6a19-487f-b245-f4b910f6a20f`) in account
`706dcbc1a70105e02814e5f2a7820456`. Zone `cosmokay.com` is active/full
(`3b3e424f8b93c580b3070b92e5afaee2`). Proxied CNAME record
`63f9f9e10cd2d3f6b7dd498337f7b14d` routes `2k5.cosmokay.com` to that tunnel.
The unrelated mediabot tunnel was left alone.

Ingress routes only this hostname to `https://127.0.0.1:8786`, with originServerName
`localhost`, explicit trusted certificate file in `.local-runtime/origin.crt`
and `noTLSVerify: false`; final ingress returns 404. The dedicated local origin
certificate includes localhost/127.0.0.1 SANs and expires in one year. Renewal
and persistent host startup remain required before unattended production use.
Tunnel/API tokens and origin key stay in ignored `.local-runtime`, private modes.

Scoped redirect ruleset `26190b7ff5c84a50995d343915c2d922`, rule
`e273f0e69c0b4acb81a7129e2ae6b4a6`, sends only HTTP requests for this host to
HTTPS with 308, retaining path/query. No zone-wide HTTPS settings were changed.

Verified trusted local TLS `/health` 200, public HTTPS `/health` 200 and HTTP
308 redirect preserving query using curl. Cloudflare reports tunnel healthy with
four active connections. Python urllib's default agent received an existing edge
403/1010; curl reached the origin. No firewall settings were weakened.

## Origin

Set a private random ASCII `FRANCHISE_WEB_TOKEN` of at least 32 characters in the
origin process environment; never put it in source, browser URLs or a package.
Run from the repository root:

```sh
python3 -m franchise.web --database /path/to/existing/franchise.sqlite --team TEAM_ID --port 8786 --tls-cert .local-runtime/origin.crt --tls-key .local-runtime/origin.key
```

The origin listens on `127.0.0.1` only. `GET /health` exposes generic readiness.
`GET /` exposes project/capability metadata, not a browser interface. Without a
database/team, financial endpoints return 503. `GET /api/franchise` and
`POST /api/preview` require `Authorization: Bearer TOKEN`. A preview body has
exact fields `offer` and `revision`, using the same Offer JSON as the pipe bridge.
A preview does not sign, reserve funds, call a model or toggle the Google AI switch.
Existing state must already be initialized and source-reconciled. Responses are
uncached; error responses omit state, credentials and exception detail.

Before publishing a live franchise browser interface, configure Cloudflare
Access for the intended user and validate unauthorized denial. The current
bearer endpoint is a prepared client API, not browser login. Remote negotiation
must retain the existing fresh Google control handshake and restricted runtime
identity; exposing HTTP must not bypass pending IAM delegation or enable paid
inference for anonymous callers.

## Running connector and rollback

The origin and dedicated cloudflared connector currently run on this Mac in local
process sessions; they are not boot-installed services. The Mac must remain
awake/online. Restart the origin with the command above and a securely loaded
web token, then run `cloudflared tunnel run --token-file .local-runtime/tunnel.token`.
Never print or commit credentials. A cloudflared warning about missing ingress
at initial startup preceded its remote configuration; actual route succeeded.

Rollback: remove only the specified DNS record, redirect rule and dedicated
hostname route, then stop this project's connector/origin. Preserve unrelated
zone resources. Full browser UI and authenticated state connection remain next.

Sources: [Cloudflare published applications](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/),
[run parameters](https://developers.cloudflare.com/tunnel/reference/run-parameters/),
[Single Redirect API](https://developers.cloudflare.com/rules/url-forwarding/single-redirects/create-api/).

## Negotiation transport

`POST /api/negotiate` uses the existing protocol-1 `negotiate` request envelope,
including request ID, configured team ID, offer, expected revision, timeout and
actor evidence. Other teams and operations are rejected. One negotiation executes
at a time without a request queue; another receives 429 busy. Durable history,
exclusive ownership, final cap validation, idempotent recall and fresh remote
shutdown checks use the same Bridge/Negotiation/store path as the native pipe.
Successful model acceptance can sign a contract; the preview endpoint cannot.

The origin defaults to `--ai disabled`. `--ai vertex-runtime` explicitly configures
only the restricted keyless runtime identity, with separate Google control/provider
credentials and no administrator fallback. Authentication/dependency failures keep
AI unavailable while inspection/preview remain usable. Pending runtime delegation
approval is unchanged; no IAM grant or live model call was made for HTTP work.
Current public origin has neither a database nor an enabled model. Remote transport
supports saved prototype contracts; this is not a verified retail-game integration.
HTTP retries can recall a committed agreement by stable request ID after a lost
response. Client disconnects through an HTTP proxy cannot prove transaction rollback;
retry the same ID rather than generating a new agreement. Server deadlines and
remote shutdown are enforced at the transaction boundary.

Saved player context is available through authenticated
`GET /api/player?player_id=STABLE_ID` when a database/team is configured. It returns
personality, relationships, signed promise goals, promise history, initialization
status and financial revision from one validated read snapshot. Unknown players
return 404; duplicate/extra/blank query parameters return 400. It performs no AI
request, personality generation or financial mutation and remains usable with AI
disabled. The equivalent native protocol operation is `player_context`, with
`team_id`, `player_id`, `request_id`, `protocol: 1` and `timeout_ms`. Native response
validation rejects mismatched identities and malformed context containers. This
is an API boundary, not a implemented browser dashboard or game menu.

Authenticated `GET /api/players` lists the configured team's registered contract
identities, contract classifications and personality initialization flags with a
single financial revision. It exposes no hidden ratings, inferred names or positions.
These identities include declared free agents/prospects and are explicitly not proof
of current guest roster membership. Reads create no actors and require no AI grant.
