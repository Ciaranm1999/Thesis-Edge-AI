# Thesis References

All references used or planned for use in the thesis. BibTeX keys match `references.bib`.

> **Verification note:** BibTeX entries in `references.bib` were constructed from titles, authors, and URLs. Before final submission, verify each entry against the actual paper using Google Scholar: find the paper → Cite → BibTeX → copy into `references.bib`.

---

## Food Waste and Strawberry Industry

### FAO2019
**Title:** The State of Food and Agriculture 2019: Moving Forward on Food Loss and Waste Reduction  
**Author:** Food and Agriculture Organization of the United Nations  
**Year:** 2019  
**Publisher:** FAO, Rome  
**URL:** https://www.fao.org/publications/sofa/2019/en/  
**Used for:** Establishing the global food waste context and scale of post-harvest losses

### FAOSTAT2024
**Title:** FAOSTAT: Crops and Livestock Products — Strawberries  
**Author:** Food and Agriculture Organization of the United Nations  
**Year:** 2024 (accessed 2025)  
**URL:** https://www.fao.org/faostat/en/#data/QCL  
**Used for:** Global strawberry production figures (>9 million tonnes/year)

---

## Mould Biology and VOC-Based Detection

### Tian2024
**Title:** A Predictive Model for the Growth Diameter of Mold under Different Temperatures and Relative Humidities in Indoor Environments  
**Authors:** Tian, Jiaqing et al.  
**Journal:** Buildings, Vol. 14, No. 1, p. 215, 2024  
**DOI:** 10.3390/buildings14010215  
**URL:** https://www.mdpi.com/2075-5309/14/1/215  
**Used for:** Supporting the 15-minute sensing interval (mould growth occurs on multi-hour timescale); temperature and humidity as mould growth predictors

### Yang2025
**Title:** Electronic Nose for Indoor Mold Detection and Identification  
**Authors:** Yang, Wei et al.  
**Journal:** Advanced Sensor Research, Wiley, 2025  
**DOI:** 10.1002/adsr.202500124  
**URL:** https://advanced.onlinelibrary.wiley.com/doi/10.1002/adsr.202500124  
**Used for:** Validating VOC sensor selection — mould produces detectable VOC signatures before visible signs appear

### Ren2023
**Title:** Accurate and Non-Destructive Monitoring of Mold Contamination in Foodstuffs Based on Whole-Cell Biosensor Array Coupling with Machine-Learning Prediction Models  
**Authors:** Ren, Xiaojin et al.  
**Journal:** Journal of Hazardous Materials, Elsevier, 2023  
**DOI:** 10.1016/j.jhazmat.2023.131200 *(verify)*  
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304389423003126  
**Used for:** ML combined with biosensors for mould prediction; supports sensor + ML approach

### DeOliveira2021
**Title:** Applications of New Technologies for Monitoring and Predicting Grains Quality Stored: Sensors, Internet of Things, and Artificial Intelligence  
**Authors:** De Oliveira Carneiro, Larissa et al.  
**Journal:** Measurement, Elsevier, 2021  
**DOI:** 10.1016/j.measurement.2021.110651 *(verify)*  
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S0263224121014810  
**Used for:** Sensor and AI integration for stored grain quality, including mould risk; establishes prior work on environmental monitoring for storage

---

## Microclimate Variability

### Lopez2017
**Title:** Wireless Sensor Networks for Greenhouse Climate and Plant Condition Assessment  
**Authors:** López Riquelme, J.A.; Soto, F.; Suardíaz, J.; Sánchez, P.; Iborra, A.; Vera, J.A.  
**Journal:** Biosystems Engineering, Vol. 153, pp. 70–81, 2017  
**DOI:** 10.1016/j.biosystemseng.2016.12.004  
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S1537511016302847  
**Used for:** Key finding: temperature differences up to 3.3°C, humidity differences up to 9% measured within the same greenhouse — the microclimate problem

