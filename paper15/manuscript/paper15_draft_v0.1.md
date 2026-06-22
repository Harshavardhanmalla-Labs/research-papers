# Fusing Real-Time and Scheduled Endpoint Telemetry for Vulnerability  Visibility: Coverage Gains, the Freshness Mechanism, and the Blind-Spot Floor

*Harshavardhan Malla, Independent Researcher*

<div class="IEEEkeywords">

asset visibility, data fusion, endpoint telemetry, vulnerability management, coverage, staleness, blind spots, pre-registration, reproducibility

</div>

# Introduction

An authorizing official can only manage the risk that the inventory makes visible. Federal asset-visibility guidance directs agencies to maintain a current account of the endpoints on their networks and of the vulnerabilities those endpoints carry , and the continuous-monitoring program that supports it treats visibility as an ongoing obligation rather than a periodic snapshot . The practical difficulty is that no single tool delivers this current account. A real-time endpoint agent reports fresh state for the assets it has been deployed to, but it never reaches the whole fleet: unmanaged hosts, network appliances, and machines outside its install base fall outside its view. A scheduled management platform covers a different and only partly overlapping set of assets, but it reports on a scan cadence, so the state it shows is as old as the last scan and is frequently stale relative to the rate at which vulnerabilities appear and are patched.

Cyber-operations teams resolve this by fusing the two feeds into one heatmap. Multisensor data fusion is the established discipline for exactly this situation: combining complementary sources of different quality, coverage, and timeliness into a single estimate that is better than any source alone , a practice that intrusion-detection research carried into security operations decades ago . The intuition that fusing a fresh-but-partial feed with a broad-but-stale feed should help is sound, but it is only an intuition. How much does fusion actually improve current-vulnerability visibility over the better single tool? What is the mechanism, so that a team can predict the gain from the properties of its two tools rather than discovering it after deployment? And what bounds the benefit, so that a program does not promise visibility that fusion structurally cannot deliver?

This paper answers those three questions with a transparent model and a pre-registered evaluation. We do not claim to measure any particular agency’s posture; we build an explicit model of two feeds with documented coverage and freshness probabilities, lock a set of hypotheses and thresholds in a dated protocol before inspecting any evaluation seed, and report what the model says with bias-corrected and accelerated bootstrap intervals  rather than significance tests. The contribution is fourfold.

- We *quantify the fusion gain*. At the reference coverage overlap, fusing the two feeds raises detection recall from 0.7498 for the better single tool to 0.8702, a gain of 0.1204 ($[0.1173, 0.1232]$) that clears a pre-registered 0.10 bar.

- We *identify the exact mechanism*. The fusion gain over the real-time feed equals, to the resolution of the experiment, the fresh coverage that only the scheduled feed adds (difference 0.0, $[-0.0, 0.0]$), because the real-time feed already supplies full freshness on its own coverage. The gain is therefore predictable from the scheduled feed’s unique fresh reach.

- We *establish a blind-spot floor*. Assets that neither tool covers place a hard lower bound on missed vulnerabilities. The fusion miss of 0.0788 exceeds this floor of 0.051 ($[0.0489, 0.0539]$), and no fusion logic can detect below it; only new coverage can.

- We *characterize the overlap dependence*. The gain decreases monotonically as the two tools’ coverage overlaps and becomes redundant, from 0.1489 at low overlap to 0.0 at full overlap, while the blind spot simultaneously grows from 0.0 to 0.2475, so high overlap is doubly unfavorable.

The methodology is deliberately conservative. Every quantitative claim is a pre-registered hypothesis evaluated on seeds that were not inspected during model development, and every interval is a BCa bootstrap interval  rather than a null-hypothesis significance test, following the pre-registration discipline now standard in empirical software engineering .

# Background and Related Work

## Multisensor and data fusion

The combination of complementary sensors into a single, better estimate is the founding idea of multisensor data fusion . The discipline distinguishes sources by their coverage, accuracy, and timeliness, and provides a vocabulary for the levels at which they can be combined, from raw-signal alignment to decision-level voting. Security operations adopted these ideas early: fusing the alerts of multiple intrusion-detection sensors was proposed as a way to raise true-positive coverage while suppressing the noise of any single sensor . Our setting is a decision-level fusion of two detection feeds, where the relevant axes are coverage (which assets a feed can see) and freshness (whether what it reports is current). We make those two axes explicit and derive the gain from them, rather than treating fusion as an opaque combiner.

## Anomaly and vulnerability detection

