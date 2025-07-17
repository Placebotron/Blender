# CAD Whisperer – Vision Board

## 1. Vision Statement

Leverage hidden intelligence in CAD hierarchies to create graph‑native digital twins that super‑charge AI reasoning, search, and generative capabilities for industrial machinery.

## 2. Problem & Opportunity

* **Messy metadata**: PDFs, Excels, images, and ERP data are disconnected and unstructured.
* **Untapped CAD models**: 3‑D assemblies already encode exact part hierarchy, geometry, and relations, yet remain siloed.
* **AI gap**: LLMs, diffusion models, and analytics pipelines lack structured 3‑D context, limiting accuracy and creativity.

**Opportunity** → Translate CAD + metadata into a Graph Neural Network (GNN) representation to enable: spare‑part intelligence, richer RAG, condition‑aware generation, and better predictive models.

## 3. Target Users

* Manufacturing data‑science & ML teams
* PLM / ERP software vendors
* Maintenance & after‑sales engineers
* AI solution integrators / consultants

## 4. Value Propositions

| Feature                     | Benefit                                                                             |
| --------------------------- | ----------------------------------------------------------------------------------- |
| **CAD→GNN translator**      | Turns assemblies into machine‑readable graphs for instant querying and ML ingestion |
| **Metadata fusion layer**   | Links BOM, supplier info, docs, images to each part‑node                            |
| **Open graph schema & SDK** | Developers integrate quickly via PyG / DGL exports or REST API                      |
| **Conditioning modules**    | Feed GNN context into LLMs, diffusion, simulators                                   |

## 5. Competitive Edge

* Goes beyond point‑cloud or mesh AI by combining **geometry *and* business metadata**
* Extensible, format‑agnostic pipeline (GLB → STEP, SLDASM, IGES, …)
* Designed for **on‑prem or cloud** to meet industrial data‑security needs

## 6. Technology Stack (MVP)

* Geometry parsing: *OpenCascade*, *trimesh*
* Graph processing: *PyTorch Geometric*
* Storage: *Neo4j* or graph RDF store
* Services: Dockerised micro‑backend with WebAssembly plug‑ins for CAD viewers

## 7. 12‑Month Roadmap

| Quarter     | Milestones                                                                                 |
| ----------- | ------------------------------------------------------------------------------------------ |
| **Q3 2025** | • Spec & scope<br>• GLB parser prototype<br>• Sample dataset + graph visual demo           |
| **Q4 2025** | • Metadata ingestion layer<br>• API v0.1<br>• Pilot with 1 manufacturer                    |
| **Q1 2026** | • Support STEP & SolidWorks<br>• GNN training pipeline templates<br>• Technical docs & SDK |
| **Q2 2026** | • Generative‑AI conditioning modules<br>• SaaS beta launch<br>• Partnership outreach       |

## 8. Success Metrics

* ≥ 95 % part‑node mapping accuracy vs manual BOM
* 50 % reduction in engineer lookup time during maintenance
* 3 pilot deployments within 12 months, 1 paid contract by Q2 2026

## 9. Risks & Mitigations

| Risk                              | Mitigation                                                             |
| --------------------------------- | ---------------------------------------------------------------------- |
| Proprietary CAD format complexity | Focus on open/neutral formats first, partner with CAD vendors          |
| Data‑security concerns            | Offer on‑prem install, ISO 27001 roadmap                               |
| Change‑management in factories    | Provide low‑code plugins & training, prove ROI via pilot KPI dashboard |

## 10. Next Steps

1. Validate pain points with three target customers (interviews + survey).
2. Build parser spike (`cad_whisperer_v0.1`) and publish demo video.
3. Assemble core team (geometry engineer, graph ML engineer, product manager).
4. Design open graph schema; draft RFC for community feedback.
