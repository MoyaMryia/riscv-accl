// 复用已审计的真实 IME 内核数值夹具。
#define main preserved_ime_main
#include "test-k1-ime.cpp"
#undef main
#include "measure.h"

struct OperatorTeam {
    int nth, mode=0, calls=1;
    bool stop=false, measure=false;
    pthread_barrier_t begin,end;
    std::vector<Data> data;
    std::vector<std::thread> workers;
    std::vector<OperatorCounter> counters;
    std::vector<OperatorSample> samples;
    OperatorTeam(int k,int n,int threads,int seed):nth(threads),counters(threads),samples(threads) {
        require(pthread_barrier_init(&begin,nullptr,nth+1)==0,"start barrier");
        require(pthread_barrier_init(&end,nullptr,nth+1)==0,"finish barrier");
        for(int i=0;i<nth;++i) data.emplace_back(32,k/32,n,4,false,seed+i);
        for(int i=1;i<nth;++i) {data[i].a=data[0].a;data[i].qa=data[0].qa;}
        for(int i=0;i<nth;++i) workers.emplace_back([&,i] {
            cpu_set_t mask;CPU_ZERO(&mask);CPU_SET(i,&mask);
            require(pthread_setaffinity_np(pthread_self(),sizeof(mask),&mask)==0,"worker affinity");
            for(;;) {
                pthread_barrier_wait(&begin);
                if(stop) break;
                if(measure) {counters[i].open();samples[i].begin(i);counters[i].begin();}
                for(int j=0;j<calls;++j) require(data[i].call(mode)==4,"processed rows");
                if(measure) {counters[i].end();samples[i].end(i);}
                pthread_barrier_wait(&end);
            }
        });
    }
    double run(int arm,int count,bool measured) {
        mode=arm;calls=count;measure=measured;
        auto start=Clock::now();pthread_barrier_wait(&begin);pthread_barrier_wait(&end);
        return ms(start);
    }
    void check() {for(auto &d:data){d.check(mode);d.reference();}}
    void dump(const char *path) {
        FILE *file=fopen(path,"wbx");require(file,"dump file");
        for(auto &d:data) {operator_dump(file,d.a);operator_dump(file,d.qa);operator_dump(file,d.qb);operator_dump(file,d.c);}
        require(fclose(file)==0,"dump close");
    }
    ~OperatorTeam(){stop=true;pthread_barrier_wait(&begin);for(auto &t:workers)t.join();pthread_barrier_destroy(&begin);pthread_barrier_destroy(&end);}
};

int main(int argc,char **argv) {
    require(argc==8,"usage: ime numeric|bench K N_PER_THREAD THREADS SEED ARM DUMP");
    bool numeric=strcmp(argv[1],"numeric")==0;
    require(numeric || strcmp(argv[1],"bench")==0,"mode");
    int k=atoi(argv[2]),n=atoi(argv[3]),nth=atoi(argv[4]),seed=atoi(argv[5]),arm=atoi(argv[6]);
    require(k>0 && k%32==0 && n>0 && n%16==0 && (nth==1 || nth==4) && (arm==0 || arm==1),"shape");
    OperatorTeam team(k,n,nth,seed);
    std::vector<std::vector<uint8_t>> qa,qb;
    for(auto &d:team.data){qa.push_back(d.qa);qb.push_back(d.qb);}
    if(numeric){team.run(arm,1,false);team.check();team.dump(argv[7]);}
    else {
        int base=1;
        for(;;){
            double shortest=1e100;
            for(int repeat=0;repeat<2;++repeat)for(int version=0;version<2;++version)
                shortest=std::min(shortest,team.run(version,base,false));
            if(shortest>=10)break;
            require(base<1048576,"call limit");base*=2;
        }
        for(int rep=0;rep<7;++rep) for(int length=0;length<3;++length) for(int order=0;order<2;++order) {
            int selected=(rep+length+order)%2,calls=base*(1<<length);
            team.run(selected,1,false);
            double wall=team.run(selected,calls,true);team.check();
            printf("{\"arm\":%d,\"repeat\":%d,\"length\":%d,\"calls\":%d,\"wall_ms\":%.12g,\"threads\":[",selected,rep,length,calls,wall);
            for(int i=0;i<nth;++i){if(i)printf(",");team.samples[i].emit(i,team.counters[i]);}
            puts("]}");fflush(stdout);
        }
    }
    for(int i=0;i<nth;++i)require(team.data[i].qa==qa[i] && team.data[i].qb==qb[i],"input changed");
    return 0;
}