Detection in security operations has a long lineage in anomaly detection, whose surveys catalog the recurring trade-off between catching more events and tolerating more noise . A vulnerability heatmap is a detection problem of this kind: each asset either does or does not carry a current vulnerability, and a feed either does or does not report it. Because the cost of a missed current vulnerability dominates, recall is the operationally meaningful metric, and the precision-recall framing is the appropriate evaluation lens for the skewed, miss-sensitive regime we study . Prior hygiene and prioritization work in this program established that endpoint telemetry arrives over several distinct channels with different reliability and timeliness ; the present paper isolates the coverage-and-freshness structure of two such channels and the consequences of fusing them.

## Federal asset-visibility mandates

The motivation is not abstract. The federal binding operational directive on asset visibility requires agencies to discover their assets and detect vulnerabilities on a regular cadence across the whole fleet , and the continuous-monitoring framework that surrounds it  reframes visibility as an ongoing program. The control catalog  and the categorization standard  that determine which assets matter most assume an inventory that is both broad and current, which is precisely what a single tool cannot supply and fusion is meant to approximate. Breach data continues to attribute incidents to known, unremediated weaknesses , so the assets a visibility program misses are not an academic concern; they are where exposure concentrates. The autonomic-computing vision of systems that continuously sense and manage their own state  anticipated this shift toward fused, continuous self-assessment.

## Evaluation discipline

We follow the evaluation conventions of empirical software engineering : hypotheses and thresholds are fixed before the evaluation data are seen, and uncertainty is reported as a bootstrap interval. We use the bias-corrected and accelerated bootstrap  because the statistics of interest are small-sample and possibly skewed, and we judge claims by interval non-overlap rather than by significance tests, avoiding the multiple-comparison hazards of repeated $p$-values across four hypotheses and five overlap levels.

# System Model

We model a fleet of endpoints observed by two feeds and ask how much current-vulnerability visibility each monitoring regime delivers. All quantities are synthetic with documented distributions; no operational, employer, or telemetry data is used.

## Fleet and coverage

Each seed instantiates a fleet of $N = 5{,}000$ assets. The real-time feed $R$ covers each asset with marginal probability $c_R = 0.75$; the scheduled feed $S$ covers each asset with marginal probability $c_S = 0.70$. The joint coverage is parameterized by the probability $p_{\cap}$ that an asset is covered by both feeds, which we sweep over $\{0.45, 0.50, 0.55, 0.60, 0.70\}$ with $0.50$ as the reference. Each asset thus falls into one of four coverage classes: both feeds, real-time only, scheduled only, or neither. The four class probabilities follow directly from the marginals and $p_{\cap}$, $$\Pr(R\text{ only}) = c_R - p_{\cap}, \quad \Pr(S\text{ only}) = c_S - p_{\cap},
\label{eq:classes}$$ and the *blind-spot rate*, the share of assets that neither feed covers, is the complement of the coverage union, $$\beta \;=\; 1 - \big(c_R + c_S - p_{\cap}\big)\;=\; 1 - c_R - c_S + p_{\cap}.
\label{eq:blindspot}$$ The blind-spot rate rises one-for-one with the overlap $p_{\cap}$: the more the two feeds duplicate each other’s coverage, the less of the fleet they jointly reach. At the reference overlap this gives $\beta = 0.051$, and across the sweep it grows from 0.0 to 0.2475.

## Freshness and detection

Each asset carries a true current vulnerability with prevalence $0.30$; this only sizes the evaluated sample, since recall is computed over the current-vulnerability assets. A feed *detects* a current vulnerability when it covers the asset and its report is fresh. The real-time feed is fresh wherever it covers, reflecting its continuous reporting. The scheduled feed is fresh with probability $\phi = 0.60$ where it covers, the remaining $0.40$ being stale because the scan cadence is slower than the rate at which vulnerabilities change. The per-feed recalls are therefore approximately constant across overlap levels, governed by coverage and freshness rather than by how the two feeds relate: the real-time feed detects at recall about $0.75$ and the scheduled feed at recall about $0.42$, the latter being its coverage discounted by its freshness.

## The fusion rule and its gain

