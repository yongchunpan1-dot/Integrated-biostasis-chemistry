import argparse
import pandas as pd
import numpy as np


def balance(m,p,n):
    x=np.array([m,p,n],dtype=float)
    cv=x.std()/x.mean()
    return max(0,1-cv)


m=pd.read_csv('knowledgebase/state_coverage_matrix.csv')


def score(mm,pp,nn,risk,module_factor):

    cov=(mm+pp+nn)/3
    bal=balance(mm,pp,nn)

    return (
        0.45*cov +
        0.30*bal +
        0.15*module_factor -
        0.10*risk
    )


def build(top,output):

    s=m[m.entropy_control_label=='Physical_Stabilization']
    c=m[m.entropy_control_label=='Chemical_Quenching']
    e=m[m.entropy_control_label=='Isolation_Encapsulation']

    structural=[]
    chemical=[]
    encapsulation=[]
    cross=[]

    for _,a in s.iterrows():
        mm=a.membrane_score
        pp=a.protein_score
        nn=a.nucleic_acid_score
        risk=a.assay_risk
        tfi=score(mm,pp,nn,risk,1/3)
        structural.append([
            f'IBC-S-{len(structural)+1:03d}',
            'Physical',
            a.material,
            mm,pp,nn,tfi
        ])

    for _,a in c.iterrows():
        mm=a.membrane_score
        pp=a.protein_score
        nn=a.nucleic_acid_score
        risk=a.assay_risk
        tfi=score(mm,pp,nn,risk,1/3)
        chemical.append([
            f'IBC-C-{len(chemical)+1:03d}',
            'Chemical',
            a.material,
            mm,pp,nn,tfi
        ])

    for _,a in e.iterrows():
        mm=a.membrane_score
        pp=a.protein_score
        nn=a.nucleic_acid_score
        risk=a.assay_risk
        tfi=score(mm,pp,nn,risk,1/3)
        encapsulation.append([
            f'IBC-E-{len(encapsulation)+1:03d}',
            'Encapsulation',
            a.material,
            mm,pp,nn,tfi
        ])

    for _,a in s.iterrows():
        for _,b in c.iterrows():
            for _,d in e.iterrows():
                mm=a.membrane_score+b.membrane_score+d.membrane_score
                pp=a.protein_score+b.protein_score+d.protein_score
                nn=a.nucleic_acid_score+b.nucleic_acid_score+d.nucleic_acid_score
                risk=a.assay_risk+b.assay_risk+d.assay_risk
                tfi=score(mm,pp,nn,risk,1.0)
                cross.append([
                    f'IBC-X-{len(cross)+1:03d}',
                    'Cross',
                    a.material+';'+b.material+';'+d.material,
                    mm,pp,nn,tfi
                ])

    columns=['formulation_id','group','materials','membrane','protein','na','predicted_tfi']

    structural_df=pd.DataFrame(structural,columns=columns).sort_values('predicted_tfi',ascending=False).head(12)
    chemical_df=pd.DataFrame(chemical,columns=columns).sort_values('predicted_tfi',ascending=False).head(12)
    encapsulation_df=pd.DataFrame(encapsulation,columns=columns).sort_values('predicted_tfi',ascending=False).head(12)
    cross_df=pd.DataFrame(cross,columns=columns).sort_values('predicted_tfi',ascending=False).head(12)

    df=pd.concat([structural_df,chemical_df,encapsulation_df,cross_df],ignore_index=True)

    print(f'Generated {len(df)} formulations')
    df.to_csv(output,index=False)
    print('\nFormulation summary:')
    print(df.groupby('group').size())


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--top',type=int,default=48)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    build(a.top,a.output)
