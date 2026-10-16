/* Transport-only fixtures have no game application adapter. They can never
 * publish a cap plan or turn a transport receipt into a native write grant. */
#include "cap_enforcement.h"
int nfl2k5_franchise_publish_cap(const FranchiseCapEnforcement *plan) {
    (void)plan;return 0;
}
