#pragma once
/* Independent, deterministic coverage policy. Record layout references:
 * cruuz/2k-football-mod-tools: tools/nfl2k5_franchise_schedule.py and
 * mod_editor/core/nfl2k5_franchise_save.py. No schedule or save mutation. */
#include <cstdint>
#include <cstdio>
#include <string>
namespace broadcast_schedule {
inline bool valid(const unsigned char *g) {
    int y=2000+g[5],m=g[3],d=g[4];
    static const int days[]={0,31,28,31,30,31,30,31,31,30,31,30,31};
    return (g[0]==0 || g[0]==3) && g[1]<32 && g[2]<32 && g[1]!=g[2] &&
        m>=1 && m<=12 && d>=1 && d<=days[m]+(m==2 && y%4==0 && (y%100!=0 || y%400==0)) && g[6]<=12 && g[7]<=59;
}
inline int weekday(const unsigned char *g) {
    int y=2000+g[5],m=g[3];
    static const int t[]={0,3,2,5,0,3,5,1,4,6,2,4};
    y-=m<3;
    return (y+y/4-y/100+y/400+t[m-1]+g[4])%7; // Sunday=0
}
inline bool afc(unsigned team) {
    const uint32_t mask=(1u<<2)|(1u<<3)|(1u<<4)|(1u<<5)|(1u<<8)|(1u<<9)|(1u<<10)|(1u<<12)|
        (1u<<16)|(1u<<17)|(1u<<21)|(1u<<22)|(1u<<24)|(1u<<28)|(1u<<29)|(1u<<30);
    return team<32 && (mask&(1u<<team));
}
inline const char *network(const unsigned char *g,bool postseason,bool preseason=false) {
    if(!valid(g))return "";
    int day=weekday(g),hour=g[6];
    if(preseason)return afc(g[1])?"CBS":"FOX";
    bool evening=hour>=7 && hour<=11 && !(hour==9 && g[7]==30);
    if(day==1)return "ESPN";
    if(day==0 && evening)return "NBC";
    if(day==4) {
        if(g[3]==11 && g[4]>=22 && g[4]<=28)
            return evening?"NBC":(hour==0 || hour==12 || hour==1 || hour==2)?"CBS":"FOX";
        return g[3]==9 && g[4]<=10?"NBC":"Prime";
    }
    if(day==6 && !postseason)return "NFL Network";
    if(day==0 && hour==9 && g[7]==30)return "NFL Network";
    return afc(g[2])?"CBS":"FOX";
}
inline unsigned regular_weeks(const unsigned char *grid) {
    // A full schedule has exactly16/17 games per club. Try18weeks first:
    // a modern schedule's first17weeks can also contain256 balanced games.
    for(unsigned weeks:{18u,17u}) {
        unsigned counts[32]={},games=0;
        for(unsigned i=0;i<weeks*17;++i) {
            const unsigned char *g=grid+i*8;
            if(valid(g)){++counts[g[1]];++counts[g[2]];++games;}
        }
        unsigned per=weeks==18?17:16;
        bool balanced=games==per*16;
        for(unsigned count:counts)balanced=balanced && count==per;
        if(balanced)return weeks;
    }
    return 0;
}
inline std::string token(const unsigned char *grid,unsigned season,unsigned weeks) {
    uint64_t h=UINT64_C(14695981039346656037);
    auto add=[&](unsigned c){h=(h^c)*UINT64_C(1099511628211);};
    add(season);add(weeks);
    for(unsigned i=0;i<weeks*17;++i)for(unsigned j=1;j<8;++j)add(grid[i*8+j]);
    char out[17];snprintf(out,sizeof(out),"%016llx",(unsigned long long)h);return out;
}
inline std::string key(const std::string &identity,unsigned cell,const unsigned char *g) {
    char out[64];snprintf(out,sizeof(out),":%u:",cell);
    std::string result=identity+out;
    for(unsigned j=1;j<8;++j){snprintf(out,sizeof(out),"%02x",g[j]);result+=out;}
    return result;
}
}
