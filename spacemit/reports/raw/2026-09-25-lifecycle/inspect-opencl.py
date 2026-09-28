import ctypes as c
cl=c.CDLL('libOpenCL.so.1')
P=c.c_void_p
U=c.c_uint
cl.clGetPlatformIDs.argtypes=[U,c.POINTER(P),c.POINTER(U)]
cl.clGetDeviceIDs.argtypes=[P,c.c_ulong,U,c.POINTER(P),c.POINTER(U)]
cl.clGetDeviceInfo.argtypes=[P,U,c.c_size_t,P,c.POINTER(c.c_size_t)]
n=U()
err=cl.clGetPlatformIDs(0,None,c.byref(n))
print('platform_count',n.value,'error',err)
if err==0 and n.value:
    platforms=(P*n.value)()
    cl.clGetPlatformIDs(n,platforms,None)
    for i,platform in enumerate(platforms):
        count=U()
        err=cl.clGetDeviceIDs(platform,0xFFFFFFFF,0,None,c.byref(count))
        print('platform',i,'device_count',count.value,'error',err)
        if err!=0 or not count.value: continue
        devices=(P*count.value)()
        cl.clGetDeviceIDs(platform,0xFFFFFFFF,count,devices,None)
        for j,device in enumerate(devices):
            vals=[]
            for key,name in ((0x102B,'name'),(0x102F,'version'),(0x103D,'opencl_c_version'),
                             (0x1030,'extensions'),(0x101F,'global_mem'),(0x1002,'compute_units'),
                             (0x1027,'available'),(0x1033,'half_fp_config')):
                buffer=c.create_string_buffer(8192)
                size=c.c_size_t()
                e=cl.clGetDeviceInfo(device,key,len(buffer),buffer,c.byref(size))
                if e: vals.append((name,'error',e))
                elif name in ('name','version','opencl_c_version','extensions'):
                    vals.append((name,buffer.value.decode(errors='replace')))
                elif name in ('global_mem','half_fp_config'):
                    vals.append((name,c.c_ulonglong.from_buffer_copy(buffer.raw[:8]).value))
                else: vals.append((name,U.from_buffer_copy(buffer.raw[:4]).value))
            print('device',j,vals)
