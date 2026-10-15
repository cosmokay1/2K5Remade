#include "save_read.h"
#include <stdlib.h>
static void require(int ok){if(!ok)abort();}
static void put(unsigned char *p,size_t offset,int32_t value){memcpy(p+offset,&value,4);}
int main(void) {
    unsigned char *p=calloc(1,FRANCHISE_SAVE_BYTES);require(p!=NULL);
    require(!franchise_save_read_shape(p,FRANCHISE_SAVE_BYTES));
    memcpy(p+0x2E0,"ROST",4);memcpy(p+0x30C,"ROST",4);
    put(p,0x2E4,0x91020);put(p,0x320,1);put(p,0x324,0xB288-0x324+1);put(p,0x32C,0xB288+0x54-0x32C+1);
    require(franchise_save_read_shape(p,FRANCHISE_SAVE_BYTES));
    require(!franchise_save_read_shape(NULL,FRANCHISE_SAVE_BYTES));
    require(!franchise_save_read_shape(p,FRANCHISE_SAVE_BYTES-1));
    require(!franchise_save_read_shape(p,SIZE_MAX));
    put(p,0x320,0);require(!franchise_save_read_shape(p,FRANCHISE_SAVE_BYTES));
    put(p,0x320,UINT32_MAX);require(!franchise_save_read_shape(p,FRANCHISE_SAVE_BYTES));
    put(p,0x320,1);put(p,0x324,INT32_MIN);require(!franchise_save_read_shape(p,FRANCHISE_SAVE_BYTES));
    put(p,0x324,0xB288-0x324+1);put(p,0x32C,INT32_MAX);require(!franchise_save_read_shape(p,FRANCHISE_SAVE_BYTES));
    free(p);return 0;
}
