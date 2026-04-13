# Introduction and Research Questions

Working notes for the Rationale chapter and paper framing.

---

## Paper Title

**Working title:**
> *Training at the Edge: Energy Profiling of TinyML Frameworks for Autonomous Mould Detection on Disconnected Microcontroller Nodes*

**Why this title works:**
- "Training at the Edge" signals on-device training as the central contribution
- "Energy Profiling" is specific about the method
- "Autonomous" and "Disconnected" carry the deployment justification
- "Microcontroller Nodes" scopes the hardware tier clearly

---

## The Core Narrative (the "why" — read this first)

### The problem in plain English

The world has settled on a default formula for putting AI on small devices: train the model on a powerful computer, shrink it down, load it onto the device, and let the device run predictions. This is inference-only TinyML, and it works well when two conditions hold:

1. Someone with a powerful computer trained a model that fits the deployment environment
2. There is a way to get that model onto the device (internet connection, USB, physical access)

For a mould detection system deployed on transport trucks, in remote warehouses, and in agricultural storage fields, **neither of these conditions is reliably true.**

Every deployment location has different baseline temperature, humidity, and VOC readings. A model trained on lab data does not know what "normal" looks like inside a specific refrigerated truck carrying strawberries, or a dry grain warehouse in rural Ireland in November, or an open-air field during a wet spring. A single pre-trained model will work in some places and fail silently in others — missing real mould risk or raising constant false alarms — because it was trained on an environment it has never seen.

The obvious fix is to collect data from each location, train a custom model for each node, and push updates remotely. But this requires either a cellular connection to each node or manual physical visits. For a fleet of trucks and dozens of remote storage sites, this is expensive, unreliable, and defeats the purpose of a low-cost autonomous system.

### The solution

Let each device learn for itself, on its own, from the data it actually sees, in the place it actually operates. No cloud. No PC. No internet. No maintenance visits. The device trains its own neural network using the sensor readings from its own environment. This is what AIfES makes possible on an ESP32 — full neural network training directly on a microcontroller that costs a few euros, runs on milliwatts, and fits in the palm of your hand.

### Why this matters (the "why" for the defence)

This is not a claim that on-device training is universally better than cloud training. Cloud training is faster, more powerful, and easier to manage. The argument is narrower and stronger:

> **For autonomous sensor nodes deployed in diverse, disconnected environments that change over time, on-device training is not a nice-to-have — it is the only approach that works without ongoing human intervention or infrastructure dependency.**

The thesis does not claim AIfES is better than TensorFlow. It claims that for this specific class of deployment — cheap, disconnected, diverse, long-lived — on-device training solves a problem that inference-only frameworks cannot address, and then it measures what that solution costs in energy and estimates what it means for battery life.

### Three sentences for the defence

> "A pre-trained model assumes it knows what the deployment environment looks like. For sensor nodes on transport trucks and in remote storage, every environment is different, conditions change seasonally, and there is no reliable connection to push model updates. On-device training allows each node to learn its own environment autonomously, and this thesis measures the energy cost of that autonomy."

---

## Research Questions

### Main Research Question

> What is the energy cost of full on-device neural network training compared to partial adaptation and inference-only execution on an ESP32 microcontroller, and when is that cost operationally justified for autonomous, disconnected edge deployments?

### Sub-Questions

| # | Sub-question | What it produces |
|---|---|---|
| SQ1 | What is the baseline energy consumption of the mould detection system (ESP32 + DHT22/SGP30/MQ3 sensors) during normal sensing operation? | Baseline power budget — sensors + idle MCU |
| SQ2 | How does the energy consumption of AIfES, TinyOL, and TF Lite Micro compare across training and inference phases on an ESP32? | Core measurement: mJ per training cycle, mJ per inference cycle, per framework |
| SQ3 | How does mould risk prediction accuracy compare across the three frameworks under representative environmental conditions? | ML performance: accuracy, precision, recall per framework |
| SQ4 | What is the estimated battery lifetime of an autonomous mould detection node under each framework, given the measured energy profiles and a realistic deployment duty cycle? | Practical output: hours/days of runtime per battery size per framework |

### Why SQ1 matters

