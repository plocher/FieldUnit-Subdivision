import re,glob,sys,collections
from pathlib import Path
base=Path.home()/'Dropbox/KiCad/InterlockingPlant/symbols'
def end_of(t,i):
    d=0;j=i
    while True:
        d+=(t[j]=='(')-(t[j]==')');j+=1
        if d==0:return j
def libmap(path,prefix):
    t=open(path).read();o={}
    for m in re.finditer(r'\n\t\(symbol "([^"_][^"]*)"\n',t):
        if re.search(r'_\d+_\d+$',m.group(1)):continue
        b=t[m.start()+2:end_of(t,m.start()+2)]
        o[f'{prefix}:{m.group(1)}']=dict(re.findall(r'\(property "([^"]+)" "([^"]*)"',b))
    return o
LIB={**libmap(base/'Railroad.kicad_sym','Railroad'),**libmap(base/'RailroadPanel.kicad_sym','RailroadPanel')}
NOCP={'Railroad:Bumper','Railroad:IRJ','Railroad:IRJ_Diag','Railroad:Mast_Double','Railroad:Mast_Single','Railroad:Mast_Dwarf','Railroad:MaintainerCall'}
log=collections.Counter(); detail=[]
def sweep(f):
    t=open(f).read()
    ls=t.index('(lib_symbols'); le=end_of(t,ls)
    head,lib,tail=t[:ls],t[ls:le],t[le:]
    # orphan embedded Rule6.28 copy
    used=set(re.findall(r'\(lib_id "([^"]+)"\)',tail))
    m=re.search(r'\n\t\t\(symbol "Railroad:Rule6\.28-OtherThanMain"\n',lib)
    if m and 'Railroad:Rule6.28-OtherThanMain' not in used:
        s=m.start()+3; e=end_of(lib,s)
        lib=lib[:m.start()]+lib[e:]; log['orphan embedded Rule6.28 removed']+=1
    houses=re.findall(r'\(lib_id "Railroad:MAIN HOUSE"\)[\s\S]*?\(property "Value" "([^"]*)"',tail)
    out=[];pos=0
    for m in re.finditer(r'\n\t\(symbol\n\t\t\(lib_id "([^"]+)"\)',tail):
        s=m.start()+2; e=end_of(tail,s); blk=tail[s:e]; lid=m.group(1); L=LIB.get(lid)
        new=blk
        if L:
            for k in ('Role','Kind'):
                if k in L and L[k]:
                    pm=re.search(r'\(property "'+k+r'" "([^"]*)"',new)
                    if pm and pm.group(1)!=L[k]:
                        detail.append((f.split('/')[-1],lid,k,pm.group(1),L[k])); log[f'{k} refreshed']+=1
                        new=new[:pm.start(1)]+L[k]+new[pm.end(1):]
            for k in ('Name','Direction','CP'):
                pm=re.search(r'\n\t\t\(property "'+k+r'" "([^"]*)"',new)
                if not pm: continue
                drop = (k in('Name','Direction') and k not in L) or (k=='CP' and lid in NOCP)
                if drop:
                    ps=pm.start()+3; pe=end_of(new,ps)
                    # swallow the preceding newline+tabs of the property
                    new=new[:pm.start()]+new[pe:]; log[f'{k} dropped ({lid.split(":")[1]})']+=1
        if lid=='Railroad:IRJ-Signal' and len(set(houses))==1:
            pm=re.search(r'\(property "CP" ""',new)
            if pm:
                new=new[:pm.start()]+'(property "CP" "'+houses[0]+'"'+new[pm.end():]; log['IRJ-Signal CP filled (single house)']+=1
        out.append((s,e,new))
    res=[];p=0
    for s,e,new in out:
        res.append(tail[p:s]);res.append(new);p=e
    res.append(tail[p:])
    open(f,'w').write(head+lib+''.join(res))
import os
locked={l.split('/')[0] for l in glob.glob('*/~*.lck')}|{os.path.basename(l)[1:].split('.')[0] for l in glob.glob('*/~*.lck')}
files=[f for f in sorted(glob.glob('*/*.kicad_sch')) if os.path.basename(f).split('.')[0] not in locked and f.split('/')[0] not in locked]
print('skipping locked:',sorted(locked))
for f in files: sweep(f)
for k,v in sorted(log.items()): print(v,k)
for d in detail: print('  ',d)