Fusion takes the freshest available signal per asset: a current vulnerability is detected if the real-time feed covers the asset, or the scheduled feed covers it and is fresh. This is a decision-level union of detections, $$\mathrm{Detect}_{\text{fuse}} \;=\; \big[\,R\text{ covers}\,\big] \;\vee\; \big[\,S\text{ covers} \;\wedge\; S\text{ fresh}\,\big].
\label{eq:fusion}$$ Because the real-time feed already contributes full freshness on everything it covers, fusion adds exactly the assets the real-time feed does *not* cover but the scheduled feed does and reports fresh. That increment, the *scheduled-only-fresh coverage* $\phi\,(c_S - p_{\cap})$, is the entire source of the fusion gain over the real-time feed. Detection recall is the fraction of current-vulnerability assets a regime detects ; the fusion miss rate is one minus fusion recall, and it can never fall below the blind-spot rate $\beta$ of Eq. (<a href="#eq:blindspot" data-reference-type="ref" data-reference="eq:blindspot">[eq:blindspot]</a>), because an asset neither feed covers cannot be detected by any combination rule. The blind spot is thus a floor on misses that fusion is structurally unable to lower; only extending coverage can.

# Theoretical Analysis

The three empirical findings are not coincidences of the chosen constants; each follows in closed form from the coverage-and-freshness structure of Section <a href="#sec:model" data-reference-type="ref" data-reference="sec:model">3</a>. This section derives the fusion identity exactly, shows that the fusion gain over the better single feed equals the scheduled-only-fresh coverage with no residual, proves the blind-spot floor on misses, and characterizes how the gain decays as the feeds become redundant. We then check each derived value against the frozen results and state the match explicitly.

Throughout we work over the population of current-vulnerability assets, since recall is computed on that population (Section <a href="#sec:model" data-reference-type="ref" data-reference="sec:model">3</a>). Detection by a feed is a coverage-and-freshness event. Let an asset be covered by the real-time feed $R$ with marginal probability $c_R$ and by the scheduled feed $S$ with marginal probability $c_S$, with both-feed probability $p_{\cap}$. Write $\phi$ for the scheduled feed’s freshness, and recall that the real-time feed is fresh wherever it covers. With $r_{\mathrm{rt}}$ the probability that the real-time feed detects an asset’s current vulnerability, the model’s freshness assumption gives the per-feed recalls in closed form, $$r_{\mathrm{rt}} \;=\; c_R, \qquad r_{\mathrm{sch}} \;=\; \phi\,c_S,
\label{eq:single_recalls}$$ because the real-time feed detects exactly where it covers, while the scheduled feed detects only where it both covers and is fresh.

## The fusion identity in closed form

Fusion detects a current vulnerability when the real-time feed covers the asset, or the scheduled feed covers it and is fresh (Eq. <a href="#eq:fusion" data-reference-type="ref" data-reference="eq:fusion">[eq:fusion]</a>). Equivalently, fusion misses an asset only when *neither* feed detects it: the real-time feed does not cover it, and the scheduled feed either does not cover it or covers it stale. Writing the fused recall as one minus the probability that neither feed detects, $$\mathrm{recall}_{\text{fuse}}
\;=\; 1 - \Pr\!\big(R\text{ misses}\,\wedge\, S\text{ misses fresh}\big).
\label{eq:fuse_complement}$$ The real-time feed misses with probability $1 - c_R$ (its uncovered assets), and these are exactly the assets where the scheduled feed must carry the load. Conditioning on the real-time miss and using the coverage accounting of Eq. (<a href="#eq:classes" data-reference-type="ref" data-reference="eq:classes">[eq:classes]</a>), the scheduled feed covers a real-time-miss asset and reports it fresh precisely on the scheduled-only-fresh class, of probability $\phi\,(c_S - p_{\cap})$. Hence $$\mathrm{recall}_{\text{fuse}}
\;=\; c_R \;+\; \phi\,(c_S - p_{\cap}).
\label{eq:fuse_recall}$$ The first term is the real-time feed’s own detection, complete and fresh on its coverage; the second term is the fresh reach the scheduled feed adds outside that coverage. Equation (<a href="#eq:fuse_recall" data-reference-type="ref" data-reference="eq:fuse_recall">[eq:fuse_recall]</a>) is the fusion identity: the fused recall is the real-time recall plus the scheduled-only-fresh coverage, with no cross term, because the real-time feed already supplies full freshness on everything it covers and the scheduled feed can add value only off that footprint.

## The fusion gain equals the scheduled-only-fresh coverage

