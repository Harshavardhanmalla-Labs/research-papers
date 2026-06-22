# The Drill Illusion: Latent Failover-Defect Decay and the Recovery-Confidence  Gain of Continuous Chaos Testing in Hybrid Government Infrastructure

*Harshavardhan Malla, Independent Researcher*

<div class="IEEEkeywords">

disaster recovery, chaos engineering, failover, latent defects, recovery confidence, contingency planning, site reliability engineering, pre-registration, reproducibility

</div>

# Introduction

Federal systems must be able to recover after a disruption, and contingency planning prescribes the drills that are meant to demonstrate that capability . A periodic disaster-recovery drill answers a narrow question, namely whether recovery works at the moment of the drill. That narrow answer is easily mistaken for a much broader one: whether recovery would work if a real disruption struck at an arbitrary later moment. The two answers diverge, and they diverge for a structural reason. Between drills, a recovery capability accumulates latent defects. A replication link breaks, a failover script’s dependency changes underneath it, a credential expires, a routing rule is edited for a troubleshooting session and never restored. Each such defect sits undetected on the component it affects until something exercises that component again. If nothing does until the next annual drill, the component spends a large fraction of the year in a silently broken state, and a disruption arriving during that window finds a recovery path that does not work.

We call the consequence the drill illusion. A drill run immediately after a validation reports near-certain recovery, because the validation has just cleared any latent defect on the components it touched. But the probability that recovery succeeds at a random disruption time, when the struck component may not have been exercised recently, is materially lower. The gap between the two is the illusion: the amount by which a passing drill overstates the recovery capability that real incidents will actually encounter. The illusion is not a measurement error; it is a property of the cadence. The longer the interval between validations of a component, the longer that component spends in a latent-defect state, and the larger the overstatement.

Chaos engineering offers a different posture . Instead of exercising the recovery capability once a year, it injects faults continuously and automatically, re-validating the covered components every few days. A latent defect that would otherwise persist for months under an annual cadence is now caught within days, so the covered components spend almost all of their time in a healthy state and at-random recovery rises toward the at-drill figure. This is the autonomic, self-managing posture anticipated by the vision of autonomic computing  and operationalized in our own prior work on self-healing remediation for government fleets . The promise is attractive, and like all attractive promises it is easy to overstate. Two facts bound it. First, a chaos suite exercises only the components it covers; a failure mode that is never injected is never validated off-cadence and stays at the annual-drill level, so coverage sets a ceiling. Second, once chaos runs frequently enough that covered components are almost always fresh, tightening the cadence further adds little, so the benefit saturates.

This paper quantifies the benefit and its two bounds. We do not claim to measure any particular agency’s recovery posture. We build a transparent model of latent-defect decay on a fleet of recovery-relevant components, lock a set of hypotheses, thresholds, and seeds before inspecting any evaluation result, and report what the model says. Every magnitude in the paper comes from the frozen evaluation run on seeds 1200 to 1224, and every interval is a bias-corrected and accelerated (BCa) bootstrap interval. The contribution is fourfold.

- We define *at-random recovery*, the probability that recovery succeeds when a failure strikes a component not specifically rehearsed near the failure time, and separate it from *rehearsed recovery*, the near-certain figure a drill reports at the drill. The difference between these two is the drill illusion, and conflating them is the central error in optimistic disaster-recovery reporting.

- We show that continuous chaos testing raises at-random recovery from 0.6875 under annual drills to 0.9489, a gain of 0.2614 that clears the pre-registered 0.10 bar.

- We formalize a *coverage ceiling*: the recovery-confidence gain cannot exceed what perfect freshness on the covered components would provide, and we confirm the realized gain sits just below that ceiling and rises with coverage.

- We show the gain *saturates with cadence*: once the chaos cadence is tight enough that covered components are almost always fresh, further tightening adds little, which gives a direct budgeting rule, namely buy coverage rather than cadence past a point.

The methodology is deliberately conservative. Every quantitative claim is a pre-registered hypothesis evaluated on seeds that were not inspected during model development, and every interval is a BCa bootstrap interval  rather than a null-hypothesis significance test, following the pre-registration discipline now standard in empirical software engineering .

# Background and Related Work

## Chaos engineering

Chaos engineering is the practice of deliberately injecting faults into a running system to surface weaknesses before they surface as incidents . Its premise is that the only reliable way to know whether a recovery path works is to exercise it, and the only way to know whether it keeps working is to exercise it continuously. The discipline grew out of large-scale production engineering, where the gap between a system that passed a test once and a system that recovers under real conditions was learned the hard way. Our work is complementary: rather than arguing that chaos testing is good practice, we quantify how much continuous fault injection raises the probability of recovery at a random disruption time relative to a periodic drill, and we characterize the two bounds, coverage and cadence, that govern that gain.

