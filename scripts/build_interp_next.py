"""Render reviewed continuation results as scientific figures, Markdown and PDF.

No model fitting, cluster submission or statistical selection occurs here.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfgen.canvas import Canvas
from pypdf import PdfReader, PdfWriter, Transformation

from build_thesis_exploration_poster import fonts

ROOT=Path(__file__).resolve().parents[1]
BLUE='#007BB8';ORANGE='#CF711F';INK='#153044';GREY='#6C7F8B'
MODEL_NAMES={'eeg_full':'EEG','phys_specific':'Physiology','eeg+phys_specific':'EEG + physiology','training_mean':'Training mean'}
PALETTE={'eeg_full':BLUE,'phys_specific':ORANGE,'eeg+phys_specific':'#417B5A','training_mean':GREY}
plt.rcParams.update({'font.family':'Arial','font.size':12,'axes.spines.top':False,'axes.spines.right':False,
    'axes.labelcolor':INK,'text.color':INK,'xtick.color':INK,'ytick.color':INK,
    'svg.fonttype':'none','pdf.fonttype':42,'figure.facecolor':'white','axes.titleweight':'bold'})


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def savefig(fig,folder,name):
    for ext in ('png','svg','pdf'):
        fig.savefig(folder/(name+'.'+ext),dpi=200,bbox_inches='tight',facecolor='white')
    plt.close(fig)


def diagram(folder,name,nodes,arrows,caption=None):
    fig,ax=plt.subplots(figsize=(11,3.5));ax.set_xlim(0,11);ax.set_ylim(0,3.5);ax.axis('off')
    for x,y,w,h,title,body,tone in nodes:
        ax.add_patch(Rectangle((x,y),w,h,facecolor=tone,edgecolor='#C7D9E4',linewidth=1))
        ax.text(x+w/2,y+h*.70,title,ha='center',va='center',weight='bold',fontsize=13)
        ax.text(x+w/2,y+h*.33,body,ha='center',va='center',fontsize=11.5)
    for start,end in arrows:
        ax.add_patch(FancyArrowPatch(start,end,arrowstyle='->',mutation_scale=13,color=BLUE,linewidth=1.6))
    if caption:ax.text(5.5,.03,caption,ha='center',va='bottom',fontsize=11,color=GREY)
    savefig(fig,folder,name)


def figures(out):
    dest=out/'figures';dest.mkdir(exist_ok=True)
    pm=pd.read_csv(out/'metrics_per_person.csv')
    summary=pd.read_csv(out/'summary.csv')
    contrasts=pd.read_csv(out/'contrasts.csv')
    diagram(dest,'architecture',[
        (.1,1.25,2.1,.9,'EEG history','26 electrodes\n16 s at 200 Hz','#EAF4FA'),
        (3.1,2.25,3.1,1,'Temporal branch','LaBraM tokens → mean\n200 features','#EAF4FA'),
        (3.1,.6,3.1,1,'Spectral branch','Multiscale magnitudes\n832 tokens → mean','#EAF4FA'),
        (7.3,1.25,3.4,.9,'Add + GELU + linear','One value per BOLD target','#FFF0DF')],
        [((2.2,1.7),(3.1,2.7)),((2.2,1.7),(3.1,1.1)),((6.2,2.7),(7.3,1.7)),((6.2,1.1),(7.3,1.7))],
        'At 24 seconds the spectral sequence has 1,248 tokens; dense time maps are learned indices.')
    fig,ax=plt.subplots(figsize=(11,3.4))
    old=[('Fine-bin ridge, 24 s',.381,.306,.456),('Shared NeuroBOLT, 24 s',.336,.266,.405),('Shared NeuroBOLT, 16 s',.323,.255,.390)]
    for i,(label,mean,lo,hi) in enumerate(old):
        ax.errorbar(mean,2-i,xerr=[[mean-lo],[hi-mean]],fmt='o',capsize=4,color=ORANGE if i==0 else BLUE,markersize=8)
        ax.text(hi+.007,2-i,f'{mean:.3f}',va='center')
    ax.set_yticks(range(3),[r[0] for r in old][::-1]);ax.set_xlim(.2,.51)
    ax.set_xlabel('Historical mean temporal r over 22 people (95% CI)')
    ax.set_ylim(-.45,2.45)
    fig.tight_layout();fig.subplots_adjust(bottom=.26)
    fig.text(.26,.02,'Historical seven-target endpoint; distinct from the new 64-region raw-R² correction.',fontsize=10)
    savefig(fig,dest,'historical_model_comparison')
    fig,axes=plt.subplots(1,2,figsize=(11,3.5),gridspec_kw={'width_ratios':[1.3,1]})
    x=np.linspace(0,4*np.pi,400,endpoint=False);truth=np.sqrt(2)*np.sin(x);prediction=.2*truth+1
    axes[0].plot(x,truth,color=INK,label='Target: mean 0, SD 1',lw=2)
    axes[0].plot(x,prediction,color=ORANGE,label='Prediction: 0.2 × target + 1',lw=2)
    axes[0].set_xlabel('Time (illustrative)');axes[0].set_ylabel('Normalized amplitude')
    axes[0].legend(fontsize=10,loc='lower left')
    axes[1].axis('off')
    axes[1].text(0,.82,'r = 1.00',fontsize=26,weight='bold')
    axes[1].text(0,.50,r'Predictive $R^2$ = −0.64',fontsize=23,color=ORANGE)
    axes[1].text(0,.15,'Perfect cofluctuation can coexist\nwith poor amplitude and offset.',fontsize=14)
    fig.tight_layout();savefig(fig,dest,'metric_example')
    fig,ax=plt.subplots(figsize=(11,3.8))
    regional=pm[(pm.targets=='all65')&(pm.roi!='global signal clean')]
    per=regional.groupby(['person','model']).R2.mean().unstack('model').sort_index()
    order=list(MODEL_NAMES)
    for who,row in per.iterrows():ax.plot(range(4),[row[m] for m in order],color='#C4CDD4',alpha=.6,lw=.8,zorder=1)
    for i,m in enumerate(order):
        vals=per[m].to_numpy();ss=summary[(summary.model==m)&(summary.targets=='all65')&(summary.metric=='R2')].iloc[0]
        ax.scatter(np.full(len(vals),i),vals,s=20,color=PALETTE[m],alpha=.65,zorder=2)
        ax.errorbar(i+.10,ss['mean'],yerr=[[ss['mean']-ss.lo],[ss.hi-ss['mean']]],fmt='D',color=INK,capthick=2,capsize=4,zorder=3)
    ax.axhline(0,color=GREY,ls='--',lw=.8);ax.set_xticks(range(4),[MODEL_NAMES[m] for m in order])
    ax.set_ylabel(r'Raw predictive $R^2$, mean of 64 regions')
    fig.tight_layout();fig.subplots_adjust(bottom=.24)
    fig.text(.12,.02,'Dots: 22 people   Diamonds: mean and participant-bootstrap 95% CI',fontsize=10)
    savefig(fig,dest,'person_performance')
    diagram(dest,'GSR_target',[
        (.1,2.05,3.2,1,'Measured regional BOLD','Outcome used for scoring','#EAF4FA'),
        (.1,.45,3.2,1,'Measured global BOLD','Used to define residual target','#FFF0DF'),
        (4.25,1.25,2.6,1.05,'Residual BOLD','Region − fitted global term','#EAF4FA'),
        (7.6,1.25,3.15,1.05,'EEG-only predictor','Fitted to training residuals\nScored on held-out residuals','#EAF4FA')],
        [((3.3,2.55),(4.25,1.78)),((3.3,.95),(4.25,1.78)),((7.6,1.78),(6.85,1.78))],
        'Measured test global BOLD is an outcome-definition input, never an EEG-model input.')
    part=pd.read_csv(out/'partitions_summary.csv')
    a=part[part.roi=='REGIONAL_MEAN_64'].set_index('component')
    fig,axes=plt.subplots(1,2,figsize=(11,3.8),gridspec_kw={'width_ratios':[1,1.3]})
    for ax,keys,labels in [(axes[0],['EEG','physiology','joint'],['EEG','Physiology','Joint']),
                           (axes[1],['unique_EEG','unique_physiology','shared'],['Joint − physiology','Joint − EEG','EEG + phys. − joint'])]:
        vals=a.loc[keys];y=vals['mean'].to_numpy()
        ax.bar(range(3),y,color=[BLUE,ORANGE,'#8595A2'],width=.6)
        ax.errorbar(range(3),y,yerr=[y-vals.lo.to_numpy(),vals.hi.to_numpy()-y],fmt='none',ecolor=INK,capsize=4)
        ax.axhline(0,color=GREY,lw=.8);ax.set_xticks(range(3),labels,rotation=12,ha='right',fontsize=10)
    axes[0].set_ylabel(r'Raw predictive $R^2$');axes[0].set_title('Prediction scores',fontsize=13)
    axes[1].set_title('Signed score differences; not causal shares',fontsize=13)
    fig.tight_layout();savefig(fig,dest,'physiology_scores')
    lag=pd.read_csv(out/'lag_profiles.csv');coupling=lag[lag.kind=='coupling']
    fig,axes=plt.subplots(1,2,figsize=(11,3.6),sharey=True)
    for ax,band in zip(axes,['alpha','beta']):
        subset=coupling[coupling.band==band]
        rois=['Cuneus','Heschl’s gyrus','Thalamus','global signal clean'];times=np.arange(1,24,2)
        values=np.array([subset[subset.roi==roi].set_index('lag_seconds').loc[times,'mean_r'].to_numpy() for roi in rois])
        qbh=np.array([subset[subset.roi==roi].set_index('lag_seconds').loc[times,'q_BH'].to_numpy() for roi in rois])
        qby=np.array([subset[subset.roi==roi].set_index('lag_seconds').loc[times,'q_BY'].to_numpy() for roi in rois])
        im=ax.imshow(values,aspect='auto',vmin=-.4,vmax=.4,cmap='RdBu_r')
        yy,xx=np.where(qbh<.05);ax.scatter(xx,yy,s=15,facecolor='none',edgecolor=INK,lw=.7)
        yy,xx=np.where(qby<.05);ax.scatter(xx,yy,s=8,color=INK)
        ax.set_xticks(np.arange(0,12,2),times[::2]);ax.set_yticks(range(4),['Cuneus',"Heschl's",'Thalamus','Global'])
        ax.set_xlabel('Seconds before BOLD frame');ax.set_title('Alpha (8–13 Hz)' if band=='alpha' else 'Beta (13–30 Hz)',fontsize=13)
    fig.subplots_adjust(left=.10,right=.90,bottom=.20,wspace=.08)
    cax=fig.add_axes([.92,.22,.015,.60]);fig.colorbar(im,cax=cax,label='Association r')
    fig.text(.11,.02,'22 people; 96 tests. Open circle: BH < .05; filled: BY < .05. Patterns are associations.',fontsize=10)
    savefig(fig,dest,'band_lag_map')
    fig,axes=plt.subplots(1,2,figsize=(11,3.6),sharey=True)
    for ax,band in zip(axes,['alpha','beta']):
        for roi,col in [('Cuneus',BLUE),('Thalamus',ORANGE),('global signal clean',GREY)]:
            g=coupling[(coupling.band==band)&(coupling.roi==roi)].sort_values('lag_seconds')
            ax.plot(g.lag_seconds,g.mean_r,color=col,label='Global' if roi=='global signal clean' else roi)
            ax.fill_between(g.lag_seconds.to_numpy(),g.lo.to_numpy(),g.hi.to_numpy(),color=col,alpha=.15)
        ax.axhline(0,color=GREY,lw=.6);ax.set_xlabel('Seconds before frame');ax.set_title(band.capitalize(),fontsize=13)
    axes[0].set_ylabel('Mean association r and 95% interval');axes[1].legend(fontsize=10)
    fig.tight_layout();savefig(fig,dest,'lag_uncertainty')
    attr=pd.read_csv(out/'attribution_summary.csv')
    fig,ax=plt.subplots(figsize=(11,3.6));parts=[('band','delta'),('band','alpha'),('band','beta'),('segment','4-0 s before')]
    models=['ridge','NeuroBOLT']
    for j,(model,col) in enumerate(zip(models,[ORANGE,BLUE])):
        g=attr[attr.model==model]
        rows=[g[(g.kind==k)&(g.part==v)].iloc[0] for k,v in parts]
        means=np.array([r['mean'] for r in rows]);lo=np.array([r.lo for r in rows]);hi=np.array([r.hi for r in rows])
        xx=np.arange(4)+(j-.5)*.22
        ax.errorbar(xx,means,yerr=[means-lo,hi-means],fmt='o',capsize=3,label='Reported NeuroBOLT' if model=='NeuroBOLT' else 'Ridge',color=col)
    ax.axhline(0,color=GREY,lw=.8);ax.set_xticks(range(4),['Delta band','Alpha band','Beta band','Last 4 seconds'])
    ax.set_ylabel('Drop in temporal r after waveform swap');ax.legend(fontsize=10,ncol=3)
    fig.tight_layout();fig.subplots_adjust(bottom=.24)
    fig.text(.11,.02,'Historical swaps, 5 people. Published-checkpoint curve omitted: training provenance unresolved.',fontsize=10)
    savefig(fig,dest,'attribution_people')
    diagram(dest,'alignment_test',[
        (.2,1.55,4.7,1.2,'Current spectral mapping','Dense learned mixtures of scale-window indices','#EAF4FA'),
        (6.1,1.55,4.7,1.2,'Proposed controlled replacement','Fixed support-overlap mapping\n48 half-second bins','#FFF0DF'),
        (1.5,.45,8, .7,'Keep the remainder fixed','24 s spectral-only model, same frames, seeds, loss, encoder and readout','#EAF4FA')],
        [((4.9,2.15),(6.1,2.15))],
        'Removing 4,512 parameters is a regularization confound. This change remains untested.')
    fig,ax=plt.subplots(figsize=(11,3.4))
    tasks=[('Understand and freeze',0,2),('Implement alignment option',2,3),('Profile and matched comparison',5,4),('Participant analysis and figures',9,3),('Explain and present',12,2)]
    for i,(label,start,duration) in enumerate(tasks):
        ax.barh(4-i,duration,left=start,height=.55,color=BLUE if i%2==0 else '#71B1CE')
    ax.set_yticks(range(5),[x[0] for x in tasks][::-1]);ax.set_xlim(0,14);ax.set_xticks(range(0,15,2));ax.set_xlabel('Project day')
    ax.grid(axis='x',color='#E0E7EB',zorder=0);ax.set_axisbelow(True)
    fig.tight_layout();savefig(fig,dest,'two_weeks')
    return summary,contrasts


def format_stat(row):
    return f"{row['mean']:+.4f} (95% CI {row.lo:+.4f} to {row.hi:+.4f}); p={row.p:.4g}, BH={row.q_BH:.4g}, BY={row.q_BY:.4g}, d_z={row.dz:.3f}"


def documents(out,summary,contrasts):
    proto=json.loads((out/'protocol.json').read_text(encoding='utf-8'))
    main=contrasts[contrasts.family=='primary_raw_R2'].set_index('contrast')
    def value(model,targets='all65',metric='R2'):
        return summary[(summary.model==model)&(summary.targets==targets)&(summary.metric==metric)].iloc[0]
    eeg,phys,joint=(value(x) for x in ('eeg_full','phys_specific','eeg+phys_specific'))
    add=main.loc['eeg+phys_specific minus eeg_full'];unique=main.loc['eeg_full minus phys_specific']
    null=pd.read_csv(out/'nulls.csv');nn=null[(null.targets=='raw7')&(null.min_requested_seconds==63)]
    bh=int((nn.q_BH<.05).sum());by=int((nn.q_BY<.05).sum());eligible=int((nn.state=='SCORED').sum())
    peaks=pd.read_csv(out/'lag_peaks.csv');alpha=peaks[peaks.band=='alpha'].iloc[0]
    gs=value('eeg_full','gsr64')
    conclusion='EEG predicts better than these physiology features' if unique.lo>0 else 'The EEG-versus-physiology comparison remains uncertain'
    slides=[
      dict(title='What the EEG-to-BOLD evidence supports',lead='Resting EEG can support prediction research. Faithful regional reconstruction requires more than temporal correlation.',figure=None,
        bullets=[f"Existing ridge predictions: mean raw R² {eeg['mean']:.3f} across 64 regions.",conclusion+'.',
                 'The next architecture change is a controlled hypothesis, not a demonstrated improvement.'],
        notes='The study reuses VU development data: 22 people and 29 scans, five person-grouped folds. These are corrected scores from existing ridge predictions, not a new NeuroBOLT training result or clinical validation. Start by explaining what a BOLD time course is and why normalized regional values differ from an MRI image.'),
      dict(title='What NeuroBOLT computes',lead='Waveform and spectral encoders summarize the same EEG history; the model adds their pooled representations.',figure='architecture',
        notes='Trace [B,26,3200] through [B,26,16,200]. The temporal branch has 416 data tokens plus CLS, while the spectral branch has 832 tokens at 16 seconds. STFT magnitudes differ from ridge log power. The temporal branch is not explicitly frozen, and pooling after attention does not prove lost order. Source: models/model.py, models/model_multiscale.py; architecture briefing audited at c962c07; NeuroBOLT paper https://arxiv.org/html/2410.05341v2 .'),
      dict(title='The completed comparison still favours ridge',lead='Historical five-fold temporal r: ridge .381; shared NeuroBOLT 24 s .336; shared NeuroBOLT 16 s .323.',figure='historical_model_comparison',
        notes='These are historical seven-target correlations and reported confidence intervals from the completed subject-grouped experiment, not reruns in this continuation. Ridge-minus-NeuroBOLT24 was +.045 [+.023,+.067]. The 24-versus16-second gain was +.013 [−.003,+.029]. These outcomes do not establish an irreversible ceiling or universal linearity. Source: reports/NeuroBOLT hypothesis tests.md.'),
      dict(title='Correlation is not waveform accuracy',lead='The earlier physiology partition used signed squared correlation under an R² label. The correction uses prediction error.',figure='metric_example',
        notes='This is an illustrative signal, not participant data: a target with mean zero and SD one, with prediction .2×target+1. Temporal r is 1 while raw predictive R² is -.64. Define R²=1−SSE/SST using the evaluated-run mean for SST; it is a reference, not a model input. No test-fitted rescaling is applied. The former plots also clipped negative partition bars. Keep both historical outputs and explicitly labelled corrections.'),
      dict(title='People are the units of uncertainty',lead=f"EEG: R² {eeg['mean']:.3f} ± {eeg.SD:.3f}; physiology {phys['mean']:.3f} ± {phys.SD:.3f}; joint {joint['mean']:.3f} ± {joint.SD:.3f}.",figure='person_performance',
        caption=f"EEG minus physiology: ΔR² {unique['mean']:+.4f}; 95% CI [{unique.lo:.4f}, {unique.hi:.4f}]; p={unique.p:.4f}; BY={unique.q_BY:.4f}; d_z={unique.dz:.3f}; n=22.",
        notes=f'These are means ± SD across 22 people, each first averaged across 64 ROIs and their scans. Error bars are participant bootstrap 95% intervals, not SD. Primary contrast EEG−physiology: {format_stat(unique)}. Joint−EEG: {format_stat(add)}. Intervals and sign flips are exploratory/conditional because folds share training data and prior results influenced development. The two primary contrasts form one FDR family; BH and BY are both reported. ANOVA was not needed for these paired questions. The supplementary figures/physiology_scores.svg shows the signed predictive-score partition, preserving negative estimates. It is not causal variance attribution.'),
      dict(title='Global-signal regression defines another target',lead=f"For existing residual-trained ridge, mean regional r={value('eeg_full','gsr64','r')['mean']:.3f}, raw R²={gs['mean']:.3f}. GSR is retrospective.",figure='GSR_target',
        notes=f'Measured global BOLD defines the residual target but never enters the EEG feature function. Existing models were fitted to residual targets within their historical training/validation protocol; this is different from scoring a raw-trained neural model against residuals. Raw-score and residual-score tables are separate. Circular-shift null at 63 seconds: {bh}/{eligible} raw7 scans meet BH .05 and {by}/{eligible} meet BY .05; repeated scans are not new people. The 126-second sensitivity gives the same rejection counts, but training alpha autocorrelation can remain high (up to .56 at 63 seconds and .45 at126 seconds). Cyclic stationarity remains an assumption; temporal alignment does not rule out shared arousal or physiology. Across-region rho=.65 remains descriptive without a spatially valid null. Whole-run filtering and GSR do not establish online or neuronal specificity.'),
      dict(title='Lag patterns need participant uncertainty',lead=f"Alpha peak difference, thalamus minus cortex: {alpha.difference_seconds:.0f} s; bootstrap interval [{alpha.lo:.0f}, {alpha.hi:.0f}] s. Resolution: 2 s.",figure='band_lag_map',
        notes='Each scan yields band–lag associations, Fisher transformed and averaged within person before 22-person inference. This is a prespecified exploratory 96-cell family, not thousands of independent samples. BY is a dependence sensitivity, and bootstrap lag curves are in figures/lag_uncertainty.svg. Peaks are selected functionals with discrete/multimodal uncertainty. The previous rank-one penalty was chosen from outer scores, so its fitted kernels cannot provide independent HRF confirmation. Scalp mixing, temporal filtering and arousal can all contribute; a lag is not an identified vascular mechanism.'),
      dict(title='The checkpoint gate limits neural claims',lead='CKA/IG were blocked by missing CV checkpoints. Existing waveform swaps below remain descriptive evidence from five people.',figure='attribution_people',
        notes='The figure reweights historical waveform swaps across repeats and ROIs, then scans, then five people. With five people a two-sided exact sign-flip test has only 32 sign patterns and minimum p=.0625. It is descriptive reliance evidence, not a high-power causal test. Band widths differ and swapped segments can introduce boundary artifacts. The published-checkpoint curve is omitted for provenance, not its scores: published Thalamus is byte-identical to the standalone intra-scan checkpoint. All original three-model results and their complete 123-test correction remain in attribution_summary.csv. Neither published per-region checkpoints nor the intra-scan Thalamus checkpoint satisfies the requested complete-CV gate. If future checkpoints are saved, verify provenance, baseline predictions, gradient checks and IG completeness; CKA needs centered matched rows, rank/variance checks and shifted/randomized controls.'),
      dict(title='Next test: physical spectral-lag alignment',lead='Replace one dense time-axis mapping in spectral-only NeuroBOLT24 with physical support-overlap weights.',figure='alignment_test',
        notes='Keep STFT magnitude, frequency projections, scale sum, embeddings, encoder, mean readout and MSE fixed. Compare against an unchanged spectral-only model and fine-bin ridge using identical frames, folds, seeds and selection. Four fixed maps remove 4,512 parameters: a gain could reflect regularization. The falsifier is no validation error benefit or higher r with worse raw R²/amplitude, absent meaningful efficiency gain. This H1 was not executed here. Later ROI queries are inspired by MARBLE, while UnEBOLT uses ROI-conditioned pooled features and UniEFS uses fMRI representation priors; these distinct approaches are not cross-paper leaderboard comparisons.'),
      dict(title='A two-week investigation with a stopping rule',lead='Complete one controlled change and explain its result. Expand only after a profiled comparison and a new compute budget.',figure='two_weeks',
        notes='Days1–2: trace tensors and reproduce corrected scores; agree on target and checkpoint provenance. Days3–5: default-off H1 mapping and synthetic support checks. Days6–9: profile a matched development comparison; choose folds/seeds and budget before outer scoring. Full five-fold training is not promised within the present allocation. Days10–12: paired participant/error/coverage analysis. Days13–14: present positive or negative results. The student should explain feature provenance, lag support, r versus R² and why overlapping windows are not independent people. EEG collaborators review clocks/filtering; AI collaborators review inductive bias/capacity; statistical collaborators review inference and endpoint choice.')]
    text=['# NeuroBOLT: what the EEG-to-BOLD evidence supports','',
      f'Exploratory continuation · VU 22 people / 29 scans · analysis {out.name} · 2 November 2026','',
      f'**Short summary.** Correcting the existing ridge predictions gives mean regional raw R² {eeg["mean"]:.3f} for EEG, {phys["mean"]:.3f} for physiology-focused features and {joint["mean"]:.3f} jointly. {conclusion}. Participant-level inference replaces repeated-scan certainty. Neural CKA/IG are blocked by checkpoint provenance; physical spectral-lag alignment remains the next untested architecture hypothesis.','',
      'This is a 10-slide presentation with speaker notes. The linked figures include editable SVGs and vector PDFs.','']
    for i,s in enumerate(slides,1):
        text.extend([f'## Slide {i}. {s["title"]}','',s['lead'],''])
        if s.get('bullets'):text.extend(['- '+x for x in s['bullets']]+[''])
        if s['figure']:text.extend([f'![{s["title"]}](figures/{s["figure"]}.png)',''])
        text.extend(['**Speaker notes**',s['notes'],'','---',''])
    text.extend(['## Mathematical and methodological appendix','',
      r'$$R^2_{\mathrm{pred}}=1-\frac{\sum_t(y_t-\hat y_t)^2}{\sum_t(y_t-\bar y_{\mathrm{eval}})^2}.$$','',
      r'For paired effects, $d_z=\bar d/s_d$; undefined when the paired SD is zero.','',
      r'Future CKA, not run here: $\mathrm{CKA}(X,Y)=\|X^\top Y\|_F^2/(\|X^\top X\|_F\|Y^\top Y\|_F)$ for centered matrices.','',
      r'Future IG check, not run here: $\sum_i IG_i\approx f(x)-f(x_{\mathrm{ref}})$.','',
      '- [Haufe et al.: interpretation of linear weights](https://pubmed.ncbi.nlm.nih.gov/24239590/)','- [Integrated Gradients](https://proceedings.mlr.press/v70/sundararajan17a.html)',
      '- [Saliency sanity checks](https://papers.nips.cc/paper_files/paper/2018/hash/294a8ed24b1ad22ec2e7efea049b8737-Abstract.html)',
      '- [CKA](https://proceedings.mlr.press/v97/kornblith19a.html)','- [FDR, BH and BY](https://docs.scipy.org/doc/scipy-1.13.1/reference/generated/scipy.stats.false_discovery_control.html)','',
      '## Limitations','',
      'No new models were trained. Saved predictions and features reuse development people; inference conditions on the fitted models and shared training sets. Circular shifts assume stationarity; training alpha autocorrelation remains substantial in some scans even at 126 seconds. Filtered scalp EEG cannot uniquely identify neural/vascular sources. Physiology-focused leads are not guaranteed EEG-free. Existing checkpoints fail the requested complete-CV gate. No clinical, online, individual-connectivity or external-cohort validation is established.','',
      '### Supplementary figures','',
      '![Signed predictive-score partition; not causal shares](figures/physiology_scores.png)','',
      '![Lag curves with participant-bootstrap intervals](figures/lag_uncertainty.png)',''])
    (out/'presentation.md').write_text('\n'.join(text),encoding='utf-8',newline='\n')
    claims=[
      ('Cross-validated R² physiology partition','scripts/interp_report.py:physio_partition','Actually sign(r) × r²; negative bars clipped','Use raw predictive R² and retain all signed score components; no causal fraction claim.'),
      ('29-scan map t statistics','scripts/interp_maps.py:summarise','Repeated scans are not independent people','22-person Fisher-z aggregation, intervals and declared multiplicity families.'),
      ('28/29 scans significant','scripts/interp_report.py:null_analysis','Unadjusted scan tests; sqrt(scan-count) group-null shortcut',f'New raw7/63s: {bh}/{eligible} BH and {by}/{eligible} BY; group null weights people.'),
      ('Thalamus has an identified earlier HRF','scripts/interp_maps.py:rank-one alpha selection','Outer scores selected penalty; fitted/jackknife maps reuse data','Exploratory lag association with participant peak uncertainty; not identified physiology.'),
      ('Across-region rho p-value proves brain localization','reports/NeuroBOLT interpretability.md','64 regions spatially dependent','Keep rho descriptive without a valid spatial null.'),
      ('Band swaps prove unique causal importance','scripts/interp_attribution.py','Correlated bands, unequal bandwidths, few repeats and five test people','Report matched predictive reliance with participant uncertainty and perturbation artifacts.'),
      ('No significant nonlinear gain proves linear biology','historical hypothesis and nonlinear results','Insufficient difference is not equivalence or an information ceiling','The tested models did not establish a consistent advantage on these data.'),
      ('Surrogate r=.912 proves 83% raw variance recovery','historical surrogate table','Squared correlation does not establish uncalibrated predictive R²','Describe strong temporal agreement; require saved matched predictions and an error metric before claiming a recovered-variance percentage.'),
      ('Pooling caused the temporal branch failure','architecture audit and historical narrative','Feature-variability export not recovered; checkpoint provenance limited','Spectral dominance under the tested recipe is supported; mechanism remains unproven.'),
      ('CKA/IG completed','inventory.json:P2','No complete verified shared cross-person CV checkpoint set','BLOCKED; zero neural passes; no substitute heatmap.'),
      ('Published checkpoints validate unseen-person prediction','checkpoint_provenance_note.json','Published Thalamus equals the standalone intra-scan file by SHA-256','Do not use this checkpoint as unseen-person evidence; its historical curve is omitted from the presentation, with all original statistics retained.'),
      ('Physical lag alignment improved NeuroBOLT','architecture proposal H1','No H1 implementation/evaluation in this continuation','PROPOSED and untested; compact ds006040 pooling pilot is a different experiment.'),
      ('26 columns prove no target leakage','requested example assertion','Engineered cache has 13,728 columns; shape alone cannot prove provenance','Whitelist x_<scan>, verify 26×44×12 schema/channel identities, source hashes and target/frame separation; historical execution proof remains limited.')]
    audit=['# Claim audit','','Historical records remain unchanged. Corrected outputs belong to this continuation.','',
           '| Historical claim | Evidence | Limitation | Corrected statement |','|---|---|---|---|']
    audit.extend('| '+' | '.join(row)+' |' for row in claims)
    (out/'claim_audit.md').write_text('\n'.join(audit)+'\n',encoding='utf-8',newline='\n')
    two=['# Next two weeks','',
      'The current correction used zero new fits and no GPU. Any future training needs a separately agreed budget and profiled runtime.','',
      '| Days | Deliverable | Decision |','|---|---|---|',
      '| 1–2 | Explain one forward pass; reproduce metrics; agree on target/frame/participant manifest | Confirm appropriate checkpoint and raw-waveform access |',
      '| 3–5 | Default-off fixed overlap maps and physical-support checks | Preserve all remaining model components |',
      '| 6–9 | Profile unchanged spectral24 versus H1 on a predeclared development comparison | Freeze folds/seeds, budget and error endpoints before outer scoring |',
      '| 10–12 | Paired people/error/amplitude/coverage and capacity analysis | Stop if no error benefit, or if only correlation rises |',
      '| 13–14 | Reproducible package and explainable presentation | H2 only after a concluded H1 investigation |','',
      'Student responsibilities: draw tensor shapes and lag supports, distinguish association from mechanism, explain selection and FDR, and independently reproduce at least one person’s score. AI can draft code and checks; the student reviews contracts and outputs.','',
      'Human review: EEG experts verify event clocks, references and filtering; AI researchers assess mapping/regularization controls; statistical collaborators assess endpoint and participant-level inference. Monash laboratory or Emotiv access must be confirmed rather than assumed.']
    (out/'next_two_weeks.md').write_text('\n'.join(two)+'\n',encoding='utf-8',newline='\n')
    readme=['# NeuroBOLT interpretability continuation','',text[4],'',
      '- [Presentation and speaker notes](presentation.md)','- [Claim audit](claim_audit.md)','- [Two-week plan](next_two_weeks.md)',
      '- [Reading/presentation PDF](../../../output/pdf/NeuroBOLT_interpretability_next.pdf)','',
      '## New primary comparisons','',
      '| Contrast: regional mean raw R² | Mean difference ± SD | 95% CI | p | BH / BY | Paired d_z | n |',
      '|---|---|---|---|---|---|---|']
    for name,r in main.iterrows():
        readme.append(f'| {name} | {r["mean"]:+.4f} ± {r.SD:.4f} | [{r.lo:+.4f}, {r.hi:+.4f}] | {r.p:.4g} | {r.q_BH:.4g} / {r.q_BY:.4g} | {r.dz:.3f} | {int(r.n_people)} people |')
    readme.extend(['','## Evidence status','',
      '- P0 metrics/partitions: completed from existing predictions; no refit.',
      '- P1 participant lag/temporal-null/perturbation corrections: completed.',
      '- P2 CKA/IG/representation probes: blocked under the complete-CV checkpoint requirement.',
      '- P3 physical spectral-lag alignment: proposed; no model improvement claimed.','',
      f'Bootstrap B={proto["bootstrap_B"]}; participant-level sign flips use 9,999 Monte Carlo draws at n=22, exact 32 sign configurations at n=5. BH/BY families are declared in protocol.json.','',
      '## Reproduce and inspect','',
      'Run `python scripts/interp_next_tests.py` for synthetic checks. The analysis protocol records source/input hashes and original M3 locations; large data/predictions remain there. A new analysis must use a new output directory and must not silently overwrite this frozen record. Run `python scripts/build_interp_next.py --run reports/interpretability_next/'+out.name+'` to rebuild figures and documents from the small outputs.','',
      'See execution_log.json, submission.json, accounting.json and verification.json for actual completion/resource/provenance details. Rendering/QA records are separate from scientific evidence. Historical reports were preserved.'])
    readme.extend(['','## Reading support','',
      '- [Earlier architecture briefing](../../NeuroBOLT%20architecture%20research%20briefing.md)',
      '- [Architecture and frontier-model review notes](../../../research_notes/NeuroBOLT%20architecture%20research%20briefing/)',
      '- [Checkpoint provenance qualification](checkpoint_provenance_note.json)',
      '', 'Training-mean GSR R² is numerically zero; negative-sign counts at approximately machine precision are not meaningful failures. All frozen outputs are retained.','',
      'The primary 63-second temporal null rejects 28/29 scans under BH and 27/29 under BY; the 126-second sensitivity has the same counts. Alpha autocorrelation persists in some training scans, so cyclic stationarity is a substantive assumption.'])
    (out/'README.md').write_text('\n'.join(readme)+'\n',encoding='utf-8',newline='\n')
    return slides


def pdf(out,slides):
    fonts();width,height=960,540
    temporary=ROOT/'tmp/pdfs/interp_next';temporary.mkdir(parents=True,exist_ok=True)
    base=temporary/'slides_base.pdf';c=Canvas(str(base),pagesize=(width,height),initialFontName='Body')
    c.setTitle('NeuroBOLT: evidence-first interpretability');c.setAuthor('Seamus Taylor')
    placements=[]
    for i,s in enumerate(slides,1):
        c.setFillColor(colors.HexColor(INK))
        title=Paragraph(escape(s['title']),ParagraphStyle('title',fontName='Body-Bold',fontSize=34,leading=40,textColor=colors.HexColor(INK)))
        _,th=title.wrap(880,95);title.drawOn(c,40,502-th)
        lead=Paragraph(escape(s['lead']),ParagraphStyle('lead',fontName='Body',fontSize=18,leading=24,textColor=colors.HexColor(INK)))
        _,lh=lead.wrap(880,90);lead.drawOn(c,40,492-th-lh)
        top=482-th-lh
        if s.get('bullets'):
            y=top-45
            for text in s['bullets']:
                body=Paragraph(escape(text),ParagraphStyle('body',fontName='Body',fontSize=24,leading=32,textColor=colors.HexColor(INK)))
                _,h=body.wrap(840,120);body.drawOn(c,55,y-h);y-=h+25
        placement=None
        if s['figure']:
            placement=(40,65,880,top-70,out/'figures'/(s['figure']+'.pdf'))
        placements.append(placement)
        if s.get('caption'):
            c.setFont('Body',11.5);c.setFillColor(colors.HexColor(INK))
            c.drawString(40,44,s['caption'])
        c.setFont('Body',10);c.setFillColor(colors.HexColor(GREY))
        c.drawString(40,23,'VU resting-state EEG–BOLD | 22 people / 29 scans | exploratory continuation, 2 Nov 2026')
        c.drawRightString(920,23,f'{i} / 10')
        c.showPage()
    c.save()
    reader=PdfReader(base);writer=PdfWriter()
    for page,place in zip(reader.pages,placements):
        if place:
            x,y,w,h,path=place
            fig=PdfReader(path).pages[0];fw,fh=float(fig.mediabox.width),float(fig.mediabox.height)
            scale=min(w/fw,h/fh)
            page.merge_transformed_page(fig,Transformation().scale(scale).translate(x+(w-fw*scale)/2,y+(h-fh*scale)/2))
        writer.add_page(page)
    target=ROOT/'output/pdf/NeuroBOLT_interpretability_next.pdf';target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('wb') as f:writer.write(f)
    return target


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True)
    args=parser.parse_args();out=args.run.resolve()
    log=json.loads((out/'execution_log.json').read_text(encoding='utf-8'))
    if log['state']!='COMPLETE':raise ValueError('Do not render partial science as complete results')
    summary,contrasts=figures(out);slides=documents(out,summary,contrasts);target=pdf(out,slides)
    manifest={'run':out.relative_to(ROOT).as_posix(),'PDF':target.relative_to(ROOT).as_posix(),'PDF_sha256':sha(target),
              'slides':10,'figures':len(list((out/'figures').glob('*.svg'))),'renderer_sha256':sha(Path(__file__)),
              'protocol_sha256':sha(out/'protocol.json'),'figure_source_formats':['PNG','SVG','PDF'],
              'new_fits':0,'P2':'BLOCKED','required_methodology_in_speaker_notes':True}
    (out/'build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
