#import "@preview/charged-ieee:0.1.4": ieee

#let paper-title = [LabGuardian: Geometry-Constrained Pin Pose Estimation for Visual Breadboard Reconstruction]

#let paper-abstract = [
  Reconstructing a breadboard circuit from a single image is difficult because millimeter-spaced holes are visually repetitive, component terminals are frequently occluded, and small localization errors change the inferred connection.

  Conventional component detectors stop at bounding boxes, while unconstrained vision-language models may describe plausible but nonexistent topology.

  We present LabGuardian, a computer-vision pipeline that formulates terminal localization as component-conditioned top-down pose estimation. Full-frame YOLO-Pose predicts component instances and pin keypoints; a planar homography rectifies camera perspective; and a geometry-constrained snap-to-grid stage maps each keypoint to a canonical hole while retaining ambiguous candidates. The resulting visual graph supports deterministic topology verification, but electrical netlist export is treated only as a downstream consumer.

  On a held-out split, component detection reaches 0.991 mAP50 and 0.786 mAP50-95, while pin pose estimation reaches 0.947 and 0.829, respectively. INT8 deployment on an Intel Core Ultra 5 225U NPU achieves 13.37 ms mean latency, 15.61 ms P99, and 74.7 images/s. These results establish an auditable image-to-structure interface for real-time breadboard understanding.
]

#show: ieee.with(
  title: paper-title,
  authors: (
    (
      name: "Su'an Liu",
      department: [School of Electronic Engineering],
      organization: [Beijing University of Posts and Telecommunications],
      location: [Beijing, China],
    ),
    (
      name: "Xinran Zhang",
      department: [School of Electronic Engineering],
      organization: [Beijing University of Posts and Telecommunications],
      location: [Beijing, China],
    ),
    (
      name: "Jiali Ruan",
      department: [School of Electronic Engineering],
      organization: [Beijing University of Posts and Telecommunications],
      location: [Beijing, China],
    ),
  ),
  abstract: paper-abstract,
  index-terms: (
    [computer vision],
    [pose estimation],
    [keypoint localization],
    [homography],
    [geometric transformation],
    [visual circuit reconstruction],
  ),
  bibliography: bibliography("refs.bib"),
  figure-supplement: "Fig.",
)

#set text(lang: "en")
#set par(justify: true)
#show raw: set text(size: 7.1pt)
#show math.equation: set text(size: 8.7pt)
#show figure.where(kind: table): set text(size: 6.9pt)

#let stagebox(title, body, fill: rgb("#F4F4F4")) = block(
  width: 100%,
  inset: 4pt,
  radius: 2pt,
  stroke: 0.45pt + black,
  fill: fill,
  align(center)[#strong[#title] #linebreak() #text(size: 7.1pt)[#body]],
)

= Introduction

Recovering a physical circuit from an image is a fine-grained visual-structure problem. In a breadboard, holes separated by a 2.54-mm pitch are nearly indistinguishable under perspective projection, and the electrical meaning of a component depends on the exact holes occupied by its terminals. A displacement of one grid cell may therefore transform a correct visual reconstruction into an open circuit or an unintended connection. The problem is further complicated by specular component bodies, thin leads, dense jumper wires, partial occlusion, illumination change, and unconstrained camera viewpoint.

Most visual pipelines terminate at component detection. A bounding box identifies a resistor or transistor, but does not determine where each lead enters the board. Cropping a component before terminal regression appears natural, yet frequently truncates leads that extend beyond the component body and removes the surrounding grid needed for disambiguation. The appropriate representation is instead an instance-conditioned set of terminal keypoints embedded in the complete board image.

A second difficulty is geometric. Direct nearest-neighbor matching in image coordinates is not invariant to perspective and may snap a terminal to the wrong row when the camera is oblique. Conversely, purely learned image-to-topology models lack an explicit mechanism for enforcing the planar lattice, center-trench separation, component span, or pin-order constraints. Vision-language models provide flexible visual semantics #cite(<llava>), but free-form descriptions cannot guarantee that a claimed connection corresponds to an observed pixel. We refer to such unsupported structural statements as *topology hallucination*.

We therefore formulate breadboard reconstruction as a sequence of visual estimation and geometric projection operations. LabGuardian first performs component-conditioned top-down pose estimation, then rectifies the planar board with a homography, and finally applies a geometry-constrained snap-to-grid algorithm. Ambiguous mappings are preserved as ranked hypotheses rather than forced into a single hole. The output is a pin-hole observation graph whose nodes remain linked to bounding boxes, keypoints, projection distances, and candidate holes. Graph verification and optional explanation operate only after this visual representation has been fixed.

