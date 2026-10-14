# Sourced efficiency in franchise decisions

Negotiation and draft model contexts now include exact descriptive rates from
complete typed observation windows or their canonical wire representation:
receptions per target, receiving yards per target, completions per pass attempt,
passing yards per pass attempt and rushing yards per rush attempt.

Each rate retains numerator and denominator counters, values, sources, sample
count, window, simulation mode and coverage. Integer ratios remain integers;
nonintegral ratios use canonical fractions. These are production units, not
money, hidden ability, a composite grade or predicted future performance.
Negative observed yardage remains valid. An observed zero numerator with positive
opportunities yields zero; missing/null inputs or zero opportunities yield an
explicit unavailable result. Targets and pressures are never manufactured from
receptions, sacks or ratings. Different windows/modes are not combined.

The original PerformanceEvidence.to_context representation remains unchanged.
from_context verifies the complete canonical source schema; efficiency_context
adds a separate derived view. Legacy descriptive negotiation data is preserved
without inventing ratios. New negotiation evidence saves the derived view and
recomputes it against source counters before commit and during replay. New draft
advice does the same per prospect/window. Older records without the optional view
remain readable. Boolean/int substitutions and changed sample/source/window/rate
claims cannot pass canonical comparison.

Synthetic tests cover exact arithmetic, missing/zero denominators, signed yards,
provider input mutation, legacy compatibility, durable receipts/restart and
corrupted negotiation/draft evidence. No live inference or real game statistics
were used. This supplies consistent arithmetic to personality/performance-driven
reasoning; it does not prove how a live model weights those facts. Verified guest
counter capture and actual play/save evidence remain required.
