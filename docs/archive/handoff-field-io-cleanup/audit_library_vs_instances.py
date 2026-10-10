import re,glob,collections,sys
from pathlib import Path
def blocks(t,start_pat):
    for m in re.finditer(start_pat,t):
        i=m.start()+2; d=0; j=i
        while True:
            d+=(t[j]=='(')-(t[j]==')'); j+=1
            if d==0: break
        yield m,t[i:j]
SKIP={'Reference','Value','Footprint','Datasheet','Description'}
def props(b): return dict(re.findall(r'\(property "([^"]+)" "([^"]*)"',b))
def libsyms(path):
    t=open(path).read(); out={}
    for m,b in blocks(t,r'\n\t\(symbol "([^"_][^"]*)"\n'):
        n=m.group(1)
        if re.search(r'_\d+_\d+$',n): continue
        out[n]=props(b)
    return out
R=Path.home()/'Dropbox/KiCad/Railroad/Archive/SPCoast'
for libname,libfile,files in [('Railroad',Path.home()/'Dropbox/KiCad/InterlockingPlant/symbols/Railroad.kicad_sym',[f for p in ['Christopher','Corporal','GilroyCalTrain','GilroyInterchange','Luchessa','Sargent','Watsonville'] for f in [R/p/f'{p}.kicad_sch']]),
   ('RailroadPanel',Path.home()/'Dropbox/KiCad/InterlockingPlant/symbols/RailroadPanel.kicad_sym',sorted((R/'South-cTc').glob('*.kicad_sch')))]:
    lib=libsyms(libfile)
    use=collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    n=collections.Counter()
    for f in files:
        t=open(f).read()
        for m,b in blocks(t,r'\n\t\(symbol\n\t\t\(lib_id "'+libname+r':([^"]+)"\)'):
            name=m.group(1); n[name]+=1
            for k,v in props(b).items():
                if k in SKIP: continue
                use[name][k][v]+=1
    print('=================',libname,'symbols:',len(lib),'used:',len(n))
    for name,p in sorted(lib.items()):
        lf={k:v for k,v in p.items() if k not in SKIP}
        diff=[]
        for k,c in use[name].items():
            for v,cnt in c.items():
                if k not in lf: diff.append(f"field {k!r} on instances only ({cnt}x {v!r})")
                elif lf[k]!=v and k in('Role','Kind','Direction','Functions'): diff.append(f"{k}: instance {v!r} ({cnt}x) != lib {lf[k]!r}")
        print(f"{name:34} n={n[name]:<3} lib={ {k:v for k,v in lf.items() if v} }")
        for d in diff: print('      !',d)
