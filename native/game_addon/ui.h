/* Optional synchronous UI messages for loadable addons. No guest-memory or
 * financial authority. The event payload and host pixels are borrowed only for
 * that invocation; an addon must never retain their pointers. */
#ifndef NFL2K5_ADDON_UI_H
#define NFL2K5_ADDON_UI_H
#include <stddef.h>
#include <stdint.h>
#define NFL2K5_ADDON_UI_INPUT "addon.ui-input.v1"
#define NFL2K5_ADDON_UI_DRAW "addon.ui-draw.v1"
#define NFL2K5_ADDON_UI_CONSUMED 1
/* Consume everything and pass exactly one native B packet to leave the menu. */
#define NFL2K5_ADDON_UI_BACK 2
typedef struct NFL2K5AddonInput {
    uint32_t port;
    uint16_t buttons;
    uint8_t analog[8]; /* A B X Y Black White LT RT */
    int16_t axes[4];
} NFL2K5AddonInput;
typedef struct NFL2K5AddonDraw {
    uint32_t width,height,stride;
    size_t capacity;
    unsigned char *pixels; /* host-owned premultiplied BGRA */
    int redraw; /* host needs a complete copy, even if addon rendering is cached */
    int changed; /* addon sets only after successfully updating pixels */
} NFL2K5AddonDraw;
#ifdef __cplusplus
extern "C" {
#endif
/* Native host hooks; optional and inert with an absent/unsupported addon. */
void nfl2k5_addon_ui_input(NFL2K5AddonInput *input);
int nfl2k5_addon_ui_draw(int width,int height,const void **pixels,int *changed);
#ifdef __cplusplus
}
#endif
#endif