## Contingency planning and disaster recovery

Federal contingency planning is codified in the Contingency Planning Guide for Federal Information Systems , which prescribes the recovery plans, roles, and procedures an agency must maintain, and which positions the periodic drill as the primary means of assurance. The contingency controls themselves live in the broader control catalog , and the categorization of a system, which sets how stringent its recovery requirements are, follows the security categorization standard . The traditional assurance model is point-in-time: a recovery plan is exercised on a schedule, the exercise passes, and the capability is certified until the next exercise. Our work models the decay that occurs between those exercises and shows that the certified number is not the number a real incident encounters.

## Test, training, and exercise programs

The discipline of exercising a plan is itself the subject of dedicated guidance , which catalogs the spectrum of exercises from tabletop discussions to full functional drills and frames testing as a recurring program rather than a one-time event. That guidance establishes that exercises should be periodic; it does not quantify how recovery capability decays in the interval between them, nor how the choice of interval determines the gap between the exercised result and the at-random result. We supply exactly that quantification, and we show that the interval is the dominant driver of the illusion: an annual interval produces a large overstatement, a monthly one a small one.

## Site reliability engineering

Site reliability engineering frames reliability as an engineering discipline with explicit objectives and continuous validation , and it is the practical home of continuous monitoring and continuous fault injection. The continuous-monitoring posture  reframes assurance from a periodic judgment into an ongoing process. The connection to our work is direct: continuous chaos testing is the recovery-specific instance of the continuous-validation principle, and our coverage ceiling and cadence saturation are the recovery-specific instances of the general fact that continuous validation reaches only what it instruments and saturates once it is fast enough.

## Autonomic and self-healing systems

The vision of autonomic computing  described systems that monitor, diagnose, and repair themselves without human intervention, and continuous chaos testing is a step toward that vision for the recovery path specifically: the system continuously tests its own ability to recover and surfaces defects for repair. Our prior work builds self-healing remediation for cyber-hygiene defects on government endpoint fleets , and the prioritization logic that decides which defects to chase first  is the same logic that, here, decides which components a coverage-limited chaos suite should exercise first. Breach data continues to attribute incidents to known but unaddressed weaknesses , which is the same lesson at the level of the whole fleet: a defect that is known to exist but is not exercised until it is too late is the defect that causes the outage. The shared lesson across this literature is that a capability you do not continuously exercise is a capability you do not actually have, and our contribution is to put a number on how much that matters for recovery.

# System Model

We model a single hybrid infrastructure over a fixed horizon and ask, for each assurance regime, how likely recovery is to succeed at a random disruption time. All quantities are synthetic with documented distributions; no operational, employer, or recovery-test data is used.

## A fleet of recovery-relevant components

Each seed instantiates a fleet of $M = 12$ recovery-relevant components, the failover modes that a disruption can require, such as region failover, database failover, network failover, and dependency failover. Each component $j$ carries a latent-defect hazard $\lambda_j$, the expected number of recovery-breaking defects per year. The fleet is stratified: 4 fragile components draw defects at 3 per year and 8 robust components draw defects at 0.3 per year, so that some components rot quickly and most rot slowly, as real fleets do. Latent defects arrive on component $j$ as a Poisson process at rate $\lambda_j / 365$ per day. A defect, once present, renders that component’s recovery path broken until a validation clears it.

## Drills rehearse a covered subset on a periodic interval

A drill is a periodic validation. Under the annual-drill regime, every component is validated every $T = 365$ days, and a validation clears any latent defect present on the components it exercises. Under the continuous-chaos regime, a chaos suite covers a fraction $c$ of the components, the *coverage* (reference $c = 0.70$, swept over $0.3$, $0.5$, $0.7$, $0.9$). The covered components are re-validated every chaos cadence $\delta$ (reference $\delta = 7$ days, swept over $1$, $7$, $30$, $90$ days), while the uncovered components remain on the $365$-day drill cadence. Over a multi-year horizon, each component’s healthy and defective intervals follow deterministically from its defect arrivals and its validation schedule.

## Recovery, the coverage ceiling, and the drill illusion

