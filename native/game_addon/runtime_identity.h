/* Optional host metadata carried through ABI2 named events/snapshots.
 * Identifies the XBE load input after built-in file patches. It is not proof
 * of later guest memory, native build compatibility, franchise or authority. */
#ifndef NFL2K5_ADDON_RUNTIME_IDENTITY_H
#define NFL2K5_ADDON_RUNTIME_IDENTITY_H
#include <string.h>
#define NFL2K5_ADDON_LOADED_IMAGE "engine.loaded-image.v1"
typedef struct NFL2K5AddonImageIdentity { char sha256[65]; } NFL2K5AddonImageIdentity;
static inline int addon_image_identity(NFL2K5AddonImageIdentity *out,const char *sha256) {
    NFL2K5AddonImageIdentity next={{0}};
    if(!out) return 0;
    if(sha256) {
        for(unsigned i=0;i<64;++i) {
            const char c=sha256[i];
            if(!((c>='0' && c<='9') || (c>='a' && c<='f'))) {memset(out,0,sizeof(*out));return 0;}
            next.sha256[i]=c;
        }
        if(sha256[64]) {memset(out,0,sizeof(*out));return 0;}
        *out=next;return 1;
    }
    memset(out,0,sizeof(*out));return 0;
}
#endif
