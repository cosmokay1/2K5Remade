# Offer reactions

The existing decision request now returns `reaction: none | offended` alongside
its accept/reject/counter and natural-language explanation. Older recorded
decisions without this field remain neutral. No second model request is needed.

Ordinary bargaining or disappointment is neutral. A rejection or counter may
record offense when the actual offer and remembered treatment justify it. The
model must explain the concern using supplied evidence, rather than inventing
market prices, competing bids or hidden ability. Acceptances cannot be offended.
The model chooses the reaction; the engine controls its effect.

`offer-reaction-v1` reduces saved team-specific respect by 0.05, clamped at zero
and normalized to six decimal places. This is an authored simulation policy,
not an NFL rule. Money, ownership, personality, trust, cap room and financial
revision do not change. Better terms do not automatically restore respect.
The next negotiation receives the changed relationship and recorded reaction.

The dialogue and its explicit `offer_reaction` event commit atomically. Replay
derives the effect from the recorded decision and actor inputs; a missing,
orphaned or altered effect refuses reconstruction. Older engines encounter an
unknown event kind and refuse to load instead of silently dropping the opinion
change. A request retry returns the recorded decision without inference or
another penalty, including after restart. The generic relationship API cannot
apply the same respect consequence again from that source.

Same-player history IDs serialize competing negotiations even though opinion
changes leave financial revision unchanged. Existing prepared guest work blocks
the whole write. Remote access is checked again before a reaction commits.
In-memory examples retain actor changes within their ledger; durable guarantees
require the SQLite store.

Captured negative replies retain their historical decision evidence when
replayed; their fresh signing checkpoint reports the current changed opinion.
Player identity, personality, performance and financial revision remain checked.
Acceptances still require the complete current actor checkpoint, and an older
agreement cannot settle after another negotiation supersedes it. A negative
response or opinion consequence never authorizes a native signing.

This does not yet implement approach limits, verified game-time cooldowns,
withdrawal, extensions, holdouts or participation consequences. It preserves
native free-agency timing. Actual AI dialogue and contract application in the
game remain unverified and disabled.