Before comparing frameworks, you need to know what the system costs to run without any ML at all. If the sensors alone draw most of the power, then differences between frameworks become relatively smaller. If the sensors are cheap to run and the ML dominates, the framework choice becomes critical. SQ1 establishes this baseline and makes the rest of the analysis honest.

### Why SQ4 is the right ending question

The physical setup was not battery-powered — it was mains-connected via the PPK2 to measure total system energy consumption. SQ4 is therefore an **analytical calculation**, not a live measurement. Using the energy-per-cycle figures from SQ2 and the baseline from SQ1, combined with a realistic duty cycle, you calculate estimated battery lifetime. This is entirely valid — you do not need to drain a battery in real time. The PPK2 data gives you the numbers; the calculation gives you the real-world meaning.

Duty cycle assumption: sensing every 15 minutes (96 samples/day), AIfES retrains once every 24 hours. Pick a standard battery size (e.g. 3000mAh LiPo at 3.7V) and calculate runtime per framework.

### A note on memory

RAM and Flash usage per framework will be measured and reported as supporting data alongside SQ2. It is not a standalone research question, but it must be reported because if a framework exceeds available RAM (ESP32 has 520KB SRAM), the comparison is invalid. Memory is a feasibility constraint, not the core inquiry.

---

## Sensing Interval — 15 Minutes

The system samples sensors every 15 minutes. This is a deliberate design decision with three layers of justification:

### 1. Mould biology
Mould growth under optimal conditions (high humidity, warm temperature) takes a minimum of 24–48 hours to become visibly established. The underlying environmental changes that create mould risk — humidity rising, temperature increasing, VOC accumulation — occur over tens of minutes to hours, not seconds. A 15-minute interval provides sufficient temporal resolution to detect a deteriorating trend well before risk becomes critical.

**Literature support:** Tian et al. (2024) model mould growth diameter as a function of temperature and humidity over hour-scale timeframes, confirming that meaningful growth occurs on a multi-hour timescale.

### 2. Cold chain and storage environment dynamics
Temperature fluctuations inside refrigerated trucks are driven by compressor duty cycles and door-opening events, which typically occur on 30–60 minute timescales. Warehouse humidity changes are similarly gradual. 15-minute sampling captures these dynamics without missing significant events.

**Literature support:** Mercier et al. and Bollen et al. document temperature variation patterns in cold chain transport over similar timescales.

### 3. Energy trade-off
Sensing every 15 minutes yields 96 samples per day. Sensing every 1 minute would produce 1440 samples per day — 15 times more sensor activations — with no meaningful gain in early mould detection, given the slow biological and environmental processes involved. The 15-minute interval is the practical minimum that balances resolution against power consumption for long-term battery-powered deployment.

---

## AIfES Retraining Frequency

AIfES performs **one full training pass every 24 hours**, using the 96 samples collected during that day.

### Why daily retraining

- The environment a node needs to learn shifts on a **daily timescale** — temperature cycles, cargo changes, seasonal drift, door-opening patterns
- Daily retraining means the model is always working from a full day of local environmental context
- It produces a clean, reproducible energy measurement: energy per training event ÷ 96 inference cycles = amortised overhead per sample
- It avoids trigger-based retraining, which would require defining a "significant change" threshold — an additional research question that is outside scope

### What this means for the energy comparison

All three frameworks run inference every 15 minutes (96 times per day). AIfES additionally runs one full training pass per day. The energy difference between AIfES and TF Lite Micro over 24 hours, divided by 96, gives the per-sample cost of autonomy. This is the central finding the thesis quantifies.

---

## Project Goal

> The goal of this project is to design and evaluate a low-cost mould detection node using an ESP32 microcontroller and environmental sensors, and to determine which TinyML framework — AIfES, TinyOL, or TF Lite Micro — best balances energy consumption, prediction performance, and operational autonomy for deployment in disconnected environments where cloud connectivity and manual maintenance are not available.

---

## Requirements

### Functional Requirements