A disruption strikes a component chosen uniformly at random at a uniformly random time; recovery succeeds if that component is healthy at the strike time. The *at-random recovery* of a regime is the probability of success under this random strike, which equals the time-and-component-averaged fraction of components healthy, $$\label{eq:atrandom}
R_{\mathrm{rand}} \;=\; \frac{1}{M}\sum_{j=1}^{M} \frac{1}{H}\int_{0}^{H} \mathbf{1}\!\left[\,j \text{ healthy at } t\,\right]\, dt,$$ where $H$ is the horizon. The *rehearsed recovery* $R_{\mathrm{reh}}$ is the same quantity evaluated immediately after a scheduled validation, when the exercised components are fresh by construction, so $R_{\mathrm{reh}}$ is near one. The *recovery-confidence gain* of continuous chaos over annual drills is the difference in at-random recovery between the two regimes, $$\label{eq:gain}
G \;=\; R_{\mathrm{rand}}^{\,\mathrm{chaos}} - R_{\mathrm{rand}}^{\,\mathrm{annual}}.$$ Because the chaos suite re-validates only the covered fraction $c$ off-cadence, the uncovered fraction $1-c$ stays at the annual-drill level no matter how tight the chaos cadence is. The *coverage ceiling* is therefore the gain that perfect freshness on the covered components would provide; the realized gain cannot exceed it, and approaches it as $\delta \to 0$. Finally, the *drill illusion* of a regime is the amount by which its rehearsed result overstates its at-random result, $$\label{eq:illusion}
I \;=\; R_{\mathrm{reh}} - R_{\mathrm{rand}},$$ which grows with the validation interval $T$, since a longer interval lets each component spend more of its time in a latent-defect state between validations. Drills implement contingency-plan controls ; the model adds the decay accounting that the controls themselves do not specify.

# Experimental Design

The study is pre-registered. Hypotheses, thresholds, model constants, and the evaluation seed range were fixed in a dated protocol before any result on the evaluation seeds was inspected, so that no analytic choice could be steered by the outcome.

## Hypotheses

**H1 (recovery-confidence gain).** Continuous chaos testing at the reference cadence and coverage raises at-random recovery over annual-drill assurance by at least 0.10, across the evaluation seeds, with a BCa interval excluding the 0.10 bar.

**H2 (coverage ceiling).** The recovery-confidence gain is bounded by the chaos suite’s coverage and rises with it; the realized gain does not exceed the gain that perfect freshness on the covered components would provide, so the ceiling gap $R_{\mathrm{rand}}^{\,\mathrm{chaos}}$ minus the perfect-freshness value is non-positive.

**H3 (saturation with cadence).** The gain saturates as the chaos cadence tightens relative to the latent-defect arrival rate: the gains form a monotone loose-to-tight ordering, and the marginal gain of each tightening step shrinks toward zero.

**H4 (the drill illusion grows with interval).** The drill illusion, the overstatement of at-random recovery by a periodic drill, grows with the drill interval, and is materially large at the annual interval.

## Protocol and statistics

Each hypothesis is evaluated over 25 evaluation seeds (frozen range 1200 to 1224). For every quantity we report the mean and a 95% BCa bootstrap interval with 10,000 resamples ; interval non-overlap, not a $p$-value, is the evidentiary standard, which avoids the multiple-comparison pitfalls of repeated significance tests. The pre-registered failure criteria are explicit. If continuous chaos does not raise at-random recovery by at least 0.05 at the reference cadence and coverage, H1 is declared null. If the realized gain exceeds the perfect-freshness coverage ceiling, H2 is rejected. If the rehearsed recovery does not exceed the at-random recovery under annual drills, H4 is rejected. No defect rate, coverage value, or cadence value is re-tuned to reach any threshold. The model was developed on separate seeds; the evaluation seeds 1200 to 1224 were touched only once, to produce the numbers below.

# Results

Table <a href="#tab:summary" data-reference-type="ref" data-reference="tab:summary">[tab:summary]</a> collects the pre-registered quantities with their intervals; all four hypotheses are supported. We take them in turn. All numbers are means over 25 seeds with 95% BCa intervals.

<div class="tabular">

@lcc@ Quantity & Mean & 95% BCa interval 
 
At-random recovery, annual drills & 0.6875 & $[0.6797, 0.6951]$ 
At-random recovery, continuous chaos & 0.9489 & $[0.9443, 0.9533]$ 
Recovery-confidence gain (H1) & 0.2614 & $[0.2549, 0.2680]$ 
 
Coverage $0.3$ & 0.2184 & 
Coverage $0.5$ & 0.2399 & 
Coverage $0.7$ & 0.2614 & 
Coverage $0.9$ & 0.2907 & 
Coverage-ceiling gap & $-0.0098$ & $[-0.0102, -0.0094]$ 
 
Cadence $1$ day & 0.2698 & 
Cadence $7$ days & 0.2614 & 
Cadence $30$ days & 0.2313 & 
Cadence $90$ days & 0.1651 & 
 
Interval $30$ days & 0.0437 & 
Interval $90$ days & 0.1186 & 
Interval $180$ days & 0.2023 & 
Interval $365$ days & 0.3125 & $[0.3051, 0.3204]$ 

</div>

