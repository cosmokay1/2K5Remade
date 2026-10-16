#ifndef NFL2K5_CONTRACT_DRAFT_H
#define NFL2K5_CONTRACT_DRAFT_H
#include "negotiation_screen.h"
namespace franchise {
/* Local proposal only. Exact annual amounts always come back from the service;
 * editing never changes guest terms or sends a negotiation to a player. */
struct ContractDraft {
    bool active=false,present=false,armed=false,waiting=false;
    unsigned field=0,scale=1;
    uint32_t amount=0,flags=0;
    uint32_t checked_amount=0,checked_flags=0;
    int held_direction=0;
    uint64_t next_repeat=0;
    unsigned long long epoch=0;
    uint16_t previous_buttons=0;
    std::array<uint8_t,8> previous_analog{};
    std::array<int,2> sticks{};
    std::string message;
    void reset(){*this={};}
    bool begin(const nlohmann::json& context,unsigned long long generation) {
        reset();
        if(!generation || !context.contains("amount_word") || !context.contains("flags_word") ||
           !context.at("amount_word").is_number_unsigned() || !context.at("flags_word").is_number_unsigned()) return false;
        const auto a=context.at("amount_word").get<uint64_t>(),f=context.at("flags_word").get<uint64_t>();
        if(!a || a>65535 || f>UINT32_MAX) return false;
        const auto format=context.value("contract_format",std::string("original_fxg_v1"));
        if(format!="original_fxg_v1" && format!="softdrink_fxg_v1") return false;
        scale=format=="softdrink_fxg_v1"?4:1;
        amount=checked_amount=static_cast<uint32_t>(a);flags=checked_flags=static_cast<uint32_t>(f);epoch=generation;active=present=true;
        return true;
    }
    bool dirty()const{return present && (amount!=checked_amount || flags!=checked_flags);}
    void rearm(){armed=false;previous_buttons=0;previous_analog.fill(0);sticks.fill(0);held_direction=0;next_repeat=0;}
    void review(){active=false;rearm();}
    void resume(){active=true;rearm();}
    unsigned years()const{return (flags>>16)&15u;}
    unsigned bonus()const{return flags&15u;}
    unsigned shape()const{return flags>>29;}
    std::string schedule()const{return shape()==1?"Descending":shape()==2?"Balanced":"Current schedule";}
    ScreenTable table()const {
        const std::array<std::string,4> labels{"Total (approx.)","Years","Signing bonus","Salary schedule"};
        const std::array<std::string,4> values{screen_money(static_cast<int64_t>(amount)*10000*scale),
            std::to_string(years()),screen_money(static_cast<int64_t>(amount)*bonus()*1000*scale)+" ("+std::to_string(bonus()*10)+"%)",schedule()};
        ScreenTable result{active?"Edit your offer":"Your draft",{"TERM","VALUE"},{}};
        for(unsigned i=0;i<4;++i) result.rows.push_back({labels[i],{values[i]}});
        return result;
    }
    // 0 consumes input, 1 cancels, 2 requests an explicit accounting check.
    int input(const NFL2K5AddonInput& event,uint64_t now=0) {
        bool neutral=!event.buttons;
        for(auto value:event.analog) if(value>30) neutral=false;
        for(auto value:event.axes) if(value>8000 || value<-8000) neutral=false;
        if(!armed){armed=neutral;return 0;}
        const auto pressed=event.buttons&~previous_buttons;
        auto down=[&](size_t i){return event.analog[i]>30 && previous_analog[i]<=30;};
        auto stick=[&](size_t i,int16_t value){
            const int before=sticks[i];
            if(value>16000) sticks[i]=1;else if(value<-16000) sticks[i]=-1;
            else if(value>=-8000 && value<=8000) sticks[i]=0;
            return before!=sticks[i]?sticks[i]:0;
        };
        stick(0,event.axes[0]);const int y=stick(1,event.axes[1]);
        const bool cancel=down(1),check=down(2);
        if(!waiting) {
            if((pressed&1) || y>0) field=(field+3)%4;
            if((pressed&2) || y<0) field=(field+1)%4;
            const bool right=(event.buttons&8) || sticks[0]>0,left=(event.buttons&4) || sticks[0]<0;
            const int direction=right==left?0:right?1:-1;
            const bool initial=direction && direction!=held_direction;
            const bool repeat=now && direction && field<3 && direction==held_direction && now>=next_repeat;
            if(initial || repeat) {
                if(field==0) amount=static_cast<uint32_t>(std::max(1,std::min(65535,static_cast<int>(amount)+direction*(event.analog[7]>30?25:1))));
                if(field==1) flags=(flags&~0x000f0000u)|(static_cast<uint32_t>(std::max(1,std::min(7,static_cast<int>(years())+direction)))<<16);
                if(field==2) flags=(flags&~15u)|static_cast<uint32_t>(std::max(0,std::min(10,static_cast<int>(bonus())+direction)));
                if(field==3) flags=(flags&0x1fffffffu)|((shape()==1?2u:1u)<<29);
                message.clear();
                next_repeat=now+(initial?350:90);
            }
            held_direction=direction;
        }
        previous_buttons=event.buttons;
        std::copy(std::begin(event.analog),std::end(event.analog),previous_analog.begin());
        return cancel?1:(!waiting && check)?2:0;
    }
};
}
#endif
