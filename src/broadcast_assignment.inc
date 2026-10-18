/* Included after the presentation menu API: schedule-aware package selection.
 * Guest bytes are copied and validated; never alter schedules or franchise data.
 * Outside the supported franchise calendar the user's manual choice is retained. */
static int broadcast_team(const std::string &code)
{
    static const char *codes[]={"SF","CHI","CIN","BUF","DEN","CLE","TB","ARI","SD","KC","IND","DAL",
        "MIA","PHI","ATL","NYG","JAC","NYJ","DET","GB","CAR","NE","OAK","STL","BAL","WAS","NO","SEA","PIT","HOU","TEN","MIN"};
    std::string key=upper(code);
    if(key=="LAC")key="SD";if(key=="LAR" || key=="LA")key="STL";
    if(key=="LV")key="OAK";if(key=="JAX")key="JAC";if(key=="WSH")key="WAS";
    for(int i=0;i<32;++i)if(key==codes[i])return i;
    return -1;
}
static void franchise_broadcast_tick(const GameState &game)
{
    static DWORD last=0;
    DWORD now=GetTickCount();if(now-last<250)return;last=now;
    static std::string last_key;
    static int assigned=-1;
    static int manual_intro=0,manual_outro=0;
    auto restore=[&] {
        int manual=s_network_manual.exchange(-1);
        if(manual>=0 && s_sel_pkg.load()==assigned) {
            pregame_replacement_reset();s_sel_pkg=manual;
            s_sel_intro=manual_intro;s_sel_outro=manual_outro;
        }
        last_key.clear();assigned=-1;
    };
    // C4F10 selects row*17+slot from E57C40. The captured phase descriptors
    // use B0 for phase horizon and B4 for current week; postseason restarts at0.
    uint32_t mode=rd32(0xE576A0u),phase=rd32(0xE576A4u),horizon=rd32(0xE576B0u),week=rd32(0xE576B4u),season=rd32(0xE576B8u);
    if(!game.valid || mode!=2 || rd32(0xE576ACu)!=32 || season>255 ||
       !((phase==7 && horizon==4 && week<=4) || (phase==8 && (horizon==17 || horizon==18) && week<horizon) || (phase==9 && horizon==4 && week<4))) {
        restore();return;
    }
    unsigned char grid[22*17*8]={};
    if(!gread(0xE57C40u,grid,sizeof grid)) {restore();return;}
    unsigned regular_weeks=phase==7?5:broadcast_schedule::regular_weeks(grid);
    if(!regular_weeks || (phase==8 && regular_weeks!=horizon)){restore();return;}
    unsigned row=phase==8?week:regular_weeks+week;
    if(row>=22){restore();return;}
    int home=broadcast_team(game.t[HOME].abbr),away=broadcast_team(game.t[AWAY].abbr),slot=-1;
    for(unsigned i=0;i<17;++i) {
        const unsigned char *record=grid+(row*17+i)*8;
        if(broadcast_schedule::valid(record) && record[1]==home && record[2]==away) {
            if(slot>=0){restore();return;}slot=(int)i;
        }
    }
    if(slot<0){restore();return;}
    unsigned cell=row*17+(unsigned)slot;
    const unsigned char *record=grid+cell*8;
    std::string identity=broadcast_schedule::token(grid,season,regular_weeks);
    std::string key=broadcast_schedule::key(identity,cell,record);
    if(last_key==key)return; // Stable through the match, including F2 overrides.
    restore();
    JVal settings;load_json("mods/broadcast-networks.json",settings);
    if(!settings.flag("enabled",true)){last_key=key;return;}
    std::string network=broadcast_schedule::network(record,phase==9,phase==7);
    if(const JVal *overrides=settings.get("overrides")) {
        const std::string chosen=overrides->str(key.c_str());
        if(chosen=="CBS" || chosen=="FOX" || chosen=="NBC" || chosen=="ESPN" || chosen=="Prime" || chosen=="NFL Network")network=chosen;
    }
    std::string folder;
    if(const JVal *packages=settings.get("packages"))folder=packages->str(network.c_str());
    if(folder.empty()) {
        if(network=="CBS")folder="NFL on CBS";
        if(network=="FOX")folder="NFL on FOX";
        if(network=="NBC")folder="NBC_SNF";
        if(network=="ESPN")folder="ESPN_MNF";
        if(network=="Prime")folder="Prime_TNF";
    }
    int selected=0;
    for(size_t i=1;!folder.empty() && i<s_pkgs.size();++i)
        if(s_pkgs[i].dir=="mods/presentations/"+folder){selected=(int)i;break;}
    if(network!="ESPN" && !selected)
        fprintf(stderr,"[BROADCAST] %s graphics unavailable; using original ESPN presentation\n",network.c_str());
    manual_intro=s_sel_intro;manual_outro=s_sel_outro;
    s_network_manual=s_sel_pkg.load();assigned=selected;last_key=key;
    pregame_replacement_reset();s_sel_pkg=selected;
    s_sel_intro=std::min(1,nfl2k5_pres_values(1)-1);s_sel_outro=std::min(1,nfl2k5_pres_values(2)-1);
    fprintf(stderr,"[BROADCAST] game=%s network=%s package=%s\n",key.c_str(),network.c_str(),s_pkgs[selected].name.c_str());
}