**Continuous chaos raises real recovery capability (H1).** At-random recovery under annual drills is only 0.6875 ($[0.6797, 0.6951]$): at a random disruption time, recovery succeeds barely more than two times in three, even though every component is rehearsed once a year and the rehearsal passes. Continuous chaos at the reference cadence and coverage raises at-random recovery to 0.9489 ($[0.9443, 0.9533]$), a gain of 0.2614 ($[0.2549, 0.2680]$) (Fig. <a href="#fig:conf" data-reference-type="ref" data-reference="fig:conf">1</a>). The interval lies entirely above the pre-registered 0.10 bar and far above the 0.05 failure threshold, so H1 is supported. Continuous fault injection converts a recovery capability that works two times in three into one that works better than nineteen times in twenty.

**The gain is bounded by a coverage ceiling (H2).** The recovery-confidence gain rises monotonically with chaos coverage, from 0.2184 at coverage 0.3, to 0.2399 at 0.5, to 0.2614 at the reference 0.7, to 0.2907 at coverage 0.9. The uncovered components are never re-validated off-cadence, so they stay at the annual-drill level and form a floor that limits the gain; widening coverage lifts more components off that floor. The realized gain sits just below the gain that perfect freshness on the covered components would provide, with a ceiling gap of $-0.0098$ ($[-0.0102, -0.0094]$). The gap is negative and its interval excludes zero, so the ceiling binds and is not exceeded, and H2 is supported. The small shortfall below the ceiling reflects the residual defect time that even a few-day cadence leaves on the covered components; the dominant fact is structural, that a component the chaos suite never exercises cannot be lifted off the annual floor by any cadence.

**The gain saturates as the cadence tightens (H3).** The gain rises with chaos frequency, but with sharply diminishing returns. Ordered from the loosest cadence to the tightest, the gains are 0.1651 at a 90-day cadence, 0.2313 at 30 days, 0.2614 at 7 days, and 0.2698 at 1 day, a monotone loose-to-tight ordering $[0.1651, 0.2313, 0.2614, 0.2698]$. The marginal gains of successive tightening steps are 0.0662 (from 90 to 30 days), 0.0301 (from 30 to 7 days), and 0.0084 (from 7 to 1 day): each step buys less than the one before, and the final step from a weekly to a daily cadence buys under one point. Once covered components are almost always fresh, tightening the cadence further adds little, so H3 is supported. A weekly cadence captures almost all of the benefit that an arbitrarily tight cadence would provide.

**The drill illusion grows with the interval (H4).** Rehearsed recovery is near certain immediately after a validation, while at-random recovery falls as the validation interval lengthens, so the illusion, the overstatement of at-random recovery by a periodic drill, grows with the drill interval. It is 0.0437 at a 30-day interval, 0.1186 at 90 days, 0.2023 at 180 days, and 0.3125 ($[0.3051, 0.3204]$) at the annual 365-day interval (Fig. <a href="#fig:illusion" data-reference-type="ref" data-reference="fig:illusion">2</a>). An annual drill therefore overstates true at-random recovery by about 31 points: it certifies a near-certain number while the capability a real incident encounters succeeds only about 0.6875 of the time. Shortening the interval to a month shrinks the overstatement to about four points. The rehearsed figure exceeds the at-random figure under annual drills at every interval, so the failure criterion is not met and H4 is supported.


![At-random recovery under annual drills versus continuous chaos. Annual drills leave recovery succeeding only 0.6875 of the time at a random disruption; continuous chaos raises it to 0.9489, a gain of 0.2614 that clears the pre-registered 0.10 bar.](fig1_confidence.png)



![The drill illusion, the amount by which a periodic drill overstates true at-random recovery, grows with the drill interval: from 0.0437 at 30 days to 0.3125 at the annual interval.](fig2_illusion.png)


# Theoretical Analysis

The empirical findings of the previous section are not accidents of the chosen constants. Each of them follows in closed form from a single primitive: the expected fraction of time a component spends in a latent-defect state between validations. This section derives that primitive, then derives the coverage ceiling, the cadence saturation, and the drill illusion from it, and states the match between each closed-form prediction and the frozen Monte Carlo result. The derivation makes precise the sense in which coverage, not cadence, sets the ceiling, mirroring the way a channel’s capacity, not the decoding effort, sets the limit on what any code can achieve .

## The defective-fraction primitive

