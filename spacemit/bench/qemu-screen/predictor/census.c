// Count actual instructions and memory bytes in one function.
#include <qemu-plugin.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

QEMU_PLUGIN_EXPORT int qemu_plugin_version=QEMU_PLUGIN_VERSION;
enum { CPUS=64, SITES=4096 };
typedef struct { _Atomic uint64_t instructions,loads,stores,load_bytes,store_bytes; } Counts;
static Counts counts[CPUS][SITES];
static _Atomic uint64_t words[SITES];
static _Atomic bool failure;
static uint64_t first,limit;
static const char *output;

static void execute(unsigned cpu,void *data) {
    unsigned site=(uintptr_t)data;
    if(cpu>=CPUS || site>=SITES) { atomic_store(&failure,true); return; }
    atomic_fetch_add(&counts[cpu][site].instructions,1);
}

static void memory(unsigned cpu,qemu_plugin_meminfo_t info,uint64_t address,void *data) {
    (void)address; unsigned site=(uintptr_t)data,shift=qemu_plugin_mem_size_shift(info);
    if(cpu>=CPUS || site>=SITES || shift>=63) { atomic_store(&failure,true); return; }
    Counts *c=&counts[cpu][site]; uint64_t bytes=UINT64_C(1)<<shift;
    if(qemu_plugin_mem_is_store(info)) { atomic_fetch_add(&c->stores,1); atomic_fetch_add(&c->store_bytes,bytes); }
    else { atomic_fetch_add(&c->loads,1); atomic_fetch_add(&c->load_bytes,bytes); }
}

#if QEMU_PLUGIN_VERSION >= 7
static void translate(struct qemu_plugin_tb *tb,void *data) {
    (void)data;
#else
static void translate(qemu_plugin_id_t id,struct qemu_plugin_tb *tb) {
    (void)id;
#endif
    for(size_t j=0;j<qemu_plugin_tb_n_insns(tb);++j) {
        struct qemu_plugin_insn *i=qemu_plugin_tb_get_insn(tb,j); uint64_t pc=qemu_plugin_insn_vaddr(i);
        if(pc<first || pc>=limit) continue;
        unsigned site=(pc-first)/2; uint8_t b[4]={0}; size_t size=qemu_plugin_insn_data(i,b,sizeof b);
        if(site>=SITES || (pc-first)%2 || (size!=2 && size!=4)) { atomic_store(&failure,true); continue; }
        uint64_t word=b[0]|(uint64_t)b[1]<<8|(uint64_t)b[2]<<16|(uint64_t)b[3]<<24|(uint64_t)size<<32;
        uint64_t old=0;
        if(!atomic_compare_exchange_strong(&words[site],&old,word) && old!=word) atomic_store(&failure,true);
        qemu_plugin_register_vcpu_insn_exec_cb(i,execute,QEMU_PLUGIN_CB_NO_REGS,(void *)(uintptr_t)site);
        qemu_plugin_register_vcpu_mem_cb(i,memory,QEMU_PLUGIN_CB_NO_REGS,QEMU_PLUGIN_MEM_RW,(void *)(uintptr_t)site);
    }
}

#if QEMU_PLUGIN_VERSION >= 7
static void finish(void *data) {
#else
static void finish(qemu_plugin_id_t id,void *data) {
    (void)id;
#endif
    (void)data; FILE *f=fopen(output,"wx");
    if(!f) { qemu_plugin_outs("census output failed\n"); return; }
    fprintf(f,"{\"schema\":3,\"failure\":%s,\"threads\":[",atomic_load(&failure)?"true":"false");
    bool comma=false;
    for(unsigned cpu=0;cpu<CPUS;++cpu) {
        uint64_t total=0;
        for(unsigned s=0;s<SITES;++s) total+=atomic_load(&counts[cpu][s].instructions);
        if(!total) continue;
        fprintf(f,"%s{\"cpu\":%u,\"instructions\":%"PRIu64",\"sites\":[",comma?",":"",cpu,total); comma=true;
        bool next=false;
        for(unsigned s=0;s<SITES;++s) {
            Counts *c=&counts[cpu][s]; uint64_t n=atomic_load(&c->instructions),w=atomic_load(&words[s]);
            if(!n) continue;
            fprintf(f,"%s{\"pc\":%"PRIu64",\"encoding\":\"%08"PRIx64"\",\"size\":%"PRIu64",\"count\":%"PRIu64",\"loads\":%"PRIu64",\"stores\":%"PRIu64",\"load_bytes\":%"PRIu64",\"store_bytes\":%"PRIu64"}",
                next?",":"",first+2*s,w&UINT64_C(0xffffffff),w>>32,n,
                atomic_load(&c->loads),atomic_load(&c->stores),atomic_load(&c->load_bytes),atomic_load(&c->store_bytes)); next=true;
        }
        fputs("]}",f);
    }
    fputs("]}\n",f); fclose(f);
}

QEMU_PLUGIN_EXPORT int qemu_plugin_install(qemu_plugin_id_t id,const qemu_info_t *info,int argc,char **argv) {
    if(strcmp(info->target_name,"riscv64")) return -1;
    for(int i=0;i<argc;++i) {
        if(!strncmp(argv[i],"start=",6)) first=strtoull(argv[i]+6,NULL,0);
        else if(!strncmp(argv[i],"end=",4)) limit=strtoull(argv[i]+4,NULL,0);
        else if(!strncmp(argv[i],"out=",4)) output=argv[i]+4;
        else return -1;
    }
    if(!output || first>=limit || limit-first>2*SITES) return -1;
#if QEMU_PLUGIN_VERSION >= 7
    qemu_plugin_register_vcpu_tb_trans_cb(id,translate,NULL);
#else
    qemu_plugin_register_vcpu_tb_trans_cb(id,translate);
#endif
    qemu_plugin_register_atexit_cb(id,finish,NULL); return 0;
}
