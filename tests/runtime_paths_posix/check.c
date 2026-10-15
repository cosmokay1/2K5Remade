/* Exercise the actual runtime translator against authored files only. */
#include "kernel/kernel.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

extern void xbox_path_map_disc_dir(const char *name,const char *host_dir);
/* This fixture exercises direct paths, not the kernel's symbolic-link table. */
const char *xbox_LookupSymbolicLink(const char *link) {(void)link;return NULL;}
void xbox_log(int level,const char *subsystem,const char *fmt,...) {
    (void)level;(void)subsystem;(void)fmt;
}
static void put(const char *path,const char *data) {
    FILE *f=fopen(path,"wb");assert(f);
    assert(fwrite(data,1,strlen(data),f)==strlen(data));assert(fclose(f)==0);
}
static void contents(const char *path,const char *data) {
    char buf[100]={0};FILE *f=fopen(path,"rb");assert(f);
    assert(fread(buf,1,sizeof(buf)-1,f)==strlen(data));assert(!strcmp(buf,data));assert(fclose(f)==0);
}
static void translated(const char *input,const char *expected) {
    char out[MAX_PATH];assert(xbox_translate_path(input,out,sizeof(out)));
    if(strcmp(out,expected)) fprintf(stderr,"%s -> %s; expected %s\n",input,out,expected);
    assert(!strcmp(out,expected));
}
int main(void) {
    char root[]="/tmp/2k5-paths-XXXXXX",out[MAX_PATH];
    assert(mkdtemp(root));assert(chdir(root)==0);
    assert(mkdir("game",0700)==0);assert(mkdir("teams",0700)==0);
    assert(mkdir("game/Mixed",0700)==0);put("game/Mixed/Roster.DAT","roster");
    put("teams/Uniform.DAT","uniform");
    xbox_path_init("game","saves");
    translated("D:\\mixed\\roster.dat","game/Mixed/Roster.DAT");
    translated("\\Device\\CdRom0\\MIXED\\ROSTER.dat","game/Mixed/Roster.DAT");
    translated("D:\\mixed\\NewFile.DAT","game/Mixed/NewFile.DAT");
    xbox_path_map_disc_dir("CUSTOM","teams");
    translated("D:\\custom\\uniform.dat","teams/Uniform.DAT");
    translated("\\??\\D:\\CUSTOM\\uniform.dat","teams/Uniform.DAT");
    translated("\\Device\\CdRom0\\custom\\uniform.dat","teams/Uniform.DAT");
    translated("U:\\NewSave","saves/UserData/NewSave");
    translated("\\Device\\Harddisk0\\Partition0","saves/Partition0.img");
    translated("\\Device\\Harddisk0\\Partition3\\","saves/Partition3.img");
    FILE *f=fopen("saves/Partition0.img","rb");char magic[16];assert(f);
    assert(fseek(f,0x800,SEEK_SET)==0);assert(fread(magic,1,16,f)==16);
    assert(!memcmp(magic,"****PARTINFO****",16));assert(fclose(f)==0);
    f=fopen("saves/Partition3.img","r+b");assert(f);assert(fseek(f,8192,SEEK_SET)==0);
    assert(fwrite("KEEP",1,4,f)==4);assert(fclose(f)==0);
    xbox_path_init("game","saves");
    f=fopen("saves/Partition3.img","rb");assert(f);assert(fseek(f,8192,SEEK_SET)==0);
    assert(fread(magic,1,4,f)==4);assert(!memcmp(magic,"KEEP",4));assert(fclose(f)==0);
    struct stat st;assert(stat("saves/Partition3.img",&st)==0);
    assert(st.st_size==0x00177000LL*512);
    put("settings.json","old settings");xbox_set_user_dir("profile");
    assert(!strcmp(xbox_user_dir(),"profile"));
    xbox_user_path("settings.json",out,sizeof(out));contents(out,"old settings");
    put("settings.json","changed old settings");xbox_user_path("settings.json",out,sizeof(out));
    contents(out,"old settings");
    xbox_user_path("cache\\new.dat",out,sizeof(out));assert(!strcmp(out,"profile/cache/new.dat"));
    assert(stat("profile/cache",&st)==0 && S_ISDIR(st.st_mode));
    xbox_set_user_dir(NULL);xbox_user_path("cache\\new.dat",out,sizeof(out));
    assert(!strcmp(out,"cache/new.dat"));
    assert(unlink("profile/settings.json")==0);assert(rmdir("profile/cache")==0);assert(rmdir("profile")==0);
    assert(unlink("settings.json")==0);
    for(int i=0;i<=5;++i) {snprintf(out,sizeof(out),"saves/Partition%d.img",i);assert(unlink(out)==0);}
    const char *dirs[]={"TitleData","UserData","Cache","SystemData"};
    for(int i=0;i<4;++i) {snprintf(out,sizeof(out),"saves/%s",dirs[i]);assert(rmdir(out)==0);}
    assert(rmdir("saves")==0);assert(unlink("game/Mixed/Roster.DAT")==0);
    assert(rmdir("game/Mixed")==0);assert(rmdir("game")==0);
    assert(unlink("teams/Uniform.DAT")==0);assert(rmdir("teams")==0);
    assert(chdir("/")==0);assert(rmdir(root)==0);
    puts("PASS: case resolution, added teams, save paths, partition persistence and settings migration");
    return 0;
}