Consider a single component with latent-defect hazard $\lambda$ defects per year, so defects arrive as a Poisson process at rate $\rho = \lambda/365$ per day, and let the component be validated on a periodic schedule of interval $T$ days, where each validation instantaneously clears every defect present. Fix one validation window of length $T$. Within the window, recovery is broken from the arrival of the *first* defect until the closing validation, and is healthy before that first arrival; a window with no arrival contributes no defective time. Let $U$ be the time of the first arrival measured from the window start, with density $\rho e^{-\rho u}$ on $[0, T]$ and an atom of mass $e^{-\rho T}$ at “no arrival.” The expected defective time in the window is $$\label{eq:expdef}
\mathbb{E}[\text{defective}] \;=\; \int_{0}^{T} (T-u)\,\rho e^{-\rho u}\, du \;=\; T - \frac{1 - e^{-\rho T}}{\rho}.$$ Dividing by the window length $T$ gives the expected *defective fraction* of a component with hazard $\rho$ validated every $T$ days, $$\label{eq:fdef}
\phi(\rho, T) \;=\; 1 - \frac{1 - e^{-\rho T}}{\rho T},$$ a quantity that rises monotonically from $0$ toward $1$ as the dimensionless load $\rho T$ grows. Two limits matter. For a tight cadence, $\rho T \to 0$, a Taylor expansion of <a href="#eq:fdef" data-reference-type="eqref" data-reference="eq:fdef">[eq:fdef]</a> gives $\phi(\rho, T) \approx \rho T / 2$, so the defective fraction vanishes linearly as the cadence tightens. For a loose cadence, $\rho T \to \infty$, $\phi(\rho, T) \to 1 - 1/(\rho T) \to 1$, so a high-hazard component validated rarely is broken almost all of the time.

## At-random recovery in closed form

The at-random recovery of <a href="#eq:atrandom" data-reference-type="eqref" data-reference="eq:atrandom">[eq:atrandom]</a> is the time-and-component-averaged fraction healthy, which is one minus the mean defective fraction over the fleet. With $M$ components partitioned into a fragile class (hazard $\rho_f$, count $M_f$) and a robust class (hazard $\rho_r$, count $M_r$), each class validated on its own interval, at-random recovery is $$\label{eq:rrand}
R_{\mathrm{rand}} \;=\; 1 - \frac{1}{M}\!\sum_{j=1}^{M} \phi(\rho_j, T_j),$$ which is exactly the quantity <a href="#eq:atrandom" data-reference-type="eqref" data-reference="eq:atrandom">[eq:atrandom]</a> estimates by Monte Carlo. *At-random recovery*, then, is the probability that a failure striking a component in proportion to its presence in the fleet, rather than the rehearsed subset, finds that component healthy. Under annual drills every $T_j = 365$, and with the pre-registered mixture $M_f = 4$ fragile at $\rho_f = 3/365$ and $M_r = 8$ robust at $\rho_r = 0.3/365$, <a href="#eq:rrand" data-reference-type="eqref" data-reference="eq:rrand">[eq:rrand]</a> evaluates to $R_{\mathrm{rand}}^{\,\mathrm{annual}} =
0.6815$. The frozen Monte Carlo mean is $0.6875$ ($[0.6797, 0.6951]$); the closed form lands inside the bootstrap interval, the residual reflecting the finite horizon and the random assignment of which specific components are fragile. *Match: the closed-form annual at-random recovery $0.6815$ agrees with the simulated $0.6875$.*

## The coverage ceiling (H2)

Under continuous chaos with coverage $c$, the $cM$ covered components are validated every cadence $\delta$ and the remaining $(1-c)M$ stay on the annual interval. By <a href="#eq:rrand" data-reference-type="eqref" data-reference="eq:rrand">[eq:rrand]</a>, the gain over annual drills is $$\label{eq:gain_cov}
G(c, \delta) \;=\; \frac{1}{M}\!\sum_{j \in \mathcal{C}} \big[\phi(\rho_j, 365) - \phi(\rho_j, \delta)\big],$$ where $\mathcal{C}$ is the covered set. Every term in the sum is non-negative because $\delta \le 365$ makes $\phi(\rho_j, \delta) \le \phi(\rho_j, 365)$, so widening $\mathcal{C}$ adds non-negative terms and $G$ rises monotonically with coverage. The *coverage ceiling* is the value of <a href="#eq:gain_cov" data-reference-type="eqref" data-reference="eq:gain_cov">[eq:gain_cov]</a> when the covered components are perfectly fresh, $\phi(\rho_j, \delta) \to 0$, $$\label{eq:ceiling}
G_{\mathrm{ceil}}(c) \;=\; \frac{1}{M}\!\sum_{j \in \mathcal{C}} \phi(\rho_j, 365),$$ and since $\phi(\rho_j, \delta) \ge 0$ for any finite cadence, the realized gain obeys $G(c, \delta) \le G_{\mathrm{ceil}}(c)$ with equality only in the limit $\delta \to 0$. The ceiling gap $G(c, \delta) - G_{\mathrm{ceil}}(c) = -\frac{1}{M}\sum_{j \in \mathcal{C}} \phi(\rho_j, \delta)$ is therefore non-positive by construction, and equals the small residual defective time a finite cadence leaves on the covered components. Evaluating <a href="#eq:gain_cov" data-reference-type="eqref" data-reference="eq:gain_cov">[eq:gain_cov]</a> at the reference cadence $\delta = 7$ over the coverage grid, with covered components ordered fragile-first, gives gains $0.2183$, $0.2405$, $0.2627$, $0.2960$ at coverage $0.3$, $0.5$, $0.7$, $0.9$, and a ceiling gap of $-0.0104$ at the reference coverage. *Match: the closed-form coverage gains $[0.2183, 0.2405,
0.2627, 0.2960]$ reproduce the simulated rising sequence $[0.2184, 0.2399, 0.2614, 0.2907]$, and the closed-form ceiling gap $-0.0104$ reproduces the simulated $-0.0098$, both negative.* The ceiling is a structural bound: a component the chaos suite never covers contributes nothing to <a href="#eq:gain_cov" data-reference-type="eqref" data-reference="eq:gain_cov">[eq:gain_cov]</a> no matter how small $\delta$ is, exactly as a source symbol outside the codebook contributes nothing to a channel’s realized rate .

