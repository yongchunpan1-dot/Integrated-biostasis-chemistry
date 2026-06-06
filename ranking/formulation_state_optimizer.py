#!/usr/bin/env python3
from itertools import combinations
from pathlib import Path
import argparse
import pandas as pd


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--ranking',default='outputs/state_coverage_ranking.csv')
    parser.add_argument('--top-materials',type=int,default=20)
    parser.add_argument('--combo-size',type=int,default=4)
    parser.add_argument('--top-formulations',type=int,default=48)
    parser.add_argument('--output',default='outputs/top48_state_formulations.csv')
    args=parser.parse_args()

    df=pd.read_csv(args.ranking)
    df=df.head(args.top_materials)

    rows=[]
    for combo in combinations(df.index,args.combo_size):
        sub=df.loc[list(combo)]
        coverage=sub['coverage_score'].sum()
        diversity=sub['category'].nunique()
        modules=sub['entropy_module'].nunique()
        score=coverage + diversity*1.5 + modules*2.0

        rows.append({
            'formulation':' + '.join(sub['material'].astype(str)),
            'materials':len(sub),
            'coverage_score':round(float(coverage),3),
            'diversity_score':diversity,
            'module_score':modules,
            'final_score':round(float(score),3)
        })

    out=pd.DataFrame(rows).sort_values('final_score',ascending=False)
    out=out.head(args.top_formulations)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(args.output,index=False)
    print(f'Generated {len(out)} formulations')

if __name__=='__main__':
    main()