Because the real-time feed is the better single feed in our regime ($r_{\mathrm{rt}} = c_R = 0.75$ against $r_{\mathrm{sch}} = \phi\,c_S \approx 0.42$ from Eq. <a href="#eq:single_recalls" data-reference-type="ref" data-reference="eq:single_recalls">[eq:single_recalls]</a>), the fusion gain over the better single feed is the gain over the real-time feed. Subtracting $r_{\mathrm{rt}} = c_R$ from Eq. (<a href="#eq:fuse_recall" data-reference-type="ref" data-reference="eq:fuse_recall">[eq:fuse_recall]</a>), $$\Delta \;\equiv\; \mathrm{recall}_{\text{fuse}} - r_{\mathrm{rt}}
\;=\; \phi\,(c_S - p_{\cap}).
\label{eq:gain}$$ The gain is *exactly* the scheduled-only-fresh coverage $\phi\,(c_S - p_{\cap})$, with the residual identically zero by construction: there is no leftover term to attribute to the fusion rule, because the union in Eq. (<a href="#eq:fusion" data-reference-type="ref" data-reference="eq:fusion">[eq:fusion]</a>) adds nothing on the real-time footprint. At the reference overlap $p_{\cap} = 0.50$, Eq. (<a href="#eq:gain" data-reference-type="ref" data-reference="eq:gain">[eq:gain]</a>) predicts $\Delta = 0.60\,(0.70 - 0.50) = 0.1200$. The frozen results report a fusion gain over the real-time feed of $0.1204$ and a scheduled-only-fresh coverage of $0.1204$, a difference of $0.0$ with BCa interval $[-0.0, 0.0]$. *The derived gain $0.1204$ matches the measured scheduled-only-fresh coverage $0.1204$, and the mechanism difference is $0.0$, as Eq. (<a href="#eq:gain" data-reference-type="ref" data-reference="eq:gain">[eq:gain]</a>) requires.*

## The blind-spot floor on misses

The fused miss rate is the complement of Eq. (<a href="#eq:fuse_recall" data-reference-type="ref" data-reference="eq:fuse_recall">[eq:fuse_recall]</a>). Every asset that neither feed covers is undetectable by any combination rule, so the fused miss can never fall below the blind-spot rate $\beta$ of Eq. (<a href="#eq:blindspot" data-reference-type="ref" data-reference="eq:blindspot">[eq:blindspot]</a>). Decomposing the miss into its two disjoint sources, the uncovered assets and the scheduled-only-but-stale assets, $$1 - \mathrm{recall}_{\text{fuse}}
\;=\; \underbrace{\big(1 - c_R - c_S + p_{\cap}\big)}_{\beta}
\;+\; \underbrace{(1-\phi)\,(c_S - p_{\cap})}_{\text{stale scheduled-only}}.
\label{eq:miss_decomp}$$ The second term is non-negative because $\phi \le 1$ and $c_S \ge p_{\cap}$, so the miss is the blind-spot floor plus a non-negative stale-coverage residual, $$1 - \mathrm{recall}_{\text{fuse}} \;\ge\; \beta,
\label{eq:floor}$$ with equality only when the scheduled feed is perfectly fresh on its non-overlapping coverage. The floor is a coverage limit, not a fusion limit: it is the information the union of the two feeds simply does not carry about the uncovered assets, and no decision rule built on these two feeds can recover it . At the reference overlap, Eq. (<a href="#eq:miss_decomp" data-reference-type="ref" data-reference="eq:miss_decomp">[eq:miss_decomp]</a>) predicts a floor $\beta = 1 - 0.75 - 0.70 + 0.50 = 0.05$ and a stale-coverage residual $(1-0.60)(0.70-0.50) = 0.40 \times 0.20 = 0.032$ before sampling, summing to a fused miss near $0.082$. The frozen results report a fusion miss of $0.0788$ and a blind-spot rate of $0.051$ with BCa interval $[0.0489, 0.0539]$. *The measured fusion miss $0.0788$ exceeds the blind-spot floor $0.051$, satisfying $1 - \mathrm{recall}_{\text{fuse}} \ge \beta$ as Eq. (<a href="#eq:floor" data-reference-type="ref" data-reference="eq:floor">[eq:floor]</a>) requires.*

## Decay of the gain as coverage becomes redundant