| # | Requirement |
|---|---|
| FR1 | The system shall measure temperature using a DHT22 sensor |
| FR2 | The system shall measure relative humidity using a DHT22 sensor |
| FR3 | The system shall measure total VOC levels using an SGP30 sensor |
| FR4 | The system shall measure ethanol/alcohol vapour levels using an MQ3 sensor |
| FR5 | The system shall run a neural network to classify mould risk from sensor readings |
| FR6 | The system shall operate without cloud connectivity or internet access |
| FR7 | The system shall support three TinyML frameworks: AIfES (full on-device training), TinyOL (partial adaptation), and TF Lite Micro (inference only) |
| FR8 | The system shall record energy consumption data measurable by a PPK2 power profiler |

### Non-Functional Requirements

| # | Requirement |
|---|---|
| NFR1 | The system shall run on an ESP32 microcontroller |
| NFR2 | All frameworks shall fit within ESP32 memory constraints (520KB SRAM, 4MB Flash) |
| NFR3 | Sensor sampling shall occur at 15-minute intervals |
| NFR4 | AIfES shall retrain once every 24 hours using the preceding 96 samples |
| NFR5 | The system shall be designed such that battery lifetime can be analytically estimated from measured energy profiles |
| NFR6 | The system shall use a custom PCB integrating the ESP32 and all sensors |

### Note on the physical setup

The system was powered via the PPK2 (not a battery) during testing. This was intentional — the PPK2 acts as both the power supply and the precision energy measurement instrument. Battery lifetime (SQ4) is calculated analytically from the measured data, not measured by running down a physical battery.

---

## SQ4 — Battery Lifetime: Key Findings from Energy Analysis

### Measured power figures (from PPK2, 240 MHz)

- **Idle system current: 58.1 mA at 5V = 290.5 mW**
- **TinyOL ML overhead: 0.17 mJ/day** (negligible — less than 0.01% of daily energy)
- **Powerbank sizes modelled in analysis: 5000 mAh, 10000 mAh, 20000 mAh**

### Critical issue: the MQ3 sensor

The MQ3 gas sensor draws approximately **310 mA (1032 mW)** continuously due to its resistive heater element. This makes the current design impractical for battery-only operation — the MQ3 alone consumes more power than the rest of the system combined.

### Why the MQ3 was used anyway

The MQ3 was selected based on **availability** — it was the ethanol/VOC sensor on hand for the prototype. This is an honest engineering constraint that should be acknowledged in the paper, not hidden. Testing what was available, then using the measurements to identify a better path forward, is valid and useful research.

The measured energy data makes the problem concrete: the MQ3's resistive heater is the single largest power consumer in the entire system, dwarfing both the idle ESP32 and all ML overhead. This is a finding, not a failure.

### The sensor reliability context

Sensor reliability was an issue throughout this project — across all stages, not just with the MQ3. This matters for the recommendation:

- **Removing the MQ3 entirely and relying solely on the SGP30** is one option. The energy analysis shows that SGP30 raw ethanol and MQ3 ethanol signals tracked similar trends, suggesting the SGP30 can serve as a relative ethanol indicator. No hardware change required.
- **However**, reducing the sensor suite from three independent mould indicators to two introduces risk. If the SGP30 is unreliable in a specific deployment environment, the system has lost its ethanol detection entirely. Multi-sensor redundancy is part of why the system is robust.
- **The better recommendation** is to replace the MQ3 with a lower-energy MEMS alternative (e.g. MiCS-5524: ~25–35 mA with enable pin, vs 310 mA for MQ3) that preserves dedicated ethanol sensing at a fraction of the energy cost. This is the right long-term recommendation: same sensor coverage, 10× lower energy draw.

### Recommended framing for the thesis

1. **Report measured energy figures for all three frameworks with the current hardware** — this is what was actually tested and measured.
2. **Acknowledge the MQ3 as a design constraint**, not just a limitation: it was chosen for availability, its high energy draw was quantified, and the measurement itself is the contribution.
3. **In the SQ4/discussion section**, present the analytical battery lifetime for:
   - Current design (MQ3 always-on): impractical for long-term battery operation
   - Improved design (MQ3 replaced with MEMS alternative): viable for multi-week operation
4. **Note the SGP30 raw ethanol signal as a no-hardware-change interim option**, but recommend MEMS replacement rather than sensor removal, given observed reliability variability across the project.

This turns a prototype limitation into a concrete finding: the energy cost of dedicated gas sensing is quantified, the trade-off between sensor coverage and power is made explicit, and a clear hardware recommendation follows from the data.