## Saturation with cadence (H3)

Fix coverage at the reference $c = 0.7$ and vary the cadence. By <a href="#eq:gain_cov" data-reference-type="eqref" data-reference="eq:gain_cov">[eq:gain_cov]</a> the only cadence-dependent term is $\phi(\rho_j, \delta)$ on the covered components, and the tight-cadence expansion $\phi(\rho_j, \delta) \approx \rho_j \delta / 2$ shows that this residual defective time shrinks *linearly* as $\delta$ falls. Once $\delta$ is small enough that $\rho_j \delta \ll 1$ for every covered component, $\phi(\rho_j, \delta)$ is already near zero and the gain is already near the ceiling <a href="#eq:ceiling" data-reference-type="eqref" data-reference="eq:ceiling">[eq:ceiling]</a>, so any further tightening can recover only the vanishing remainder. The marginal gain of a tightening step is therefore the difference of two already-small residuals and shrinks toward zero. Evaluating <a href="#eq:gain_cov" data-reference-type="eqref" data-reference="eq:gain_cov">[eq:gain_cov]</a> from the loosest to the tightest cadence gives gains $0.1633$, $0.2311$, $0.2627$, $0.2716$ at $\delta = 90, 30, 7, 1$ days, with marginal gains $0.0678$, $0.0316$, $0.0089$ across successive tightening steps. *Match: the closed-form cadence gains $[0.1633, 0.2311, 0.2627, 0.2716]$ reproduce the simulated monotone sequence $[0.1651, 0.2313,
0.2614, 0.2698]$, and the closed-form marginal gains $[0.0678, 0.0316, 0.0089]$ reproduce the simulated diminishing sequence $[0.0662, 0.0301, 0.0084]$, each step buying less than the one before.* The saturation is thus a direct consequence of the linear vanishing of $\phi$ near $\delta = 0$: once a component is exercised within its decay window, further exercise removes a residual that is already near zero and adds essentially nothing.

## The drill illusion grows with the interval (H4)

Define the *drill illusion* as rehearsed recovery minus at-random recovery, $I = R_{\mathrm{reh}}
- R_{\mathrm{rand}}$. A rehearsal evaluated immediately after a validation finds every exercised component fresh, so $R_{\mathrm{reh}} = 1$, and by <a href="#eq:rrand" data-reference-type="eqref" data-reference="eq:rrand">[eq:rrand]</a> with a common interval $T$ across all components, $$\label{eq:illgrows}
I(T) \;=\; 1 - R_{\mathrm{rand}}(T) \;=\; \frac{1}{M}\!\sum_{j=1}^{M} \phi(\rho_j, T).$$ Since $\phi(\rho_j, T)$ is increasing in $T$ for every $j$, the illusion $I(T)$ is increasing in the drill interval: a longer interval leaves more components past their readiness decay, so the rehearsed figure overstates the at-random figure by more. Evaluating <a href="#eq:illgrows" data-reference-type="eqref" data-reference="eq:illgrows">[eq:illgrows]</a> over the interval grid gives illusions $0.0461$, $0.1218$, $0.2063$, $0.3185$ at intervals $30$, $90$, $180$, $365$ days, with the annual illusion at $0.3185$. *Match: the closed-form illusion sequence $[0.0461, 0.1218,
0.2063, 0.3185]$ reproduces the simulated growing sequence $[0.0437, 0.1186, 0.2023, 0.3125]$, and the closed-form annual illusion $0.3185$ reproduces the simulated annual illusion $0.3125$.* The illusion is therefore not a measurement artifact but a deterministic function of the validation interval through the same primitive <a href="#eq:fdef" data-reference-type="eqref" data-reference="eq:fdef">[eq:fdef]</a> that governs the gain: the very interval that makes a drill cheap to schedule is the interval that makes its passing result optimistic.

