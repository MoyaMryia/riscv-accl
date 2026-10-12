#include "spine-mtp-policy.h"
#include <cstdlib>
#include <iostream>
static void require(bool value) { if (!value) std::abort(); }
int main() {
    spine_mtp_config c;
    spine_mtp_policy p;
    c.mode="auto"; c.workload="code"; c.expected_output_tokens=512;
    p.begin(c,true,170); require(!p.enabled);
    c.direct_ms_per_token=100; c.calibration_id="matched"; c.calibrated_prompt_max=256;
    p.begin(c,true,170); require(p.enabled);
    p.begin(c,true,257); require(!p.enabled);
    p.begin(c,false,170); require(!p.enabled);
    c.workload="prose"; p.begin(c,true,170); require(!p.enabled);
    c.workload="code"; c.expected_output_tokens=255; p.begin(c,true,170); require(!p.enabled);
    c.expected_output_tokens=512; p.begin(c,true,170);
    int64_t t=1;
    for (int i=0;i<24;++i) {
        p.begin_cycle(t); p.begin_cycle(t+100000); // retry/replay must not restart the clock
        const bool switched=p.finish_cycle(t+360000,3,3*(i+1));
        require(switched==(i==23)); t+=400000;
    }
    require(!p.enabled && p.fallback_at==72 && p.total_us==24*360000LL);
    c.mode="off"; p.begin(c,true,170); require(!p.enabled && p.cycles==0);
    c.mode="on"; c.test_fallback_after=3; p.begin(c,true,170);
    for(int i=0;i<3;++i) { p.begin_cycle(t); require(p.finish_cycle(t+200000,2,2*(i+1))==(i==2));t+=300000; }
    require(!p.enabled && p.reason=="test_forced_boundary");
    c.test_fallback_after=0; p.begin(c,true,170); require(p.enabled && p.fallback_at==-1);
    for(int i=0;i<30;++i) { p.begin_cycle(t); require(!p.finish_cycle(t+180000,3,3*(i+1)));t+=300000; }
    require(p.enabled);
    c={}; p.begin(c,true,170); p.begin_cycle(t); require(!p.finish_cycle(t+100000,3,3));
    require(p.enabled && p.cycles==0); // unchanged legacy mode has no controller
    std::cout << "policy boundary/replay accounting/reset tests passed\n";
}