#### Additional microclimate references (not yet in .bib — add if needed)
- Escamilla-Garcia et al. — IoT-Enhanced Decision Support System for Real-Time Greenhouse Microclimate Monitoring — https://www.mdpi.com/2227-7080/12/11/230
- Ma et al. — Precise quantification of microclimate heterogeneity in solar greenhouses — https://link.springer.com/article/10.1007/s12273-025-1247-5
- Romero-Gamez et al. — Microclimatic Evaluation of Five Types of Colombian Greenhouses — https://pmc.ncbi.nlm.nih.gov/articles/PMC9146035/
- Gruda et al. — Microclimate monitoring in commercial tomato greenhouse — https://www.frontiersin.org/journals/horticulture/articles/10.3389/fhort.2024.1425285/full

---

## Cold Chain Transport

### Mercier2017
**Title:** Time–Temperature Management Along the Food Cold Chain: A Review of Recent Developments  
**Authors:** Mercier, Stéphane; Villeneuve, Sébastien; Mondor, Martin; Uysal, Ismail; Brecht, Jeffrey K.; Herold, Bernhard; Fahmy, Mohamed; Ramaswamy, Hosahalli S.  
**Journal:** Comprehensive Reviews in Food Science and Food Safety, Vol. 16, No. 4, pp. 647–667, 2017  
**DOI:** 10.1111/1541-4337.12269  
**URL:** https://ift.onlinelibrary.wiley.com/doi/10.1111/1541-4337.12269  
**Used for:** Temperature variability in cold chain transport; justification for per-node model training

### Bollen2025
**Title:** Technical, Process-Related and Sustainability Requirements for IoT-Based Temperature Monitoring in Fruit and Vegetable Supply Chains  
**Authors:** Bollen, A.F. et al.  
**Journal:** Smart Agricultural Technology, Springer, 2025  
**DOI:** 10.1007/s44187-025-00427-1  
**URL:** https://link.springer.com/article/10.1007/s44187-025-00427-1  
**Used for:** Recommendation for 6+ sensors per truck; spatial variation in cold chain — supports the microclimate argument for diverse sensor node deployments

#### Additional cold chain references (not yet in .bib — add if needed)
- Zhao et al. — Cold chain transport technology for storage fruits and vegetables — https://www.sciencedirect.com/science/article/abs/pii/S2352152X22019466
- Qian et al. — Comprehensive review of cold chain logistics for fresh agricultural products — https://www.sciencedirect.com/science/article/abs/pii/S0924224421000728
- Mukherjee et al. — Ambient Parameter Monitoring in Fresh Fruit and Vegetable Supply Chains — https://pmc.ncbi.nlm.nih.gov/articles/PMC9222862/

---

## Concept Drift

### Lu2022
**Title:** From Concept Drift to Model Degradation: An Overview on Performance-Aware Drift Detectors  
**Authors:** Lu, Jie; Liu, Anjin; Dong, Fan; Gu, Feng; Gama, João; Zhang, Guangquan  
**Journal:** Knowledge-Based Systems, Vol. 245, p. 108632, 2022  
**DOI:** 10.1016/j.knosys.2022.108632  
**URL:** https://www.sciencedirect.com/science/article/pii/S0950705122002854  
**Used for:** Comprehensive survey of concept drift; establishes that IoT data distributions change over time and models degrade without adaptation

### Naeini2023
**Title:** Concept Drift Detection and Adaptation in IoT Data Stream Analytics  
**Authors:** Naeini, Mahdi et al.  
**Journal:** IEEE Access, 2023  
**DOI:** 10.1109/ACCESS.2023.3328820 *(verify)*  
**URL:** https://ieeexplore.ieee.org/document/10316080/  
**Used for:** Concept drift specifically in IoT data streams; justifies need for adaptive/incremental learning

#### Additional concept drift reference (not yet in .bib — add if needed)
- Mohamad et al. — A Lightweight Concept Drift Detection and Adaptation Framework for IoT Data Streams — https://www.researchgate.net/publication/351471737

---

## TinyML Framework Papers

