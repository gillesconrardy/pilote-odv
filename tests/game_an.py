import json, bisect, sys
d=json.load(open('harness_out.json')); R={int(k):v for k,v in d['rec'].items()}
def at(v,t):
    rr=R[v]; ts=[r[0] for r in rr]; i=min(max(bisect.bisect_left(ts,t),0),len(rr)-1); return rr[i][2],rr[i][3]
end=float(sys.argv[1]) if len(sys.argv)>1 else 38000
mins={}
for t in range(2500,int(end),20):
    P=[at(v,t) for v in (1,2,3,4)]
    for a in range(4):
        for b in range(a+1,4):
            dd=max(abs(P[a][0]-P[b][0]),abs(P[a][1]-P[b][1])); k=(a+1,b+1)
            if dd<mins.get(k,(99,0))[0]: mins[k]=(dd,t)
print('distance mini par paire :', {k:(round(v[0],2),v[1]) for k,v in mins.items()})
for t in list(range(4000,int(end),3000)):
    print(t, ' '.join('V%d(%.1f,%.1f)'%((v,)+at(v,t)) for v in (1,2,3,4)))
print([o[1] for o in d['out'] if o[1].startswith('V4') and any(k in o[1] for k in ('JON','CATCH','JRET','JOK','JSTUCK','MAN','BUSY','JNO'))])
