# 2k5.cosmokay.com

Requested destination: franchise browser interface/API plus a project/package
section. Current scope implemented: an authenticated HTTP origin for stored
franchise inspection and contract previews. Browser UI, remote negotiation,
draft transactions and downloadable playable packages remain unfinished.

## Cloudflare inspection (October 13, 2026)

The connected Cloudflare plugin can read account
`706dcbc1a70105e02814e5f2a7820456` and active full zone `cosmokay.com`
(`3b3e424f8b93c580b3070b92e5afaee2`). There is no exact DNS record for
`2k5.cosmokay.com`. The unrelated `mediabot` tunnel was left alone.
Creating a dedicated remotely configured `llm-2k5` tunnel returned
`10000: Authentication error`. No tunnel, configuration or DNS record was created.
Reconnect the plugin with Tunnel Write and DNS Write scope before retrying;
do not substitute unrelated credentials or alter other services.

## Origin

Set a private random ASCII `FRANCHISE_WEB_TOKEN` of at least 32 characters in the
origin process environment; never put it in source, browser URLs or a package.
Run from the repository root:

```sh
python3 -m franchise.web --database /path/to/existing/franchise.sqlite --team TEAM_ID --port 8786
```

The origin listens on `127.0.0.1` only. `GET /health` exposes generic readiness.
`GET /` exposes project/capability metadata, not a browser interface. Without a
database/team, financial endpoints return 503. `GET /api/franchise` and
`POST /api/preview` require `Authorization: Bearer TOKEN`. A preview body has
exact fields `offer` and `revision`, using the same Offer JSON as the pipe bridge.
It does not sign, reserve funds, call a model or toggle the Google AI switch.
Existing state must already be initialized and source-reconciled. Responses are
uncached; error responses omit state, credentials and exception detail.

Before publishing a live franchise browser interface, configure Cloudflare
Access for the intended user and validate unauthorized denial. The current
bearer endpoint is a prepared client API, not browser login. Remote negotiation
must retain the existing fresh Google control handshake and restricted runtime
identity; exposing HTTP must not bypass pending IAM delegation or enable paid
inference for anonymous callers.

## Pending tunnel configuration

After write access is restored, create/reuse the dedicated tunnel and publish
only this host to `http://127.0.0.1:8786`, with a final `http_status:404` ingress
rule. Create a proxied CNAME `2k5.cosmokay.com` to the verified tunnel UUID's
`cfargotunnel.com` hostname. Run its connector on the same host as this service,
using a securely stored tunnel token; never commit/print that token. Validate
connector health, HTTPS `/health`, authorized API success and unauthorized 401.
A local connector requires the host to remain awake; it is not cloud compute.

Rollback removes only this hostname route/DNS record, then stops the dedicated
connector/origin. No rollback is needed yet because the mutation failed.

Sources: [Cloudflare published applications](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/),
[API setup](https://developers.cloudflare.com/tunnel/get-started/).