The overlap dependence is read directly off Eq. (<a href="#eq:gain" data-reference-type="ref" data-reference="eq:gain">[eq:gain]</a>). As the feeds duplicate each other’s coverage, $p_{\cap}$ rises toward $c_S$, the scheduled feed’s marginal coverage. The scheduled-only coverage $c_S - p_{\cap}$ shrinks, and at $p_{\cap} = c_S$ it vanishes, so $$\lim_{p_{\cap}\to c_S} \Delta \;=\; \phi\,(c_S - c_S) \;=\; 0.
\label{eq:decay}$$ The gain decays linearly in $p_{\cap}$ with slope $-\phi$, reaching zero exactly when the scheduled feed covers nothing the real-time feed does not, since at that point fusion has no unique fresh asset to add. Evaluating Eq. (<a href="#eq:gain" data-reference-type="ref" data-reference="eq:gain">[eq:gain]</a>) on the overlap grid $\{0.45, 0.50, 0.55, 0.60, 0.70\}$ gives the predicted gains $\{0.1500, 0.1200, 0.0900, 0.0600, 0.0000\}$. The frozen results report the gain sequence $\{0.1489, 0.1204, 0.0886, 0.0595, 0.0\}$. *The measured gain sequence $\{0.1489, 0.1204, 0.0886, 0.0595, 0.0\}$ tracks the closed-form prediction and decays to $0.0$ at overlap $0.70$, as Eq. (<a href="#eq:decay" data-reference-type="ref" data-reference="eq:decay">[eq:decay]</a>) requires.* The same limit drives the blind spot the other way: substituting $p_{\cap} = c_S$ into Eq. (<a href="#eq:blindspot" data-reference-type="ref" data-reference="eq:blindspot">[eq:blindspot]</a>) gives $\beta = 1 - c_R = 0.25$, so full overlap simultaneously erases the gain and enlarges the blind spot, the doubly-unfavorable regime confirmed by the sweep.

# Experimental Design

The study is pre-registered. Hypotheses, thresholds, model constants, and the evaluation seed range were fixed in a dated protocol before any result on the evaluation seeds was inspected, so that no analytic choice could be steered by the outcome.

## Hypotheses

**H1 (fusion gain).** At the reference coverage overlap, fusing the two feeds detects current vulnerabilities at a recall at least 0.10 higher than the better single feed, with the BCa interval excluding 0.10.

**H2 (blind-spot floor).** Assets covered by neither feed form a hard floor on missed vulnerabilities: the fusion miss rate is at least the blind-spot rate, and no freshness improvement reduces it below that floor. The residual miss above the floor is attributable to stale scheduled-only coverage.

**H3 (freshness mechanism).** Fusion’s recall gain over the real-time feed alone equals the fresh coverage that only the scheduled feed provides, because the real-time feed already supplies full freshness on its own coverage; the difference between the two is zero within the experiment’s resolution.

**H4 (overlap dependence).** Fusion’s recall gain over the better single feed decreases as the coverage overlap between the two feeds increases, and high overlap simultaneously enlarges the blind spot.

## Protocol and statistics

Each hypothesis is evaluated over 25 evaluation seeds (frozen range 1000 to 1024) at each of the five overlap levels, for 125 primary rows. For every quantity we report the mean and a 95% BCa bootstrap interval with 10,000 resamples ; interval non-overlap, not a $p$-value, is the evidentiary standard. The pre-registered failure criteria are explicit: H1 is declared null if fusion does not exceed the better single feed by at least 0.05 recall at the reference overlap; H2 is rejected if the fusion miss rate falls below the blind-spot rate, which would indicate a model error since blind-spot assets cannot be detected; H4 is rejected if the gain does not decrease across the overlap sweep. No coverage, overlap, or freshness probability is re-tuned to reach any threshold. The development of the model used separate seeds; the evaluation seeds were touched only once, to produce the numbers below.

# Results

Table <a href="#tab:summary" data-reference-type="ref" data-reference="tab:summary">[tab:summary]</a> collects the per-overlap quantities with their intervals; all four hypotheses are supported. We take them in turn.

<div class="tabular">

@cccc@ Overlap $p_{\cap}$ & Fusion gain & Blind-spot $\beta$ & Note 
& 0.1489 & 0.0000 & maximum gain 
0.50 & 0.1204 & 0.0510 & reference 
0.55 & 0.0886 & 0.1012 & 
0.60 & 0.0595 & 0.1495 & 
0.70 & 0.0000 & 0.2475 & gain vanishes 
 
& 0.8702 & 
& 0.7498 & 
& 0.1204 & $[0.1173, 0.1232]$ 
& 0.0788 & 
& 0.0510 & $[0.0489, 0.0539]$ 
& 0.0000 & $[-0.0000, 0.0000]$ 
& 0.1489 & $[0.1456, 0.1525]$ 

</div>

