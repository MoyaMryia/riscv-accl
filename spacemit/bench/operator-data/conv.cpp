// 使用实际卷积计算图，保留输入与状态的独立参考检查。
#include "ggml-cpu.h"
static int operator_threads=4;
static unsigned operator_seed=123;
static ggml_threadpool_t operator_pool=nullptr;
#define main preserved_conv_main
#include "test-k1-ssm-conv.cpp"
#undef main
#include "measure.h"
static void dump_graph(Fixture &f,const char *path) {
    FILE *file=fopen(path,"wbx");require(file,"dump file");
    for(auto *v:{&f.xdata,&f.wdata,&f.hdata,&f.result,&f.state})operator_dump(file,*v);
    require(fclose(file)==0,"dump close");
}
int main(int argc,char **argv) {
    require(argc==9,"usage: conv numeric|bench CHANNELS TOKENS THREADS SEED PADDING ARM DUMP");
    bool numeric=strcmp(argv[1],"numeric")==0;
    require(numeric || strcmp(argv[1],"bench")==0,"mode");
    int c=atoi(argv[2]),t=atoi(argv[3]),padding=atoi(argv[6]),arm=atoi(argv[7]);
    operator_threads=atoi(argv[4]);operator_seed=atoi(argv[5]);
    require(c>0 && t>0 && (operator_threads==1 || operator_threads==4) && (arm==0 || arm==2),"shape");
    if(numeric){Fixture f(c,4,t,1,arm,padding);auto x=f.xdata,w=f.wdata,h=f.hdata;f.run();f.check();f.run();f.check();require(f.xdata==x && f.wdata==w && f.hdata==h,"input changed");dump_graph(f,argv[8]);return 0;}
    Fixture control(c,4,t,1,0,padding),candidate(c,4,t,1,2,padding);
    int base=1;
    for(;;){
        double shortest=1e100;
        for(int repeat=0;repeat<2;++repeat){shortest=std::min(shortest,control.run(base));shortest=std::min(shortest,candidate.run(base));}
        if(shortest>=10)break;
        require(base<1048576,"call limit");base*=2;
    }
    for(int rep=0;rep<7;++rep)for(int length=0;length<3;++length)for(int order=0;order<2;++order){
        int selected=(rep+length+order)%2,calls=base*(1<<length);Fixture &f=selected?candidate:control;
        f.run();double wall=f.run(calls);f.check();
        printf("{\"arm\":%d,\"repeat\":%d,\"length\":%d,\"calls\":%d,\"wall_ms\":%.12g,\"threads\":%d}\n",selected?2:0,rep,length,calls,wall,operator_threads);fflush(stdout);
    }
    require(control.result==candidate.result && control.state==candidate.state,"paired output changed");
}