# Robustness and Sensitivity

This section reports the full sweeps behind the headline numbers in booktabs form and then states the adversarial regime that the drill illusion exposes. Every value in the three tables is taken directly from the frozen results file; no value is recomputed or smoothed.

## Coverage sweep

Table <a href="#tab:cov_sweep" data-reference-type="ref" data-reference="tab:cov_sweep">1</a> reports the recovery-confidence gain as chaos coverage widens at the reference cadence. The gain rises monotonically because each newly covered component contributes a non-negative term to <a href="#eq:gain_cov" data-reference-type="eqref" data-reference="eq:gain_cov">[eq:gain_cov]</a>; the closed-form prediction of Section <a href="#sec:theory" data-reference-type="ref" data-reference="sec:theory">6</a> is shown alongside the simulated mean, and the two agree to within the residual of the finite-horizon Monte Carlo.

<div id="tab:cov_sweep">

| Coverage $c$ | Gain (simulated) | Gain (closed form) |
|:-------------|:----------------:|:------------------:|
| $0.3$ | 0.2184 | 0.2183 |
| $0.5$ | 0.2399 | 0.2405 |
| $0.7$ | 0.2614 | 0.2627 |
| $0.9$ | 0.2907 | 0.2960 |

Coverage sweep at the reference cadence ($\delta = 7$ days): recovery-confidence gain rises with coverage. Simulated means over 25 seeds; closed form from <a href="#eq:gain_cov" data-reference-type="eqref" data-reference="eq:gain_cov">[eq:gain_cov]</a>.

</div>

## Cadence sweep

Table <a href="#tab:cad_sweep" data-reference-type="ref" data-reference="tab:cad_sweep">2</a> reports the gain and its marginal increments as the chaos cadence tightens at the reference coverage. The marginal gain falls toward zero, the saturation predicted by the linear vanishing of $\phi$ near $\delta = 0$ in Section <a href="#sec:theory" data-reference-type="ref" data-reference="sec:theory">6</a>.

<div id="tab:cad_sweep">

| Cadence $\delta$ (days) | Gain | Marginal gain |
|:------------------------|:------:|:-------------:|
| $90$ | 0.1651 | |
| $30$ | 0.2313 | 0.0662 |
| $7$ | 0.2614 | 0.0301 |
| $1$ | 0.2698 | 0.0084 |

Cadence sweep at the reference coverage ($c = 0.7$), ordered loose to tight: the gain saturates and the marginal gain shrinks. Simulated means over 25 seeds.

</div>

## Drill-interval sweep

Table <a href="#tab:int_sweep" data-reference-type="ref" data-reference="tab:int_sweep">3</a> reports the drill illusion as the validation interval lengthens. The illusion grows monotonically and reaches $0.3125$ at the annual interval, the overstatement an annual drill produces.

<div id="tab:int_sweep">

| Drill interval (days) | Illusion | 95% BCa interval |
|:----------------------|:--------:|:------------------:|
| $30$ | 0.0437 | |
| $90$ | 0.1186 | |
| $180$ | 0.2023 | |
| $365$ | 0.3125 | $[0.3051, 0.3204]$ |

Drill-interval sweep: the drill illusion (rehearsed recovery minus at-random recovery) grows with the interval. Simulated means over 25 seeds; the annual value carries a 95% BCa interval.

</div>

## The at-random adversary

The three sweeps share an adversarial reading that sharpens the practical stakes. A real incident is not a rehearsal: it does not wait for the drill, and it does not strike the specific component the drill just exercised. It strikes a component in proportion to that component’s presence in the fleet, at a moment chosen without regard to the validation schedule. This is precisely the at-random adversary that <a href="#eq:rrand" data-reference-type="eqref" data-reference="eq:rrand">[eq:rrand]</a> models, and it is the regime in which the annual drill certifies most optimistically. The drill reports $R_{\mathrm{reh}} = 1$ because it inspects a freshly validated component, but the at-random adversary lands on a component that may be deep in its latent-defect window, where the success probability is only $0.6875$ under annual drills. The illusion of $0.3125$ is the exact size of the gap the adversary exploits: an annual drill certifies recovery against the one component it just rehearsed while leaving the fleet, on average, $31$ points more fragile against a failure that strikes anywhere else. Continuous chaos covers exactly this regime, because it re-validates components in proportion to their hazard rather than rehearsing a fixed subset once a year, and the coverage ceiling <a href="#eq:ceiling" data-reference-type="eqref" data-reference="eq:ceiling">[eq:ceiling]</a> states the limit of that defense: the at-random adversary retains its full advantage on any component the chaos suite never exercises. The robustness conclusion is therefore directional and conservative: against an adversary that strikes at random, the annual drill is optimistic by construction, continuous chaos closes most of the gap, and what it cannot close is set by coverage rather than by cadence.