**Fusion improves recall well past the bar (H1).** At the reference overlap, fusion detects current vulnerabilities at recall 0.8702 against 0.7498 for the better single feed, the real-time agent, and 0.42 for the scheduled feed. The gain over the better single feed is 0.1204 ($[0.1173, 0.1232]$), which clears both the pre-registered 0.10 bar, with the whole interval above it, and the 0.05 failure threshold by a wide margin (Fig. <a href="#fig:regimes" data-reference-type="ref" data-reference="fig:regimes">1</a>). Fusion recovers the scheduled feed’s additional coverage and the real-time feed’s freshness in a single estimate.

**The blind spot is a hard floor (H2).** The blind-spot rate at the reference overlap is 0.051 ($[0.0489, 0.0539]$). The fusion miss of 0.0788 exceeds this floor and decomposes into it plus a 0.0277 residual from stale scheduled-only assets, those the real-time feed does not cover and the scheduled feed covers but reports stale. The fusion miss is strictly above the floor, never below it, exactly as the model requires: no combination of these two feeds can detect an asset that neither covers. The remedy for the floor is not better fusion logic but additional coverage.

**The gain is exactly the scheduled-only-fresh coverage (H3).** Fusion’s improvement over the real-time feed alone is 0.1204, and the scheduled-only-fresh coverage, the fresh reach unique to the scheduled feed, is also 0.1204; the difference is 0.0 ($[-0.0, 0.0]$). The real-time feed already supplies full freshness on its own coverage, so fusion can add nothing there and adds precisely the scheduled feed’s unique fresh assets. This identity makes the gain predictable from two measurable tool properties, the scheduled feed’s non-overlapping coverage and its freshness, without running the fusion at all.

**The gain shrinks with overlap, and the blind spot grows (H4).** As the coverage overlap rises across $\{0.45, 0.50, 0.55, 0.60, 0.70\}$, the fusion gain falls monotonically through $\{0.1489, 0.1204, 0.0886, 0.0595, 0.0\}$, a drop from low to high overlap of 0.1489 ($[0.1456, 0.1525]$), while the blind spot grows through $\{0.0, 0.051, 0.1012, 0.1495, 0.2475\}$ (Fig. <a href="#fig:overlap" data-reference-type="ref" data-reference="fig:overlap">2</a>). At full overlap (0.70) the scheduled feed covers nothing the real-time feed does not, so its unique fresh coverage is zero and the fusion gain vanishes, while a quarter of the fleet has fallen into the blind spot. High overlap is therefore doubly unfavorable: it both removes the reason to fuse and enlarges the region neither feed can see.


![Detection recall by regime at the reference overlap. Fusion (0.8702) approaches the coverage union, well above the real-time feed (0.7498) and the scheduled feed; the blind spot is the floor that fusion cannot cross.](fig1_regimes.png)



![As coverage overlap rises from 0.45 to 0.70, the fusion gain falls from 0.1489 to 0.0 while the blind spot grows from 0.0 to 0.2475. High overlap removes the gain and enlarges the blind spot at once.](fig2_overlap.png)


# Robustness and Sensitivity

The headline results are reported at the reference overlap, but the contribution of this paper is structural, and the structure is best seen across the full overlap sweep. This section presents the complete sweep and then examines the one scenario the model cannot defend against by fusion alone: an adversary who hides in the blind spot.

## Full overlap sweep

Table <a href="#tab:sweep" data-reference-type="ref" data-reference="tab:sweep">1</a> reports every primary quantity at each of the five overlap levels: the real-time recall, the scheduled recall, the fused recall, the fusion gain over the better single feed, and the blind-spot rate, each a mean over the 25 evaluation seeds. The per-feed recalls are nearly flat across the sweep, near $0.75$ for the real-time feed and near $0.42$ for the scheduled feed, confirming Eq. (<a href="#eq:single_recalls" data-reference-type="ref" data-reference="eq:single_recalls">[eq:single_recalls]</a>): the single-feed recalls depend on coverage and freshness, not on how the two coverage sets relate. The fused recall, the fusion gain, and the blind spot, by contrast, all move with the overlap, and they move exactly as the closed-form analysis of Section <a href="#sec:theory" data-reference-type="ref" data-reference="sec:theory">4</a> predicts. The fused recall falls from $0.9001$ at low overlap to $0.7525$ at full overlap, where it coincides with the real-time recall because the scheduled feed has no unique fresh asset left to add. The gain falls monotonically from $0.1489$ to $0.0$ while the blind spot grows monotonically from $0.0$ to $0.2475$. The sweep is therefore a sensitivity analysis on the one parameter that distinguishes a pair of complementary feeds from a pair of redundant ones, and it shows the gain to be entirely governed by that parameter through Eq. (<a href="#eq:gain" data-reference-type="ref" data-reference="eq:gain">[eq:gain]</a>).

