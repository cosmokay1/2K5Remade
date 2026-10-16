#pragma once
#include <cstdint>
#include <stdexcept>
#include <vector>
namespace franchise {
struct GuestAnnualRow {int64_t salary,bonus;int64_t charge()const{return salary+bonus;}};
/* Shared original schedule decoding. Legacy cap schedules retain their original
 * allocation; modern offer eligibility is checked separately by the caller. */
inline std::vector<GuestAnnualRow> guest_annual_rows(int64_t amount,unsigned bonus,unsigned shape,unsigned years,int64_t scale) {
    if(amount<1 || amount>65535 || bonus>10 || shape>7 || !years || years>15 || (scale!=1 && scale!=4))
        throw std::runtime_error("Unsupported saved contract schedule");
    const int64_t average=static_cast<int64_t>(static_cast<float>(static_cast<double>(amount)*10/years));
    const int64_t base=average-amount*bonus/years;
    std::vector<GuestAnnualRow> rows;
    for(unsigned i=0;i<years;++i) {
        int64_t salary=base;
        const double position=i+0.5, midpoint=years*0.5;
        if(shape==0 || shape==7) {
            int factor=position<midpoint?12:position>midpoint?8:10;
            if(shape==7) factor=20-factor;
            salary=base*factor/10;
        } else if(shape==1 || shape==6) {
            const float fraction=static_cast<float>(2*(position/years)-1);
            const int direction=shape==1?-1:1;
            salary=static_cast<int64_t>(static_cast<float>(base+direction*static_cast<double>(base/2)*fraction));
        } else if((shape==3 || shape==4) && years>1) {
            const double offset=position<=midpoint?position:position-midpoint;
            const float fraction=static_cast<float>(2*offset/midpoint-1);
            int direction=position<=midpoint?1:-1;
            if(shape==4) direction=-direction;
            salary=static_cast<int64_t>(static_cast<float>(base+direction*static_cast<double>(base/2)*fraction));
        } else if(shape==5 && years>1) salary=base*(i%2==0?12:8)/10;
        rows.push_back({salary*1000*scale,(amount*bonus/years)*1000*scale});
    }
    return rows;
}
}