The contributions are threefold:

- We formulate terminal localization as a component-conditioned pose-estimation task that retains full-image context and associates pin hypotheses with component instances through multi-cue geometric matching.
- We introduce a homography-based spatial mapping and physically constrained snap-to-grid formulation that normalizes viewpoint, rejects infeasible assignments, and exposes residual uncertainty at the hole level.
- We evaluate both localization accuracy and heterogeneous edge inference. The pose model attains 0.947 pin mAP50 and 0.829 pin mAP50-95, while NPU INT8 inference reaches 13.37 ms mean latency and 74.7 images/s.

= Related Work

== Keypoint and Pose Estimation

Pose estimation converts an image into structured landmarks rather than a single category or bounding box. High-resolution representations such as HRNet improve spatial precision by maintaining multi-scale feature streams throughout the network #cite(<hrnet>). Top-down methods typically detect an instance and then localize its keypoints, whereas bottom-up methods detect landmarks before grouping them. YOLO-Pose integrates detection and keypoint regression in a single forward pass while preserving instance-level grouping #cite(<yolopose>). We adopt this heatmap-free family but reinterpret the pose: a rigid electronic component is the instance and its electrical terminals are the keypoints. Unlike human joints, these landmarks are small, often collinear, and constrained by package geometry and a regular receiving lattice.

== Planar Geometric Transformation

Planar calibration and projective rectification are established tools for mapping observations into a canonical coordinate system #cite(<zhangcalib>). A breadboard is particularly suitable for this treatment because its useful surface is approximately planar and contains a repeated metric grid. However, homography alone does not resolve a terminal that projects between two adjacent holes. LabGuardian therefore couples projective rectification with a discrete geometry layer that accounts for board topology, package type, pin span, collinearity, and center-trench constraints.

== Visual Circuit Understanding

SPICE and graph matching operate on an already available symbolic circuit #cite(<spice>)#cite(<vf2>); they do not recover physical connectivity from an image. Conversely, generic multimodal models can summarize visual content but do not provide a deterministic pixel-to-hole correspondence. Our scope is the missing interface between these regimes: the visual reconstruction of component terminals and their canonical board locations. Symbolic comparison is retained only as a downstream validation mechanism and is not presented as the primary contribution.

= Proposed Visual Reconstruction Framework

== Problem Formulation

Let an RGB image $I in RR^(H times W times 3)$ contain component instances $cal(C)={C_i}$. Each instance has a class $t_i$, bounding box $b_i$, and an ordered set of visible or occluded terminal keypoints $K_i={bold(p)_(i k)}$. The board model provides a canonical set of hole centers $cal(H)={bold(c)_h}$ and feasibility relations determined by the board region and component package. The objective is to estimate

$
  F: I arrow { (C_i, k, h, z_(i k)) },
$

where $h$ is the assigned physical hole and $z_(i k)$ stores confidence, projection distance, candidate rank, visibility, and ambiguity. This representation deliberately precedes electrical interpretation: it describes what the image supports, not whether the circuit is correct.