---

## SQ3 — Data Labelling: Camera-Based Ground Truth

### What was done

A Raspberry Pi 5 with a Camera Module 3 photographed the strawberries every hour. Visual inspection of these photographs was used to label sensor readings as mould-present or mould-absent. Mould growth was deliberately induced under controlled conditions to generate clear positive examples.

### Why this is methodologically sound

The camera was used exclusively as a **ground-truth labelling instrument** — it is not part of the deployed sensor node. This is standard supervised ML practice. You cannot validate a predictive system without knowing what actually happened, and visual inspection is the accepted ground truth for mould presence.

**The defence has two parts:**

1. **The camera establishes labels; it does not replace sensors.** In a production deployment, initial labels could come from expert assessment, deliberate calibration runs, or known conditions. The camera was the practical tool for doing this rigorously in the lab.

2. **Controlled mould induction produces clean, representative data.** Deliberately forcing moulding under known temperature and humidity conditions gives unambiguous positive examples. This is how supervised ML datasets for environmental monitoring are created. The alternative — waiting for mould to appear randomly — would introduce unknown label noise.

### The honest limitation — and why it reinforces the thesis

The model was trained on strawberry mould under controlled laboratory conditions. A sceptic at the defence could say: *"This model won't generalise to grain in a warehouse, or cheese in a cold store, or citrus in a truck. Your results are only valid for strawberries in a lab."*

This is true. And it is the entire point.

**Why the limitation is actually the argument:**

The claim is not that the lab-trained model works everywhere. The claim is that *no centrally-trained model can work everywhere*, because every deployment environment is different. Consider what a generalised model would need to know:

- What "normal" temperature and humidity looks like inside a specific refrigerated truck, running a specific compressor, carrying a specific cargo, in a specific season
- What baseline VOC levels are in a dry grain warehouse versus an open-air agricultural field
- How these baselines shift over time as cargo changes, seasons change, and the environment drifts

A model trained on aggregated lab data or cloud-sourced readings cannot learn any of this — it was trained on data from environments it has never visited. The failure mode is silent: the model continues to run, continues to output predictions, but it is effectively guessing in an environment it does not recognise.

**What the lab experiment actually proves:**

The strawberry mould experiment demonstrates one specific, important thing: the sensor system *can learn to predict mould risk when given accurate labelled training data*. That is the capability being evaluated. The question the thesis answers is not "does this model work for all food types?" but rather "can a sensor node of this type, running these frameworks, learn to detect mould in its own environment?" — and the answer, from the lab experiment, is yes.

**How this carries to deployment:**

In real deployment, each node collects its own data from its own environment. Initial labels can come from:
- A brief supervised calibration period (a human expert confirms conditions once at installation)
- Known-state conditions (new empty truck cargo bay = no mould risk = class 0; deliberate calibration run with known-mouldy sample = class 1)
- Conservative threshold-based pre-labelling from sensor readings before the model is trained

The on-device training capability (AIfES) is the mechanism that turns local sensor data into a locally-trained model, without requiring connectivity, cloud compute, or ongoing maintenance. The lab experiment proves the system is capable of this. The limitation — that it needs to retrain per environment — is not a flaw; it is a design requirement that on-device training fulfils.

**The rhetorical move for the defence:**

If challenged: *"Your model only works for strawberries in a lab."*

Answer: *"Correct — a model trained on strawberries in a lab is calibrated for that environment. That is why inference-only TinyML, which relies on a single pre-trained model, is insufficient for this use case. Each deployed node operates in a different environment, and this system is designed so that each node trains its own model on its own data. The lab experiment demonstrates that the training process works. The on-device training capability is what makes it viable to repeat that process at every deployment site, without a lab, without a camera, and without a network connection."*

---

## TODO

- [x] MQ3 treatment for SQ4: report current design energy, recommend MEMS replacement (e.g. MiCS-5524) as the right long-term fix, note SGP30 raw ethanol as an interim option. Two-scenario battery calculation: current (MQ3 always-on) vs improved (MEMS replacement).
- [ ] Draft the Rationale/Introduction chapter in LaTeX
- [ ] Abstract — leave until the end