# Discussion

The two ways of reporting recovery point in different directions, and conflating them is the error this study is designed to puncture. A drill measures the system at its single best moment, immediately after a validation, when the exercised components are fresh by construction, and reports a near-certain result. But the quantity that a real incident turns on is at-random recovery, the probability that recovery works when a failure strikes a component that was not specifically rehearsed near the failure time, and that quantity is only 0.6875 under annual drills. An annual drill therefore certifies a number that real incidents do not honor: it overstates true at-random recovery by 0.3125, about 31 points. Recovery readiness should be reported as the at-random recovery probability, not the rehearsed result, and a recovery program that reports only its drill outcomes is reporting its single best moment as if it were typical.

Continuous random fault injection earns its keep. By re-validating the covered components every few days, it raises at-random recovery from 0.6875 to 0.9489, a gain of 0.2614, and it does so by attacking exactly the mechanism behind the illusion: it shortens the interval over which each covered component can sit in a silently broken state. But it earns its keep only up to a point, because the gain saturates as the cadence tightens. The marginal gain falls from 0.0662 for the first tightening step to 0.0084 for the last, so a weekly cadence captures almost all of the benefit and a daily one adds under a point. Spending to tighten an already-tight cadence buys very little.

The actionable consequence is to size investment to coverage, not to cadence, past a point. The gain rises steadily with coverage, from 0.2184 at coverage 0.3 to 0.2907 at coverage 0.9, because every component the chaos suite does not exercise stays pinned to the annual-drill floor regardless of how fast the covered components are validated. So once the cadence is tight enough that covered components are almost always fresh, the next dollar should buy coverage of an as-yet-unexercised failure mode, not a tighter cadence on the modes already covered. Concretely: get the cadence to roughly weekly, then stop tightening and start widening, prioritizing the fragile components whose high defect rate makes them the largest contributors to the at-random shortfall.

# Threats to Validity

*Construct validity.* The model abstracts latent-defect arrival as a Poisson process and a validation as an instantaneous clearing of all defects on the exercised components. Real defects may be bursty, correlated across components (a single bad change can break several recovery paths at once), or seasonal around change windows, and a real validation may be partial. These would shift the absolute recovery probabilities but not the structural relationships: a coverage ceiling exists whenever any component is left uncovered, the illusion grows with any interval over which decay accumulates, and saturation follows once the cadence is short relative to the defect rate.

*Internal validity.* Because the study is pre-registered and the evaluation seeds were inspected only once, the reported numbers are not the product of analytic search. The model was developed on separate seeds, and no defect rate, coverage value, or cadence value was tuned to clear a threshold. The mechanical evaluation script computes each verdict from the frozen data with no hand-set value.

*External validity.* The component count, the defect-rate mixture, the coverage values, and the cadence values are documented priors, not measurements from any agency, so the absolute magnitudes (0.6875 at-random recovery, the 0.3125 annual illusion) should be read as illustrative of the model rather than as field estimates. The comparative findings, the gain, the coverage ceiling, the cadence saturation, and the growth of the illusion with interval, depend on the qualitative structure of the model rather than on the specific constants, and we expect them to transfer. A real chaos experiment also carries operational risk that this model does not charge; calibrating the defect and coverage distributions against a real recovery-test record, and accounting for that risk, is the natural next step.

*Statistical validity.* Intervals are BCa bootstrap intervals over 25 seeds, appropriate for the small-sample, possibly skewed statistics reported here; we use interval non-overlap rather than significance testing throughout .

# Conclusion

A passing annual disaster-recovery drill measures recovery at its single best moment and hides the decay that accumulates between drills, so it overstates the recovery capability that real incidents encounter. In a pre-registered simulation, at-random recovery under annual drills was only 0.6875, while the annual drill overstated it by 0.3125, about 31 points. Continuous chaos testing closed most of that gap, raising at-random recovery to 0.9489, a gain of 0.2614 that cleared the pre-registered bar. The gain was bounded by a coverage ceiling, rising from 0.2184 at coverage 0.3 to 0.2907 at coverage 0.9 and staying just below the perfect-freshness ceiling, and it saturated as the cadence tightened, with the final step from weekly to daily buying under one point. The guidance that follows is concrete: report recovery as the at-random probability rather than the drill outcome, run continuous fault injection at roughly a weekly cadence, and then size further investment to coverage rather than to cadence, widening the chaos suite to the fragile components that dominate the at-random shortfall. Calibrating the model against a real recovery-test record is the next step toward turning these structural findings into field estimates.