<div id="tab:sweep">

| Overlap $p_{\cap}$ | Real-time | Scheduled | Fusion | Gain | Blind-spot $\beta$ |
|:------------------:|:---------:|:---------:|:------:|:------:|:------------------:|
| 0.45 | 0.7511 | 0.4194 | 0.9001 | 0.1489 | 0.0000 |
| 0.50 | 0.7498 | 0.4153 | 0.8702 | 0.1204 | 0.0510 |
| 0.55 | 0.7497 | 0.4200 | 0.8382 | 0.0886 | 0.1012 |
| 0.60 | 0.7522 | 0.4213 | 0.8116 | 0.0595 | 0.1495 |
| 0.70 | 0.7525 | 0.4210 | 0.7525 | 0.0000 | 0.2475 |

Full overlap sweep: per-feed recall, fused recall, fusion gain over the better single feed, and blind-spot rate, each a mean over 25 evaluation seeds. Values are read from the frozen primary results.

</div>

## The adversarial blind spot

The blind-spot floor of Eq. (<a href="#eq:floor" data-reference-type="ref" data-reference="eq:floor">[eq:floor]</a>) is a structural limit under benign asset placement, but it becomes a security property under adversarial placement. Consider an adversary who controls where a vulnerable asset sits relative to the two feeds’ coverage, by introducing an unmanaged host, a network appliance outside the real-time agent’s install base, or a machine the scheduled scanner never reaches. Such an adversary places the asset in the blind spot, the coverage class that neither feed sees, of probability $\beta$ in Eq. (<a href="#eq:blindspot" data-reference-type="ref" data-reference="eq:blindspot">[eq:blindspot]</a>). By the fusion identity Eq. (<a href="#eq:fuse_recall" data-reference-type="ref" data-reference="eq:fuse_recall">[eq:fuse_recall]</a>), an asset in the blind spot contributes nothing to either term of the fused recall: the real-time feed does not cover it, so the first term excludes it, and the scheduled feed does not cover it, so the second term excludes it. The asset is therefore invisible to fusion *by construction*, not by any failure of the fusion logic, and no decision rule built on these two feeds can detect it . This is the worst case for a fused heatmap: an adversary who knows the coverage map can guarantee non-detection by occupying the one region the union of feeds does not reach. The implication is sharp and matches the deployment guidance: closing the blind spot requires new coverage, a third feed with complementary reach or the discovery and onboarding of unmanaged assets, and not a better way of merging the two feeds that already exist. Refining the fusion rule cannot move an asset out of the blind spot; only extending coverage can. The blind-spot rate $\beta$ is thus both the benign floor on misses and the adversarial measure of how much of the fleet an attacker can render invisible by placement alone, and it is the quantity a visibility program should drive down.

# Discussion

The three findings combine into a single deployment principle: fusion is worth doing exactly to the extent that the two feeds are complementary, and its value is bounded by what they jointly cover. The gain is not a property of the fusion algorithm, which is a simple union; it is the scheduled-only-fresh coverage that the second feed contributes, and the identity in H3 lets a team estimate it before deploying anything. A team can measure the scheduled feed’s coverage outside the real-time feed’s footprint, multiply by its freshness, and read off the gain to within the resolution of our experiment. Where the two feeds overlap, fusion adds nothing, because the real-time feed already supplies full freshness there; where neither feed reaches, fusion cannot help, because the blind spot is a floor that no combination rule can lower.

This reframes the visibility program. The binding constraint on current-vulnerability visibility is not the sophistication of the fusion, but the blind spot, the assets that neither tool covers. At the reference overlap that floor is 0.051, and it grows to 0.2475 as the tools become redundant. An agency that wants to push visibility past the floor must extend coverage, by deploying the real-time agent more broadly, adding a third feed with complementary reach, or discovering and onboarding unmanaged assets, rather than refining how the existing two feeds are merged. The overlap result sharpens the tool-selection decision: agencies should pair tools with complementary coverage and accept that redundant footprints are doubly wasteful, since they neither add fusion gain nor shrink the blind spot. The autonomic-computing goal of continuous self-assessment is best served by feeds chosen for complementarity .

## A deployment recipe from the identity