### David2021 — TF Lite Micro
**Title:** TensorFlow Lite Micro: Embedded Machine Learning for TinyML Systems  
**Authors:** David, Robert; Duke, Jared; Jain, Advait et al.  
**Venue:** Proceedings of Machine Learning and Systems, Vol. 3, pp. 800–811, 2021  
**URL:** https://proceedings.mlsys.org/paper_files/paper/2021/hash/d2ddea18f00665ce8623e36bd4e3c7c5-Abstract.html  
**Used for:** Citing TF Lite Micro as the inference-only framework

### Disabato2021 — TinyOL
**Title:** Incremental On-Device Tiny Machine Learning  
**Authors:** Disabato, Simone; Roveri, Manuel  
**Venue:** ACM Workshop on Challenges in AI and ML for IoT, 2020  
**DOI:** 10.1145/3417313.3429378 *(verify — search "TinyOL" on Google Scholar for the canonical citation)*  
**Used for:** Citing TinyOL as the partial adaptation framework

### Wollert2022 — AIfES
**Title:** AIfES: A Next-Generation Edge AI Framework  
**Authors:** Wöllert, Justus; Lammert, Niklas; Viga, Reinhard; Grabmaier, Anton  
**Venue:** IEEE International Conference on Industrial Technology (ICIT) 2022  
**DOI:** 10.1109/ICIT48603.2022.10002918 *(verify)*  
**Used for:** Citing AIfES as the full on-device training framework

---

## TinyML and On-Device Training

### Dutta2022
**Title:** TinyML Meets IoT: A Comprehensive Survey  
**Authors:** Dutta, Lachit; Bharali, Swapna  
**Journal:** Internet of Things, Vol. 16, p. 100461, 2021  
**DOI:** 10.1016/j.iot.2021.100461  
**URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC9227753/ *(PMC version)*  
**Note:** Title in ML_Notes.md is "TinyML: Enabling of Inference Deep Learning Models on Ultra-Low-Power IoT Edge Devices for AI Applications" — verify exact title matches this BibTeX entry; there may be two different papers. Use PMC9227753 to find the correct citation.  
**Used for:** Comprehensive overview of TinyML capabilities and limitations on MCUs

### Imteaj2024
**Title:** Federated Learning for IoT Devices: Enhancing TinyML with On-Board Training  
**Authors:** Imteaj, Ahmed et al.  
**Journal:** Information Fusion, Elsevier, 2024  
**DOI:** 10.1016/j.inffus.2023.101980 *(verify)*  
**URL:** https://www.sciencedirect.com/science/article/pii/S1566253523005055  
**Used for:** Case for on-board training when cloud connectivity is unavailable; combines federated learning with TinyML

### Khalil2024
**Title:** TinyWolf: Efficient On-Device TinyML Training for IoT Using Enhanced Grey Wolf Optimization  
**Authors:** Khalil, Reem A. et al.  
**Journal:** Internet of Things, Elsevier, 2024  
**DOI:** 10.1016/j.iot.2024.101243 *(verify)*  
**URL:** https://www.sciencedirect.com/science/article/pii/S2542660524003068  
**Used for:** On-device training optimisation for IoT; directly addresses energy and memory constraints at the MCU tier

#### Additional on-device training reference (not yet in .bib — add if needed)
- Singh et al. — Federated learning and TinyML on IoT edge devices: Challenges, advances, and future directions — https://www.sciencedirect.com/science/article/pii/S2405959525000839

---

## Verification Checklist

Before thesis submission, verify each entry marked *(verify)*:
- [ ] Ren2023 — correct DOI
- [ ] DeOliveira2021 — correct DOI  
- [ ] Naeini2023 — correct DOI
- [ ] Imteaj2024 — correct DOI; verify this is the right Imteaj paper (there may be multiple)
- [ ] Khalil2024 — correct DOI
- [ ] Dutta2022 — verify title matches PMC9227753; BibTeX key may need updating
- [ ] FAOSTAT2024 — add specific report year and data query details
