import argparse
import pandas as pd
import numpy as np


def balance(m,p,n):
    x=np.array([m,p,n],dtype=float)
    cv=x.std()/x.mean()
    return max(0,1-cv)

m=pd.read_csv('knowledgebase/state_coverage_matrix.csv')


def build(top,output):
    s=m[m.mechanism_class=='Structural_Stabilization']
    c=m[m.mechanism_class=='Chemical_Stabilization']
    e=m[m.mechanism_class=='Physical_Encapsulation']

    rows=[]
    idx=1

    for _,a in s.iterrows():
      for _,b in c.iterrows():
        mm=a.membrane_score+b.membrane_score
        pp=a.protein_score+b.protein_score
        nn=a.nucleic_acid_score+b.nucleic_acid_score
        cov=(mm+pp+nn)/3
        bal=balance(mm,pp,nn)
        risk=a.assay_risk+b.assay_risk
        tfi=0.45*cov+0.30*bal+0.15*(2/3)-0.10*risk
        rows.append([f'IBC-G1-{idx:03d}',a.material+';'+b.material,mm,pp,nn,cov,bal,tfi])
        idx+=1

    for _,a in s.iterrows():
      for _,b in c.iterrows():
       for _,d in e.iterrows():
        mm=a.membrane_score+b.membrane_score+d.membrane_score
        pp=a.protein_score+b.protein_score+d.protein_score
        nn=a.nucleic_acid_score+b.nucleic_acid_score+d.nucleic_acid_score
        cov=(mm+pp+nn)/3
        bal=balance(mm,pp,nn)
        risk=a.assay_risk+b.assay_risk+d.assay_risk
        tfi=0.45*cov+0.30*bal+0.15*1.0-0.10*risk
        rows.append([f'IBC-G1-{idx:03d}',a.material+';'+b.material+';'+d.material,mm,pp,nn,cov,bal,tfi])
        idx+=1

    df=pd.DataFrame(rows,columns=['formulation_id','materials','membrane','protein','na','coverage','balance','predicted_tfi'])
    df=df.sort_values('predicted_tfi',ascending=False).head(top)
    df.to_csv(output,index=False)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--top',type=int,default=48)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    build(a.top,a.output)