#figure(
  grid(
    columns: (1fr, auto, 1fr, auto, 1fr, auto, 1fr),
    column-gutter: 4pt,
    align: center + horizon,
    stagebox([Board Image], [Full-frame RGB observation], fill: rgb("#E9F1F8")),
    [#sym.arrow.r],
    stagebox([Pin Pose], [Component instances and ordered keypoints], fill: rgb("#E9F1F8")),
    [#sym.arrow.r],
    stagebox([Rectification], [Planar homography to canonical board], fill: rgb("#EEF5EA")),
    [#sym.arrow.r],
    stagebox([Grid Assignment], [Constrained hole hypotheses], fill: rgb("#EEF5EA")),
    grid.cell(colspan: 7)[
      #v(3pt)
      #align(center)[#text(size: 7.1pt)[Visual output: component - pin - pixel - rectified coordinate - candidate hole]]
    ],
  ),
  caption: [Computer-vision pipeline. Electrical topology verification consumes the final pin-hole graph but does not modify the visual observations.],
  placement: top,
  scope: "parent",
) <fig:pipeline>

== Component-Conditioned Top-Down Pose Estimation

The pose network processes the complete image at 960-pixel resolution. For every detected component, it regresses a bounding box, class confidence, terminal coordinates, keypoint visibility, and keypoint confidence. Full-frame inference preserves leads and the board lattice around each component. Seven directly annotated classes are considered: resistor, ceramic capacitor, electrolytic capacitor, diode, light-emitting diode, jumper wire, and three-pin transistor. Dense DIP-8 and DIP-14 terminals are generated after package detection from rigid package geometry, because direct keypoint regression becomes unstable when adjacent pins occupy only a few pixels.

Component and pin hypotheses are associated through a category-gated score. For component $i$ and pose hypothesis $j$,

$
  S_(i j) &= w_1 "IoU"(b_i,b_j)
    + w_2 exp(-norm(bold(mu)_i-bold(mu)_j)_2^2/(2 sigma_i^2)) \
  &quad + w_3 rho_(i j) + w_4 gamma_(i j) + w_5 c_j.
$ <eq:association>

where $bold(mu)$ is the box center, $rho_(i j)$ is the fraction of keypoints inside an expanded component box, $gamma_(i j)$ measures consistency between keypoint span and component extent, and $c_j$ is detection confidence. Candidate pairs with incompatible classes are removed. Remaining pairs are sorted by $S_(i j)$ and assigned greedily one to one, preventing duplicated ownership. If the best score is below the acceptance threshold, the pose remains unmatched rather than being silently attached to a neighboring component.

#figure(
  image("figures/cadx/e2e_triptych.pdf", width: 96%),
  caption: [Project-specific end-to-end reconstruction: (a) the full-frame breadboard observation, (b) component instances with terminal landmarks, and (c) the instance-linked pin representation after geometric mapping. The symbolic panel visualizes the output interface and is not used as additional visual evidence.],
  placement: top,
  scope: "parent",
) <fig:e2e>

== Homography-Based Spatial Mapping

Let $bold(p)=[x_p,y_p,1]^T$ be a terminal keypoint in image coordinates. Four board landmarks determine a nonsingular planar homography $bold(H) in RR^(3 times 3)$. The canonical coordinate $bold(q)=[u,v,1]^T$ is obtained by

$
  lambda bold(q) &= bold(H) bold(p), \
  u &= frac(h_11 x_p + h_12 y_p + h_13, h_31 x_p + h_32 y_p + h_33), \
  v &= frac(h_21 x_p + h_22 y_p + h_23, h_31 x_p + h_32 y_p + h_33).
$ <eq:homography>

Here, $lambda != 0$ is the homogeneous scale and $h_(i j)$ denotes the entry of $bold(H)$ in row $i$ and column $j$. Equation #ref(<eq:homography>) removes projective distortion before any discrete grid decision. If landmark calibration fails, a synthetic grid may be used as a flagged fallback, but its assignments are not treated as equally reliable.

#figure(
  grid(
    columns: (1fr, auto, 1fr, auto, 1fr),
    column-gutter: 5pt,
    align: center + horizon,
    stagebox([Image Plane], [$bold(p)=[x_p,y_p,1]^T$ #linebreak() perspective-distorted board], fill: rgb("#E9F1F8")),
    [#sym.arrow.r #text(size: 7pt)[$bold(H)$]],
    stagebox([Canonical Plane], [$lambda bold(q) = bold(H) bold(p)$ #linebreak() metric lattice coordinates], fill: rgb("#EEF5EA")),
    [#sym.arrow.r #text(size: 7pt)[$pi_(cal(H))$]],
    stagebox([Discrete Grid], [$h^*$ plus ranked alternatives #linebreak() feasibility-filtered mapping], fill: rgb("#FFF4DE")),
  ),
  caption: [Projective-to-discrete geometric interface. Homography removes viewpoint distortion, whereas the grid projection $pi_(cal(H))$ resolves terminal coordinates against physically valid hole centers and preserves ambiguous alternatives.],
  placement: top,
  scope: "parent",
) <fig:geometry-interface>

== Geometry-Constrained Snap-to-Grid

For valid canonical holes $cal(H)$, Euclidean nearest-neighbor assignment gives

$
  h^* &= arg min_(h in cal(H)) norm(bold(q)_(1:2)-bold(c)_h)_2, quad a = d_(h^*) / s_g, \
  "accept" &= (a <= tau) and (phi(h^*,t_p,K_i)=1).
$ <eq:snap>

where $d_(h^*)$ is the rectified snapping distance, $s_g$ is the physical grid pitch, $tau$ is a normalized threshold, $t_p$ is the pin/package type, and $phi$ is a feasibility predicate. The predicate rejects assignments that violate the board boundary, center-trench separation, axial-device span, three-pin collinearity, or package-specific ordering. Normalization by $s_g$ makes the acceptance rule independent of output resolution.

Crucially, rejection does not erase the observation. The mapper records the top candidate holes, their normalized distances, the rejected constraint, and a confidence flag. This explicit ambiguity representation prevents a subpixel localization residual from being converted into a false structural claim.

#figure(
  image("figures/cadx/ambiguity.pdf", width: 96%),
  caption: [Project-specific hole-level ambiguity case. Nearby terminal-to-hole candidates are retained and compared under rectified distance and package constraints instead of forcing the geometrically nearest assignment.],
) <fig:ambiguity>

== Visual Topology Readout

The accepted pin-hole relations are converted into a compact component-net graph by grouping holes according to the known breadboard layout and merging regions connected by detected jumpers. A depth-first traversal or an equivalent disjoint-set implementation performs this grouping. The graph can be exported to SPICE and compared with a reference by VF2, but these operations do not contribute additional visual evidence. Their role is to test whether the image-derived structure supports a downstream application. Every mismatch therefore retains pointers to the originating component, terminal keypoint, rectified coordinate, and candidate hole.

= Experimental Evaluation

== Dataset and Training Protocol

The private dataset contains real top-view breadboard photographs spanning six instructional circuit families: first-order RC, common-emitter amplifier, differential pair, and UA741 inverting, integrating, and summing amplifiers. It includes viewpoint variation, illumination variation, wire overlap, and partial occlusion. Annotations combine component boxes with up to three ordered terminal keypoints and visibility flags. Training, validation, and test splits are disjoint; the test split is excluded from optimization and model selection.

YOLOv8s-pose #cite(<yolo>) was trained for 100 epochs with 960-pixel input and batch size 8. Standard color, translation, and scale augmentation were used, and mosaic augmentation was disabled during the final ten epochs. INT8 post-training quantization used 144 calibration images and reduced the OpenVINO model from 22 MB to 11 MB.

== Geometric Evaluation Protocol

Pose AP measures whether terminal landmarks are detected around the correct component, but it does not directly measure whether a landmark is assigned to the correct physical hole. We therefore separate continuous localization from discrete reconstruction. For ground-truth image keypoint $bold(p)_(i k)^gt$, predicted keypoint $hat(bold(p))_(i k)$, and component-box diagonal $d_i$, normalized keypoint error is

$
  "NKE" = 1/N sum_(i,k) norm(hat(bold(p))_(i k)-bold(p)_(i k)^gt)_2 / d_i .
$ <eq:nke>

PCK@$alpha$ is the fraction with normalized error at most $alpha$; hole-assignment accuracy is $N^(-1) sum_(i,k) [hat(h)_(i k)=h_(i k)^gt]$ after rectification and snapping. Ambiguity-rejection precision is computed only on predictions rejected by $phi$. The current experiment log retains pose AP but not the per-keypoint predictions and hole labels required for these three geometric measures; they are specified here as mandatory submission-time additions rather than inferred from AP.

== Detection and Pin-Pose Accuracy

#figure(
  table(
    columns: (1.35fr, 0.85fr, 0.85fr, 0.9fr, 1fr),
    align: (left, center, center, center, center),
    stroke: 0.35pt,
    inset: 2.5pt,
    table.header([Prediction target], [Precision], [Recall], [mAP50], [mAP50-95]),
    [Component boxes], [0.991], [0.989], [0.991], [0.786],
    [Pin keypoints], [0.955], [0.954], [0.947], [0.829],
  ),
  caption: [Validation accuracy after 100 epochs. Pin-pose metrics evaluate the ordered terminal keypoints associated with detected component instances.],
) <tab:pose-accuracy>

As shown in #ref(<tab:pose-accuracy>), the keypoint head preserves high recall despite the small spatial support of terminals. The gap between pin mAP50 and mAP50-95 indicates that strict localization remains more difficult than coarse keypoint detection, motivating the subsequent projective normalization and ambiguity-aware snapping rather than direct pixel-space nearest-neighbor assignment.

== Heterogeneous Vision Inference

Experiments were performed on an Intel Core Ultra 5 225U system with 8 GB memory and integrated CPU, iGPU, and Intel AI Boost NPU execution paths #cite(<intel225u>). Between 60 and 1,153 serial inferences were collected for each configuration.

#figure(
  table(
    columns: (0.9fr, 0.75fr, 0.78fr, 0.88fr, 0.84fr, 0.84fr, 0.82fr),
    align: (left, center, center, center, center, center, center),
    stroke: 0.35pt,
    inset: 2.35pt,
    table.header([Device], [Prec.], [Load (s)], [Mean (ms)], [P95 (ms)], [P99 (ms)], [img/s]),
    [CPU], [FP16], [0.14], [92.44], [96.74], [98.92], [10.8],
    [CPU], [INT8], [0.24], [29.02], [30.13], [30.65], [34.5],
    [iGPU], [FP16], [0.43], [26.87], [27.32], [28.18], [37.2],
    [iGPU], [INT8], [2.85], [18.26], [19.29], [20.11], [54.7],
    [NPU], [FP16], [1.01], [16.55], [16.64], [17.67], [60.4],
    [#strong[NPU]], [#strong[INT8]], [#strong[1.20]], [#strong[13.37]], [#strong[13.75]], [#strong[15.61]], [#strong[74.7]],
  ),
  caption: [YOLOv8s-pose latency and throughput across processor units. NPU INT8 gives the lowest mean and tail latency.],
  placement: top,
  scope: "parent",
) <tab:vision-perf>

NPU INT8 reduces mean latency by 85.5% relative to CPU FP16 and improves throughput from 60.4 to 74.7 images/s relative to NPU FP16. The 15.61-ms P99 supports real-time visual interaction. As secondary deployment evidence, the matched INT8 NPU run consumed 8.53 W package power and 114.2 mJ per inference, compared with 26.37 W and 813.6 mJ on the CPU; these power measurements are not treated as a separate contribution.

== Qualitative Geometric Analysis

The examples in #ref(<fig:e2e>) and #ref(<fig:ambiguity>) expose two distinct visual failure sources. Component boxes may remain correct while terminal endpoints are partially hidden by jumpers; full-frame pose inference preserves visible lead direction, neighboring lattice structure, and long-range package context for the keypoint head. Separately, an accurately localized endpoint can still lie near a Voronoi boundary between holes after rectification. The proposed mapper makes this geometric uncertainty observable through candidate distances and explicit constraint failures.

The three scenes in #ref(<fig:pose-scenes>) further show why component detection alone is insufficient. Similar body-level confidence may coexist with substantially different terminal visibility, clutter, and foreshortening. The instance-linked pose representation exposes these differences before discrete projection, enabling low-confidence keypoints to be rejected or retained as multiple hole hypotheses instead of being converted into an overconfident structural relation.

#figure(
  grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 5pt,
    image("figures/yolo_dataset.png", width: 100%),
    image("figures/yolo_inference_chip.png", width: 100%),
    image("figures/yolo_inference_resistor.png", width: 100%),
  ),
  caption: [Representative full-frame pose outputs under (a) dense wiring, (b) partial terminal occlusion around an integrated package, and (c) sparse component placement. Instance contours and terminal landmarks remain registered to the original image.],
  placement: top,
  scope: "parent",
) <fig:pose-scenes>

== Scope of Nonvisual Modules

The deterministic visual-to-template path remains below 100 ms end to end. An optional INT4 explanation module reduces storage from 3.1 GB to 941.5 MB and peak memory to 1.36 GB while preserving the rule-based pass rate on the same 30-question set (80.0% before and after quantization). These measurements delimit deployment cost only; no generative or electrical metric is used to support the computer-vision claims.

= Discussion

The current evidence supports accurate component and terminal localization and low-latency inference, but it does not yet constitute a complete geometric benchmark. In particular, the experiment log does not contain a controlled ablation of homography, unconstrained nearest-neighbor snapping, and the full feasibility predicate, nor a statistically reported pin-to-hole assignment accuracy. Those measurements are necessary to isolate the contribution of the geometric transformation from the pose model itself. A camera-ready study should therefore report per-split image and instance counts, pixel error or PCK, hole-assignment accuracy, ambiguity-rejection precision, and performance stratified by viewpoint and occlusion.

The private dataset also limits comparison with public pose benchmarks because its keypoints represent rigid terminals rather than human joints. This difference is intrinsic to the task, but a release of annotations and board geometry would materially improve reproducibility. Finally, the symbolic verifier can reveal whether a visual reconstruction is structurally inconsistent, but it cannot retrospectively prove that every keypoint or hole assignment was correct. Visual and structural metrics must therefore remain separately reported.

= Conclusion

LabGuardian reframes breadboard understanding as a computer-vision problem centered on pin-level pose estimation and geometric transformation. Full-frame, component-conditioned keypoint prediction preserves terminal context; planar homography maps arbitrary viewpoints to a canonical board; and geometry-constrained snapping converts rectified coordinates into discrete hole hypotheses without hiding ambiguity. The resulting visual graph is auditable because every downstream relation remains linked to image evidence. Validation mAP and cross-device measurements show that the approach is both spatially accurate at the pose level and suitable for real-time NPU execution. The next priority is a controlled geometric ablation and a public pin-to-hole benchmark, which are required to quantify the contribution beyond pose estimation alone.

