# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 11:57:10 2021

@author: amurtha
"""
# =============================================================================
# Import Packages and set parameters
# =============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon

#What genes do you want to show?
gene_list = ['TP53', 'PTEN', 'RB1', 'SPOP', 'TMPRSS2', 'BRCA2', 'ATM', 'CDK12', 'NKX3-1',
             'CLU', 'NCOA2', 'MYC', 'PIK3CA']

cn = pd.read_csv('C:/Users/amurtha/Dropbox/Ghent M1 2019/Mar2021_datafreeze/copy_number/final melted cna files/M1RP_cna.tsv', sep = '\t')
mut = pd.read_csv('C:/Users/amurtha/Dropbox/Ghent M1 2019/Mar2021_datafreeze/mutations/final melted mutations/M1RP_mutations_inclDependent.tsv', sep = '\t')
tc = pd.read_csv('https://docs.google.com/spreadsheets/d/13A4y3NwKhDevY9UF_hA00RWZ_5RMFBVct2RftkSo8lY/export?format=csv&gid=963468022')
samples = pd.read_csv('https://docs.google.com/spreadsheets/d/13A4y3NwKhDevY9UF_hA00RWZ_5RMFBVct2RftkSo8lY/export?format=csv&gid=0')
gl = pd.read_csv('C:/Users/amurtha/Dropbox/Ghent M1 2019/Mar2021_datafreeze/mutations/final melted mutations/M1RP_germline_mutations.tsv', sep = '\t')

gl['NOTES'] = gl['NOTES'].astype(str)

# =============================================================================
# Keep coding mutations
# =============================================================================

mut = mut[mut['EFFECT'].str.split(' ').str[0].isin(['Missense','Frameshift','Stopgain','Splice'])]
gl = gl[gl['NOTES'].str.contains('ClinVar:Pathogenic.')]

# =============================================================================
# Keep TC > 20.
# =============================================================================

tc.columns = tc.iloc[0]
tc = tc.drop(tc.index[0])
tc['Final tNGS_TC'] = tc['Final tNGS_TC'].astype(float)

tc = tc[tc['Final tNGS_TC']>0.2]

# =============================================================================
# Keep patients with >= 2 metastatic samples. 
# =============================================================================

samples.columns = samples.iloc[0]
samples = samples.drop(samples.index[0])

samples = samples[samples['Sample ID'].isin(tc['Sample ID'].tolist())]

samples['Sample Category'] = samples['Sample Category'].replace(dict.fromkeys(['MLN','cfDNA','MB','MT'], 'Met'))
samples['Sample Category'] = samples['Sample Category'].replace(dict.fromkeys(['RP','PB'], 'Primary'))

met_count = samples[samples['Sample Category'] == 'Met']
met_count = met_count[['Patient ID']]
met_count['met_count'] = 1
met_count = met_count.groupby('Patient ID').count().reset_index()

samples = samples.merge(met_count, on = 'Patient ID', how = 'left')
samples['met_count'] = samples['met_count'].fillna(0)

pri_count = samples[samples['Sample Category'] == 'Primary']
pri_count = pri_count[['Patient ID']]
pri_count['primary_count'] = 1
pri_count = pri_count.groupby('Patient ID').count().reset_index()

samples = samples.merge(pri_count, on = 'Patient ID', how = 'left')
samples['primary_count'] = samples['primary_count'].fillna(0)

samples = samples[(samples['met_count'] >= 1)&(samples['primary_count'] >= 1)]
patients = samples['Patient ID'].unique().tolist()

# =============================================================================
# Keep patients in samples
# =============================================================================

cn = cn[cn['Sample ID'].isin(samples['Sample ID'].tolist())]
mut = mut[mut['Sample ID'].isin(samples['Sample ID'].tolist())]

# =============================================================================
# Keep copy number data present in > 2 samples
# =============================================================================

cn = cn[cn['GENE'].isin(gene_list)]
mut = mut[mut['GENE'].isin(gene_list)]

cn['Copy_num'] = cn['Copy_num'].replace(dict.fromkeys([-1, -2], -1))
cn['Copy_num'] = cn['Copy_num'].replace(dict.fromkeys([1, 2], 1))

cn_count = cn[['Patient ID','GENE','Copy_num']].copy()
cn_count = cn_count[cn_count['Copy_num'] != 0]
cn_count['Count'] = 1
cn_count = cn_count.groupby(['Patient ID','GENE','Copy_num']).count().reset_index()
cn_count = cn_count[cn_count['Count'] >= 2]

cn = cn.merge(cn_count, on = ['Patient ID','GENE','Copy_num'])

# =============================================================================
# Add germline variants to muts
# =============================================================================

cols = ['Cohort', 'Patient ID', 'Sample ID', 'CHROM', 'POSITION', 'REF', 'ALT',
       'GENE', 'EFFECT', 'Allele_frequency', 'Read_depth', 'NOTES',
       'Independent', 'Final tNGS_TC', 'Clonal']

append_df = pd.DataFrame(columns = cols)
gl = gl[gl['Patient ID'].isin(patients)]
for index, row in gl.iterrows():
    pt_samples = tc[tc['Patient ID'] == row['Patient ID']]['Sample ID'].tolist()
    tmp = pd.DataFrame({'Cohort':['M1RP']*len(pt_samples),'Patient ID':[row['Patient ID']]*len(pt_samples),'Sample ID':pt_samples, 'CHROM':[row['CHROM']]*len(pt_samples), 'POSITION':[row['POSITION']]*len(pt_samples), 'REF':[row['REF']]*len(pt_samples), 'ALT':[row['ALT']]*len(pt_samples), 'GENE':[row['GENE']]*len(pt_samples), 'EFFECT':[row['EFFECT']]*len(pt_samples),'Allele_frequency':[0]*len(pt_samples),'Read_depth':[0]*len(pt_samples),'NOTES':[row['NOTES']]*len(pt_samples),'Independent':[True]*len(pt_samples),'Final tNGS_TC':[0]*len(pt_samples),'Clonal':[True]*len(pt_samples),'Germline':['*']*len(pt_samples)})
    append_df = append_df.append(tmp, ignore_index=True)
    
mut['Germline'] = 's'
mut = mut.append(append_df, ignore_index=True)

# =============================================================================
# Calculate offset
# =============================================================================

mut_count = mut.drop_duplicates(['Patient ID','GENE','EFFECT']).groupby(['Patient ID','GENE']).count().reset_index()
mut_count = mut_count[mut_count['CHROM'] >= 2]

mut['Offset'] = 0
mut.loc[mut['Sample ID'].isin(mut_count['Sample ID'].tolist()), 'Offset'] = 0.3

mut_count = mut_count.drop_duplicates(['Patient ID','GENE'])
mut.loc[mut['Sample ID'].isin(mut_count['Sample ID'].tolist()), 'Offset'] = -0.3

# =============================================================================
# Sort
# =============================================================================



# =============================================================================
# Assign Y values
# =============================================================================

ys = dict(zip(gene_list, np.arange(0,len(gene_list),1)))
cn['y'] = cn['GENE'].map(ys)
mut['y'] = mut['GENE'].map(ys)

# =============================================================================
# Assign color to muts and cn
# =============================================================================

cn['color'] = cn['Copy_num'].map({-1:'#9CC5E9',0:'#efefef',1:'#F59496'})
mut['color'] = mut['EFFECT'].str.split(' ').str[0].map({'Missense':'#79B443',
                                                        'Frameshift':'#FFC907',
                                                        'Stopgain':'#FFC907',
                                                        'Splice':'#BD4398'})

# =============================================================================
# Split by primary v metastatic
# =============================================================================

cn = cn.merge(samples[['Sample ID','Sample Category']], on = 'Sample ID')
mut = mut.merge(samples[['Sample ID','Sample Category']], on = 'Sample ID')

cn_primary = cn[cn['Sample Category'] == 'Primary'].copy()
cn_met = cn[cn['Sample Category'] == 'Met'].copy()

mut_primary = mut[mut['Sample Category'] == 'Primary'].copy()
mut_met = mut[mut['Sample Category'] == 'Met'].copy()

del mut, cn, tc, samples, met_count, pri_count

# =============================================================================
# 
# =============================================================================

cn_primary = cn_primary[['Patient ID','GENE','Copy_num','y','color']]
cn_primary = cn_primary.drop_duplicates()

cn_met = cn_met[['Patient ID','GENE','Copy_num','y','color']]
cn_met = cn_met.drop_duplicates()

# =============================================================================
# Assign x's and ys
# =============================================================================

factor = 2.5
xs = dict(zip(patients, np.arange(0,len(patients)*factor,factor)))

cn_primary['x'] = cn_primary['Patient ID'].map(xs)
mut_primary['x'] = mut_primary['Patient ID'].map(xs)

cn_met['x'] = cn_met['Patient ID'].map(xs) + 1
mut_met['x'] = mut_met['Patient ID'].map(xs) + 1

# =============================================================================
# Create dataframe of genes/pts with both gain and loss called
# =============================================================================

cn_primary_count = cn_primary[['GENE','Patient ID','color']].groupby(['GENE','Patient ID']).count()
cn_primary_count.columns = ['Count']

cn_primary = cn_primary.merge(cn_primary_count, left_on = ['GENE','Patient ID'], right_index = True, how = 'left')
cn_primary.loc[cn_primary['Count'] == 2, 'color'] = 'white'

# =============================================================================
# Create plot
# =============================================================================

fig,ax = plt.subplots(figsize = (7.5,5))

# =============================================================================
# plot cna data
# =============================================================================

for x in list(xs.values()):
    for y in list(ys.values()):
        ax.bar(x,0.8,bottom= y, color = '#efefef', zorder = 0)
        ax.bar(x+1,0.8,bottom= y, color = '#efefef', zorder = 0)

ax.bar(cn_primary['x'],0.8,bottom = cn_primary['y'], color = cn_primary['color'], zorder = 10)
ax.bar(cn_met['x'],0.8,bottom = cn_met['y'], color = cn_met['color'], zorder = 10)

cn_both = cn_primary[cn_primary['Count'] == 2]
for index, row in cn_both.iterrows():
    x1 = row['x'] - 0.4
    x2 = row['x'] + 0.4
    y1 = row['y']
    y2 = row['y'] + 0.8
    p1 = Polygon(np.array([[x1,y1],[x1,y2], [x2,y1]]), color = '#9CC5E9', lw = 0, zorder = 100)
    p2 = Polygon(np.array([[x2,y2],[x1,y2], [x2,y1]]), color = '#F59496', lw = 0, zorder = 100)
    ax.add_patch(p1)
    ax.add_patch(p2)

# =============================================================================
# Plot mutation data
# =============================================================================

for index, row in mut_primary.iterrows():
    ax.scatter(row['x']+row['Offset'], row['y']+0.4+row['Offset'], c = row['color'], lw = 0, zorder = 100, marker = row['Germline'], s = 8)
for index, row in mut_primary.iterrows():
    ax.scatter(row['x']+row['Offset'], row['y']+0.4+row['Offset'], c = row['color'], lw = 0, zorder = 100, marker = row['Germline'], s = 8)

# =============================================================================
# Label x and y axis
# =============================================================================

ax.set_xticks(np.array(list(xs.values()))+0.5)
ax.set_yticks(np.array(list(ys.values()))+0.4)

ax.set_xticklabels(patients, rotation = 90)
ax.set_yticklabels(gene_list)

ax.set_ylim(-0.02, len(gene_list))
ax.set_xlim(-0.52, len(patients)*factor-0.5)

fig.tight_layout()
plt.savefig('C:/Users/amurtha/Dropbox/Ghent M1 2019/Figures/Work from 2021/summary/paired_oncoprint.pdf')