The closed-form identity turns the design of a fusion deployment into three measurements that a team can take before committing to any integration work. First, estimate the real-time feed’s coverage and the scheduled feed’s coverage independently, for example from each tool’s own asset inventory against the authoritative fleet list. Second, estimate the overlap, the fraction of assets both feeds reach, since the gain falls as that overlap rises: from 0.1489 at an overlap of 0.45 to 0.0 at an overlap of 0.70, where the second feed is fully redundant. Third, multiply the scheduled feed’s out-of-footprint coverage by its freshness to read off the expected fusion gain directly, because that product is the scheduled-only-fresh coverage that the identity equates to the gain. A team that performs these three measurements can predict the value of fusion to within the resolution of our experiment without integrating anything, and can decline the integration when the predicted gain is small.

The same measurements bound the residual risk. The blind-spot rate, the fraction of assets neither feed reaches, is the floor on missed current vulnerabilities and is read off the same coverage estimates: it is 0.051 at the reference overlap and rises to 0.2475 as the feeds become redundant. Because that floor is invariant to the fusion rule, it belongs on the visibility program’s risk register as a coverage-extension item, not a fusion-tuning item. The operational ordering follows: measure coverage and overlap, fuse when the predicted gain justifies the integration, and treat the blind spot as the next coverage investment. This is the discipline that distinguishes a visibility program that compounds its feeds from one that merely accumulates redundant ones.

# Threats to Validity

*Construct validity.* The model abstracts detection as a coverage-and-freshness event and a current vulnerability as a binary per-asset fact. Real feeds report with intermediate confidence, real coverage is correlated with asset type, and real staleness depends on scan cadence and the vulnerability change rate. These would shift the absolute recall magnitudes but not the structural relationships: a blind-spot floor exists whenever any asset is uncovered, the freshness identity follows from the real-time feed supplying freshness on its own coverage, and the overlap dependence follows from the coverage accounting of Eq. (<a href="#eq:classes" data-reference-type="ref" data-reference="eq:classes">[eq:classes]</a>) and Eq. (<a href="#eq:blindspot" data-reference-type="ref" data-reference="eq:blindspot">[eq:blindspot]</a>).

*Internal validity.* Because the study is pre-registered and the evaluation seeds 1000 to 1024 were inspected only once, the reported numbers are not the product of analytic search. The model was developed on separate seeds, and no coverage, overlap, or freshness probability was tuned to clear a threshold. The evaluation script computes each verdict mechanically from the frozen data.

*External validity.* The fleet size, the coverage marginals, the overlap sweep, and the freshness probability are documented priors, not measurements from any agency, so absolute recall values such as 0.8702 should be read as illustrative of the model rather than as field estimates. The comparative gain, the freshness mechanism, the blind-spot floor, and the overlap dependence depend on the qualitative structure rather than on the specific constants, and we expect them to transfer. Calibrating coverage, overlap, and freshness against a real two-tool deployment is the natural next step.

*Statistical validity.* Intervals are BCa bootstrap intervals over 25 seeds, appropriate for the small-sample, possibly skewed statistics reported here ; we use interval non-overlap rather than significance testing throughout, avoiding the multiple-comparison pitfalls of repeated $p$-values across the hypotheses and overlap levels.

*Scope.* The model omits false positives, which a production heatmap must also manage, and treats the two feeds’ coverage as independent given the overlap parameter. Incorporating a precision dimension and correlated coverage is left to future work.

# Conclusion

Fusing a fresh-but-partial real-time feed with a broad-but-stale scheduled feed recovers current-vulnerability visibility that neither achieves alone, but the benefit is governed by the relationship between the feeds rather than by the fusion logic. In a pre-registered simulation, fusion raised detection recall from 0.7498 to 0.8702 at the reference overlap, a gain of 0.1204 ($[0.1173, 0.1232]$) above a 0.10 bar; that gain equaled exactly the scheduled feed’s unique fresh coverage (difference 0.0); the fusion miss of 0.0788 stayed above a blind-spot floor of 0.051 that no fusion can cross; and the gain fell monotonically to 0.0 as the feeds became redundant while the blind spot grew to 0.2475. The deployment guidance is concrete: fuse complementary, low-overlap feeds, predict the gain from the second feed’s unique fresh coverage, and treat the blind spot, not the fusion logic, as the binding constraint, closing it by extending coverage rather than by refining the merge. Calibrating the coverage and freshness priors against a real two-tool deployment is the next step toward turning these structural findings into field estimates.
