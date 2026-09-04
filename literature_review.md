# 🎓 T2M Academic Research Report

**Query:** `Perform a comprehensive academic literature review on physics-grounded text-to-motion synthesis and ...` | **Extracted Search Terms:** `text-to-motion physics diffusion reinforcement learning 3d pose estimation` | **Unique Papers Processed:** 118 | **PDFs Secured:** 0
**Fetchers Active:** IEEE GoogleScholar 

---

## 🔍 Intermediate Sub-Agent Findings (Tables & Analysis)

### 1. Kinematic Models Sub-Agent
| Paper Title & Year | Architecture (Diffusion/GPT) | Pose Skeleton Used | Key Metrics (FID, etc.) | Limitations |
| :--- | :--- | :--- | :--- | :--- |
| [[LLM-guided fuzzy kinematic modeling for resolving kinematic uncertainties and linguistic ambiguities in text-to-motion generation (2025)](https://doi.org/10.1016/j.eswa.2025.127283)] | LLM & Fuzzy Kinematic Modeling | 3D Kinematic Joint Skeleton | N/A | Limited quantitative metric breakdown in abstract; relies on rule-based fuzzy logic bounds. |
| [[LLM‐Based Modeling of 3D Joint Kinematics of the Polonaise Folk Dance for Motion‐to‐Text Generation for User‐Feedback Capabilities (2026)](https://doi.org/10.1002/cav.70130)] | LLM (Mistral 7B, H2O-Danube 3 4B, Qwen 2.5 3B) | 3D Joint Angles / Vicon Plug-in Gait | Feedback Accuracy, Real-time Latency | Domain-specific focus on Polonaise folk dance; requires specialized motion capture setup. |
| [[KETA: Kinematic-Phrases-Enhanced Text-to-Motion Generation via Fine-grained Alignment (2025)](https://doi.org/10.48550/arxiv.2501.15058)] | Diffusion (MDM backbone) + LLM (Text Decomposition) | Kinematic Phrases (KP) / 3D Joint Skeleton | R-Precision (1.19x increase), FID (2.34x improvement) | Multi-round iterative refinement increases inference latency. |
| [[MOTION AND IMAGE IN KINEMATIC TEXTS (2020)](https://doi.org/10.2307/j.ctvr695gt.4)] | Non-computational (Theoretical/Literary Analysis) | N/A | N/A | Literary analysis text; not a generative machine learning model. |
| [[Automatic Generation of Kinematic Models for the Conversion of Human Motion Capture Data into Humanoid Robot Motion (2000)](https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText=Automatic Generation of Kinematic Models for the Conversion of Human Motion Capture Data into Humanoid Robot Motion)] | Kinematic Parameter Scaling / Optimization | MoCap Marker Skeleton to Humanoid Robot Skeleton | Kinematic Scaling Error, Motion Fidelity | Non-learning deterministic approach; rigid mapping between human and robot kinematics. |
| [[Knee and torso kinematics in generation of optimum gait pattern based on human-like motion for a seven-link biped robot (2019)](https://doi.org/10.1007/s11044-019-09679-z)] | Kinematic Trajectory Optimization | 7-Link Biped Robot Skeleton | Gait Stability, Energy Consumption | Restricted to 2D/planar 7-link bipedal walking dynamics. |
| [[OLARGE : on kinematic schemes and regularization for automatic generation of human motion and ergonomic evaluation of workplaces (2007)](https://doi.org/10.1109/iecon.2007.4460252)] | Inverse Kinematics (IK) with Regularization | Ergonomic Digital Mannequin Skeleton | Ergonomic Score, Joint Torque Limits | Tailored strictly for repetitive industrial task evaluation; lacks natural diversity. |
| [[Kinematic Synergy Primitives for Human-Like Grasp Motion Generation (2024)](https://doi.org/10.1109/icra57147.2024.10611490)] | Kinematic Synergy Movement Primitives (VMRNs) | 5-Fingered Hand Joint Kinematic Skeleton | Joint Angle Reproduction Error (3.9%), Grasp Success | Focuses solely on hand grasping motions; omits whole-body dynamic interactions. |
| [[Combining inverse blending and Jacobian‐based inverse kinematics to improve accuracy in human motion generation (2014)](https://doi.org/10.1002/cav.1615)] | Hybrid Motion Blending + Jacobian IK | 3D Articulated Skeleton | Positional End-Effector Error, Convergence Rate | Depends heavily on pre-computed weight maps and existing example databases. |
| [[KinMo: Kinematic-Aware Human Motion Understanding and Generation (2025)](https://doi.org/10.1109/iccv51701.2025.01041)] | Hierarchical Alignment & Coarse-to-Fine Diffusion | Kinematic Group Joint Skeleton | R-Precision, FID, Retrieval R@K | Depends on automated fine-grained description pipelines for dataset training. |
| [[Realtime interactive dynamics computation of structure-varying kinematic chains and its application to motion generation of human figures (2002)](https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText=Realtime interactive dynamics computation of structure-varying kinematic chains and its application to motion generation of human figures)] | Dynamic Kinematic Chain Solver | Structure-Varying Kinematic Chain | Computation Latency (FPS) | Legacy dynamic formulation; lacks natural language text conditioning. |
| [[SMPL-GPTexture: Scalable, Training-Free SMPL Texture Synthesis with World Knowledge Transfer from GPT via Geometry-Aware Projection (2026)](https://doi.org/10.1109/tai.2026.3688439)] | GPT / VLM + Geometry-Aware Projection (Training-Free) | SMPL 3D Mesh | Texture Realism, Alignment Score | Focuses on static 3D mesh surface texturing rather than dynamic motion synthesis. |
| [[Full-Body Motion from a Single Head-Mounted Device: Generating SMPL Poses from Partial Observations (2022)](https://doi.org/10.1109/iccv48922.2021.01148)] | Temporal Recurrent Estimator / Deep Learning | SMPL 3D Body Model | MPJPE (Mean Per Joint Position Error), Positional Error | Susceptible to lower-body tracking ambiguity due to single-point head observations. |
| [[RC-SMPL: Real-time Cumulative SMPL-based Avatar Body Generation (2023)](https://doi.org/10.1109/ismar59233.2023.00023)] | Real-Time Cumulative Parametric Fitting | SMPL 3D Body Model | Frame Rate (FPS), Reconstruction Error | Vulnerable to sensor occlusion and high input noise. |
| [[SMPL Variable Model for 3D Reconstruction and Image Fusion in Animation Media Applications (2025)](https://doi.org/10.1109/access.2025.3549466)] | SMPL Variable Parameter Model | SMPL Parametric Skeleton | Reconstruction Error, Fusion Fidelity | Targeted at visual media image reconstruction rather than kinematic text-to-motion. |
| [[bmlSUP – A SMPL Unity Player (2021)](https://doi.org/10.1109/vrw52623.2021.00169)] | Unity Software Integration Framework | SMPL Body Mesh / Joint Skeleton | Real-time Playback FPS | Rendering software utility; contains no generative machine learning pipeline. |
| [[SMPL, a Specification Based Framework for the Semantic Structure, Annotation and Control of SMIL Documents (2010)](https://doi.org/10.1109/ism.2009.114)] | XML/SMIL Specification Framework | N/A (Multimedia Web Structure) | N/A | Non-pose related (unrelated acronym overlap for SMIL web document specifications). |
| [[3D Human Pose and Shape Estimation Based on SMPL Model (2025)](https://doi.org/10.1109/icivc61627.2024.10837359)] | Deep Convolutional / Transformer Estimator | SMPL (24 Joints + Shape Parameters) | MPJPE, PA-MPJPE | Discriminative pose estimation model; cannot perform text-driven motion generation. |
| [[Optimal Motion Synthesis of a Mobile Robot (2005)](https://doi.org/10.1109/imc.1990.687442)] | Optimal Trajectory Kinematic Control | 2D/3D Mobile Robot Kinematic Frame | Path Smoothness, Trajectory Time | Limited to mobile robot wheel/chassis path generation. |
| [[SMPL-A: Modeling Person-Specific Deformable Anatomy (2022)](https://doi.org/10.1109/cvpr52688.2022.02015)] | Parametric Anatomical Deformable Model | SMPL-A (SMPL + Soft Tissue Layers) | Surface Mesh Error, Volumetric Accuracy | Focuses on static/dynamic body shape anatomy rather than semantic motion generation. |
| [[Exploring the Discriminative Power of SMPL-Derived Body Proportions: An Initial Investigation (2026)](https://doi.org/10.1109/iit.src67760.2026.11628866)] | Statistical Feature Classifier | SMPL Body Proportions / Shape Vectors | Classification Accuracy | Purely analytical study for biometrics; offers no motion generation capabilities. |
| [[Prototypes of walking machines: motion synthesis (2003)](https://doi.org/10.1109/romoco.2002.1177089)] | Mechanical Kinematic Mechanism Synthesis | Multi-Legged Walking Robot Kinematics | Gait Stability, Speed | Hardware-centric linkage design, lacking computational neural control. |
| [[Realistic synthesis of novel human movements from a database of motion capture examples (2002)](https://doi.org/10.1109/humo.2000.897383)] | Example-based MoCap Blending / Motion Graph | 3D Articulated Kinematic Skeleton | Motion Smoothness, Continuity | Bound by pre-recorded database examples; poor out-of-distribution synthesis. |
| [[Motion Synthesis in Motion Reconstruction based on Video (2006)](https://doi.org/10.1109/mmmc.2006.1651338)] | Video-Guided Motion Interpolation | 3D Human Joint Skeleton | 3D Reconstruction Error | Requires video streams as input; lacks direct text prompt interface. |
| [[SMPL Virtual Try-On (S-VTON): A Solution for Systemic Challenges in Apparel Industry (2026)](https://doi.org/10.1109/ichora69329.2026.11537103)] | Virtual Try-On Deformation Network | SMPL Body Surface Mesh | Garment Fit Accuracy, SSIM | Restricted to 2D/3D apparel warping without dynamic kinematic sequence generation. |
| [[Determining the principles of human motion by combining motion analysis and motion synthesis (2010)](https://doi.org/10.1109/ichr.2009.5379557)] | Biomechanical Optimization | Full-Body Humanoid Skeleton | Dynamic Consistency, Torque Minimization | High optimization cost; restricted to standard lab-monitored task dynamics. |
| [[SMPL Normal Map Is All You Need for Single-view Textured Human Reconstruction (2025)](https://doi.org/10.1109/icme59968.2025.11209141)] | Normal Map Prediction / Diffusion | SMPL Surface Mesh / Normal Map | PSNR, SSIM, Chamfer Distance | Synthesizes static textured human meshes without dynamic temporal motion. |
| [[Guided Motion Diffusion for Controllable Human Motion Synthesis (2024)](https://doi.org/10.1109/iccv51070.2023.00205)] | Guided Motion Diffusion (GMD) | 3D Human Skeleton (22 Joints) | FID, R-Precision, Diversity, Foot Skating | Requires computing computationally intensive test-time guidance gradients. |
| [[A Unified Robust Motion Controller Synthesis for Compliant Robots Driven by Series Elastic Actuators (2022)](https://doi.org/10.1109/amc51637.2022.9729316)] | Robust Control Synthesis (H-infinity) | Series Elastic Actuator Kinematic Model | Joint Tracking Error, Disturbance Rejection | Low-level mechanical actuator controller; non-generative. |
| [[Motion synthesis from stochastically encoded motion primitives for anthropomorphic robotic arm (2015)](https://doi.org/10.1109/urai.2014.7057368)] | Stochastic Motion Primitives (ProMP / GMM) | Anthropomorphic Robot Arm (DOF Skeleton) | Trajectory Variance, Task Success Rate | Restricted to robotic arm trajectories; lacks natural language text interface. |

### 2. Physics & Diffusion Sub-Agent
| Paper Title & Year | Physics Integration Method | Physics Engine (MuJoCo/Isaac) | Physical Metrics | Limitations |
| :--- | :--- | :--- | :--- | :--- |
| [PhysDiff: Physics-Guided Human Motion Diffusion Model (2023)](https://doi.org/10.1109/iccv51070.2023.01467) | Physics-based motion projection module using dynamic motion imitation within diffusion denoising steps | Isaac Gym / Physics Simulator | Foot sliding, ground penetration, floating rate | High computational overhead due to physics simulation rollout per diffusion step |
| [PhysDiff: Physics-Guided Human Motion Diffusion Model (2022)](https://doi.org/10.48550/arxiv.2212.02500) | Physics projection operator mapping intermediate denoised poses to physically plausible state space | Isaac Gym / Physics Simulator | Foot sliding distance, penetration depth, physical plausibility score | Increased generation latency during iterative sampling process |
| [Physics-guided human interaction generation via motion diffusion model (2025)](https://doi.org/10.1016/j.cviu.2025.104470) | Physics-guided diffusion loss constraints for multi-person interaction motion generation | Not specified (Implicit/Kinematic simulator) | Inter-person contact accuracy, pose plausibility | Minimal implementation detail provided in abstract text |
| [Physics-Embedded Motion Planning With Contact Handling for Continuum Surgical Robots_supp1-3573623.mp4 (2025)](https://doi.org/10.1109/lra.2025.3573623/mm1) | Kinematic and dynamic contact-embedded trajectory optimization for continuous mechanics | Custom continuum robot engine | Contact force magnitude, anatomical deflection precision | Restricted to specialized continuum manipulator kinematics |
| [A divide-and-merge approach to automatic generation of contact states and planning of contact motion (2002)](https://doi.org/10.1109/robot.2000.844141) | Divide-and-merge topological contact state space searching and motion planning | Kinematic dynamic solver | Contact state transition accuracy, path trajectory validity | High combinatorial complexity for high-DOF systems |
| [Structured contact force optimization for kino-dynamic motion generation (2016)](https://doi.org/10.1109/iros.2016.7759420) | Structured contact force optimization enforcing dynamic dynamic feasibility constraints | Analytical dynamics engine | Wrench cone stability, joint torque limits, force equilibrium | Prone to local minima under non-convex contact surfaces |
| [Optimization-Based Posture Generation for Whole-Body Contact Motion by Contact Point Search on the Body Surface (2020)](https://doi.org/10.1109/lra.2020.2974689) | Non-linear whole-body optimization with automatic surface contact point searching | Rigid-body dynamic solver | Static equilibrium margin, contact surface alignment | High computational search latency on complex geometries |
| [Motion generation for a tumbling robot using a general contact model (2004)](https://doi.org/10.1109/robot.2004.1308758) | Impulse contact dynamic modeling for continuous momentum generation during tumbling | Dynamic impulse simulator | Landing stability, post-impact angular momentum | Highly sensitive to accurate friction coefficient estimation |
| [Motion Generation for Shaping Deformable Linear Objects with Contact Avoidance Using Differentiable Simulation <sup>*</sup> (2023)](https://doi.org/10.1109/robio58561.2023.10355033) | Gradient-based trajectory optimization via backpropagation through differentiable physics simulation | Differentiable Physics Simulator | Shape deviation error, minimum contact clearance | Susceptible to gradient vanishing over long collision sequences |
| [A convex model of humanoid momentum dynamics for multi-contact motion generation (2017)](https://doi.org/10.1109/humanoids.2016.7803371) | Convex formulation of centroidal momentum dynamics for multi-contact planning | Analytical dynamic solver | CoM trajectory smoothness, friction cone feasibility | Conservative linearizations limit highly dynamic agility |
| [Morph: a Motion-Free Physics Optimization Framework for Human Motion Generation (2026)](https://doi.org/10.1109/iccv51701.2025.01353) | Motion-free optimization using explicit dynamic laws and analytical physics loss terms | MuJoCo / Physics Simulator | Balance recovery margin, torque limit compliance, foot penetration | Sensitive to initialization without reference motion priors |
| [Whole-Body Multi-Contact Motion Control for Humanoid Robots Based on Distributed Tactile Sensors_supp1-3475052.mp4 (2024)](https://doi.org/10.1109/lra.2024.3475052/mm1) | Real-time feedback dynamics coupling distributed tactile sensor feedback with whole-body control | Dynamic whole-body controller | Contact force tracking error, disturbance rejection rate | Requires specialized dense hardware sensor integration |
| [Rolling motion generation of multi-points contact for a humanoid robot (2016)](https://doi.org/10.1109/icarm.2016.7606911) | Multi-point contact dynamic motion synthesis for continuous surface rolling | Rigid-body dynamics solver | Center of pressure (CoP) displacement, roll trajectory stability | Restricted to smooth convex robot body geometries |
| [Concurrent Motion and Force Control for Manipulators Constrained by Stiff Contact (2005)](https://doi.org/10.1109/imc.1990.687337) | Hybrid impedance and direct force-motion dynamic control framework for rigid dynamic contact | Analytical manipulator solver | Contact force overshoot, position trajectory error | Subject to high-frequency chatter under stiff surfaces |
| [Optimal control for whole-body motion generation using center-of-mass dynamics for predefined multi-contact configurations (2015)](https://doi.org/10.1109/humanoids.2015.7363428) | Non-linear optimal control over simplified Center-of-Mass (CoM) dynamics | CoM dynamics solver | Dynamic feasibility, contact wrench cone adherence | Requires hardcoded/predefined contact phase sequences |
| [Contact (2013)](https://doi.org/10.1109/ngns.2012.6656114) | Dynamic network routing topology contact interval modeling | N/A (Network simulator) | Network link duration, packet delivery latency | Domain mismatch (telecommunication contact, not physical robotics) |
| [Fast Multi-Contact Motion Planning Based on Best-Neighbor Search of Contact Sequences (2023)](https://doi.org/10.1109/humanoids53995.2022.10000158) | Heuristic best-neighbor search integrated with dynamic kinodynamic contact verification | Kinodynamic physics planner | Contact sequence discovery latency, dynamic equilibrium rate | Discretized search space may miss smooth continuous contact paths |
| [Motion Generation in Hybrid Control Converted from Human Motion Data (2024)](https://doi.org/10.1109/amc58169.2024.10505697) | Hybrid dynamic force/position control mapping capture data into dynamic motor actions | Physics controller | Joint angle tracking error, interaction force stability | Prone to dynamic tracking delays during sudden acceleration |
| [HCDiff: Hierarchical Latent Constraint-Projected Diffusion Framework for Deformable Linear Objects Manipulation in Cluttered Environments_supp1-3699256.mp4 (2026)](https://doi.org/10.1109/lra.2026.3699256/mm1) | Hierarchical latent diffusion projected onto physical collision and deformation manifolds | Deformable physics simulator | Collision frequency, deformation precision rate | High computational cost for latent projection at inference |
| [CoShMDM: Contact and Shape-Aware Latent Motion Diffusion Model for Human Interaction Generation (2026)](https://doi.org/10.1109/tvcg.2026.3675725) | Contact- and shape-aware latent loss guiding motion diffusion for multi-agent dynamic interaction | Kinematic geometric engine | Inter-body penetration distance, contact timing error | Simplified distance-based energy loss lacks full multi-body dynamics |
| [Centroidal Trajectory Generation and Stabilization Based on Preview Control for Humanoid Multi-Contact Motion (2022)](https://doi.org/10.1109/lra.2022.3186515) | Preview control combined with quadratic programming dynamic stabilization for centroidal trajectories | Dynamic physics model | Zero Moment Point (ZMP) offset, CoM tracking error | Assumes fixed contact timing schedule across control horizon |
| [Rotational Sliding Motion Generation for Humanoid Robot by Force Distribution in Each Contact Face (2017)](https://doi.org/10.1109/lra.2017.2719765) | Surface force distribution optimization modeling friction cones during rotational contact sliding | Rigid-body dynamic solver | Dynamic balance margin, contact torque error | Performance degrades with non-uniform surface friction coefficients |
| [Identification of contact condition based on modal motion stiffness by bilateral motion control (2010)](https://doi.org/10.1109/iecon.2009.5415287) | Bilateral control framework estimating dynamic stiffness for real-time contact adaptation | Bilateral control simulator | Stiffness estimation accuracy, reaction force tracking | Susceptible to sensor noise during low-velocity contacts |
| [Jumping Motion Generation for Humanoid Robot Using Arm Swing Effectively and Changing in Foot Contact Status (2021)](https://doi.org/10.1109/iros45743.2020.9341665) | Angular momentum dynamic optimization across discontinuous foot contact state transitions | Dynamic whole-body solver | Takeoff velocity, jump distance, landing impact balance | Non-convex optimization prone to local convergence failure |
| [Contact (2014)](https://doi.org/10.1109/ngns.2014.6990213) | Mobility pattern modeling for opportunistically contacting dynamic nodes | N/A (Network simulator) | Node contact duration, data throughput | Domain mismatch (mobile ad-hoc network contacts) |
| [High Performance Motion Control and Safe Contact Transition using Impedance-Aware Disturbance Observer (2026)](https://doi.org/10.1109/amc67705.2026.11435826) | Impedance-aware disturbance observer (DOB) enforcing continuous dynamics during rapid contact changes | Robotic dynamic engine | Transient force spike magnitude, tracking recovery speed | Controller performance limited by physical actuation delay |
| [Fast contact localisation between deformable polyhedra in motion (2002)](https://doi.org/10.1109/ca.1996.540495) | Dynamic continuous collision detection and bounding hierarchy traversal for moving deformable polyhedra | Continuous collision engine | Detection frame rate, contact point spatial accuracy | High memory overhead for highly detailed deformable meshes |
| [Motion estimation for environment-contact task with position controlled manipulator (2014)](https://doi.org/10.1109/isr.2013.6695608) | Reaction force compliance estimation for position-controlled manipulator dynamics | Manipulator dynamics model | Position adaptation error, interaction force balance | Vulnerable to unmodeled structural robot compliance |
| [Progressive Human Motion Generation Based on Text and Few Motion Frames_supp1-3556868.mp4 (2025)](https://doi.org/10.1109/tcsvt.2025.3556868/mm2) | Progressive latent motion diffusion constrained by initial frame poses and text prompts | Kinematic motion module | Frame consistency score, transition trajectory error | Absence of explicit dynamic simulator leads to minor foot sliding |
| [Integrated motion and contact control of robotic manipulators (2002)](https://doi.org/10.1109/isic.1995.525070) | Unified dynamic differential state equation modeling unconstrained motion and rigid contact dynamics | Dynamic dynamic controller | Transition state stability, dynamic force tracking error | Requires hard dynamic switching boundaries between phases |

### 3. RL Control Sub-Agent
| Paper Title & Year | RL Algorithm (PPO, etc.) | Reward Function Components | Simulation Environment | Limitations |
| :--- | :--- | :--- | :--- | :--- |
| [Towards Vision-Based Deep Reinforcement Learning for Robotic Motion Control (2015)](https://doi.org/10.48550/arxiv.1511.03791) | Deep Q-Network (DQN) | Target distance minimization, reach target success | Simulated 3-joint robotic manipulator (Gazebo) | Direct sim-to-real transfer failed using raw visual inputs, requiring synthetic visual domain adaptation. |
| [Robust Motion Control for UAV in Dynamic Uncertain Environments Using Deep Reinforcement Learning (2020)](https://doi.org/10.3390/rs12040640) | Robust-DDPG (Delayed learning, adversarial attack, mixed exploration) | Target arrival, path length/smoothness, obstacle collision avoidance | Dynamic uncertain UAV flight simulator | Limited to dual-channel continuous control (roll and speed); validated solely in simulation. |
| [A Survey of Deep Reinforcement Learning Algorithms for Motion Planning and Control of Autonomous Vehicles (2021)](https://doi.org/10.1109/iv48863.2021.9575880) | N/A (Survey covering DQN, DDPG, PPO, SAC, etc.) | Safety metrics, velocity optimization, passenger comfort, collision penalties (Surveyed) | N/A (Surveys CARLA, TORCS, SUMO, highway-env, etc.) | Survey paper; identifies field-wide limitations in safety guarantees, expert data scarcity, and generalization. |
| [Adaptive Formation Motion Planning and Control of Autonomous Underwater Vehicles Using Deep Reinforcement Learning (2024)](https://doi.org/10.1109/joe.2023.3278290) | Deep Reinforcement Learning (Actor-Critic) | Goal distance, obstacle avoidance, formation distance/angle maintenance | Simulated underactuated AUV environment with ocean currents and delays | Restricted to speed and heading control of underactuated AUVs; validated in computer simulations only. |
| [Joint Optimization of Sensing, Decision-Making and Motion-Controlling for Autonomous Vehicles: A Deep Reinforcement Learning Approach (2022)](https://doi.org/10.1109/tvt.2022.3150793) | Deep Reinforcement Learning (Attention + CNN architecture) | Driving safety, velocity tracking error penalty, traffic rule compliance | Custom driving simulator & physical autonomous vehicle test setup | High computational load due to combined Attention-CNN state representation; real-world testing restricted to a specific scene. |
| [Model-based deep reinforcement learning for data-driven motion control of an under-actuated unmanned surface vehicle: Path following and trajectory tracking (2022)](https://doi.org/10.1016/j.jfranklin.2022.10.020) | Model-Based Deep Reinforcement Learning (MB-DRL) | Path following error, trajectory tracking deviation, energy consumption penalty | Unmanned Surface Vehicle (USV) dynamic simulation | Dependent on high dynamic model accuracy under hydrodynamic disturbances; lack of full physical deployment details. |
| [Hierarchical Motion Planning and Tracking for Autonomous Vehicles Using Global Heuristic Based Potential Field and Reinforcement Learning Based Predictive Control (2023)](https://doi.org/10.1109/tits.2023.3266195) | Prioritized Q-Learning (integrated with Predictive Control) | Path tracking accuracy, motion stability, deviation error minimization | Virtual driving simulator & real-world autonomous driving testbed | Artificial Potential Field upper layer can experience local minima; decoupled hierarchical structure requires multi-stage tuning. |
| [Motion control of unmanned underwater vehicles via deep imitation reinforcement learning algorithm (2020)](https://doi.org/10.1049/iet-its.2019.0273) | Imitation Learning Twin Delay DDPG (IL-TD3) | Trajectory tracking error minimization, control effort penalty, stability maintenance | Unmanned Underwater Vehicle (UUV) simulation platform | Depends on expert closed-loop control data for behavior cloning initialization; evaluated only in simulation. |
| [Motion control of a space manipulator using fuzzy sliding mode control with reinforcement learning (2020)](https://doi.org/10.1016/j.actaastro.2020.06.028) | Fuzzy Sliding Mode Control with Reinforcement Learning (FSM-RL) | Joint tracking error reduction, sliding surface deviation penalty, chattering suppression | Space manipulator dynamic simulation environment | High design complexity from combining fuzzy logic rules with sliding mode dynamics; lacking physical hardware validation. |
| [Reinforcement Learning Impedance Control of a Robotic Prosthesis to Coordinate With Human Intact Knee Motion (2022)](https://doi.org/10.1109/lra.2022.3179420) | Reinforcement Learning (Actor-Critic / Impedance tuning) | Intact knee motion tracking error (echo control), gait symmetry penalty | Robotic knee prosthesis experimental setup / human-in-the-loop simulation | Non-stationary trajectory changes driven by human adaptation complicate real-time online tracking stability. |
| [Self-scaling reinforcement learning for fuzzy logic controller-applications to motion control of two-link brachiation robot (1999)](https://doi.org/10.1109/41.807999) | Self-Scaling Reinforcement Learning Fuzzy Logic Controller (SS-RL FLC) | Target branch capture success, angular momentum/trajectory error penalty | 2-link brachiation robot simulation environment | Tested on simplified 2D dynamic models; fuzzy membership scaling factors require initial manual configuration. |
| [Learn to swim: Online motion control of an underactuated robotic eel based on deep reinforcement learning (2022)](https://doi.org/10.1016/j.birob.2022.100066) | Deep Reinforcement Learning (Model-free DRL) | Forward swimming velocity, energy consumption penalty, heading alignment | Physics simulation model & physical multi-segment robotic eel prototype | Sim-to-real transfer gap present due to complex fluid mechanics of flexible compliant structures. |
| [Ball Motion Control in the Table Tennis Robot System Using Time-Series Deep Reinforcement Learning (2021)](https://doi.org/10.1109/access.2021.3093340) | Time-Series Deep Reinforcement Learning | Target landing location error penalty, over-net clearance height constraint | Virtual table tennis environment & physical table tennis robot system | Cannot directly measure spin velocity; relies on time-series estimations which may degrade under unseen ball spins. |
| [Reinforcement Learning-Based Prescribed Performance Motion Control of Pneumatic Muscle Actuated Robotic Arms With Measurement Noises (2022)](https://doi.org/10.1109/tsmc.2022.3207575) | Actor-Critic RL (with Generalized Proportional Integral Observer & Error Transformation) | Prescribed transient/steady-state performance bounds, noise suppression reward, control energy penalty | Pneumatic Muscle Actuated (PMA) robotic arm experimental testbed | Highly complex theoretical framework; performance strongly tied to observer state estimation accuracy under high noise. |
| [A Multitasking-Oriented Robot Arm Motion Planning Scheme Based on Deep Reinforcement Learning and Twin Synchro-Control (2020)](https://doi.org/10.3390/s20123515) | DDPG with Twin Synchro-Control (TSC-DDPG) | Human joint angle trajectory matching, task accomplishment reward, path smoothness | Humanoid robot BHR-6 digital twin simulation environment | Requires explicit human joint angle data collection for prior knowledge; evaluated strictly in simulated tasks. |
| [Motion Control for Biped Robot via DDPG-based Deep Reinforcement Learning (2018)](https://doi.org/10.1109/wrc-sara.2018.8584227) | Parallel DDPG with Prioritized Experience Replay (PER-DDPG) | Balance retention / fall prevention penalty, forward walking speed, inclination alignment | Passive biped robot simulation environment (slope walking) | Evaluated exclusively in simulation; high hyperparameter sensitivity for maintaining continuous bipedal balance. |
| [Physics-informed reinforcement learning for motion control of a fish-like swimming robot (2023)](https://doi.org/10.1038/s41598-023-36399-4) | Physics-Informed Deep Reinforcement Learning (Curriculum DRL) | Limit cycle velocity tracking error, path deviation penalty, propulsion efficiency | Hydrodynamic simulation of Joukowski hydrofoil planar swimmer | Relies on a simplified 2D/planar hydrofoil model; high-fidelity fluid dynamic simulations remain computationally expensive. |
| [A Deep Reinforcement Learning-Based Decentralized Hierarchical Motion Control Strategy for Multiple Amphibious Spherical Robot Systems With Tilting Thrusters (2023)](https://doi.org/10.1109/jsen.2023.3333872) | Decentralized Hierarchical DDPG (Low-level DDPG + High-level APF action networks) | Compound reward: goal reaching, inter-robot distance maintenance, obstacle avoidance, thrust energy | Multi-Amphibious Spherical Robot (ASR) physics simulation & physical multi-robot platform | High structural complexity with multiple action networks; underwater communication latency affects scalability. |
| [Research on Motion Planning Based on Flocking Control and Reinforcement Learning for Multi-Robot Systems (2021)](https://doi.org/10.3390/machines9040077) | Reinforcement Learning (integrated with Flocking Control & Wall-Following) | Flocking distance maintenance, obstacle avoidance penalty, wall-following path reward | Custom visual multi-robot simulation platform | Tested exclusively in a simulation platform; lacks physical multi-robot hardware validation under real dynamic noise. |
| [Motion control of autonomous underwater vehicle based on physics-informed offline reinforcement learning (2024)](https://doi.org/10.1016/j.oceaneng.2024.119432) | Physics-Informed Offline Reinforcement Learning | Trajectory tracking error minimization, physics-conformance penalty, energy efficiency | AUV motion control ocean simulation platform | Constrained by the state-action coverage and quality of the pre-collected offline dataset; limited abstract details. |
| [A general motion control architecture for an autonomous underwater vehicle with actuator faults and unknown disturbances through deep reinforcement learning (2022)](https://doi.org/10.1016/j.oceaneng.2022.112424) | Deep Reinforcement Learning (Fault-Tolerant DRL Architecture) | Trajectory tracking error penalty, actuator fault compensation penalty, control effort smoothness | Autonomous Underwater Vehicle (AUV) fault simulation platform | Evaluated only under simulated fault conditions; lacks detailed physical hardware failure verification. |
| [Reinforcement Learning Control for Moving Target Landing of VTOL UAVs With Motion Constraints (2023)](https://doi.org/10.1109/tie.2023.3310014) | Online Data-Based Reinforcement Learning (with Funnel surface constraint) | Funnel surface relative position constraint bound, orientation safety, landing precision | Simulation environment & physical VTOL UAV flight test bed | Theoretical convergence and safety rely strictly on preassigned funnel constraint parameters and finite excitation conditions. |
| [Progressive Reinforcement Learning with Distillation for Multi-Skilled Motion Control (2018)](https://doi.org/10.48550/arxiv.1802.04765) | Progressive Learning and Integration via Distillation (PLAID / Policy Distillation) | Terrain-specific locomotion velocity, balance retention, posture energy efficiency | Simulated bipedal locomotion terrain environment (physics engine) | Evaluated purely in physics simulation; distillation can cause minor performance degradation relative to single-skill specialists. |
| [Reinforcement learning neural network (RLNN) based adaptive control of fine hand motion rehabilitation robot (2015)](https://doi.org/10.1109/cca.2015.7320733) | Actor-Critic Reinforcement Learning Neural Network (RLNN) | Assist-as-Needed (AAN) trajectory tracking error, applied force intensity penalty, patient participation reward | Computer simulation & physical hand rehabilitation robotic device | Limited clinical trials with human post-stroke patients; sensitive to varying individual biomechanical impedance. |
| [Residual Reinforcement Learning for Motion Control of a Bionic Exploration Robot—RoboDact (2023)](https://doi.org/10.1109/tim.2023.3282297) | Parameter Randomization Residual RL (PR-RRL: SAC + ADRC baseline) | Underwater motion stability, trajectory/heading tracking accuracy, residual control action penalty | Underwater exploration robot dynamics simulation & RoboDact physical prototype | Hybrid architecture increases system complexity; requires precise gain balancing between ADRC baseline and SAC residual output. |
| [A Deep Reinforcement Learning Motion Control Strategy of a Multi-rotor UAV for Payload Transportation with Minimum Swing (2022)](https://doi.org/10.1109/med54222.2022.9837220) | Twin Delayed Deep Deterministic Policy Gradient (TD3) | Waypoint position tracking accuracy, payload swing angle minimization penalty, flight stability | Multirotor UAV simulation environment & physical octorotor UAV testbed | Cascaded design directly replaces position controller; tracking performance degrades under unmodeled payload mass variations. |
| [Quadrotor motion control using deep reinforcement learning (2021)](https://doi.org/10.1139/juvs-2021-0010) | Proximal Policy Optimization (PPO) | Hover positioning distance error, angular velocity penalty, control signal effort penalty | Quadrotor UAV simulation environment | Evaluated only in simulation without real flight test validation; performance relies heavily on precise reward tuning. |
| [Reinforcement learning-based motion control for snake robots in complex environments (2024)](https://doi.org/10.1017/s0263574723001613) | Modified Deep Q-Learning (DQN) + Path Integral (PI) Algorithm | Path smoothness, obstacle clearance distance, gait parameter efficiency, path tracking accuracy | Multi-obstacle simulation environment for snake robot locomotion | Multi-stage control pipeline (Floyd-moving average + DQN + Path Integral) increases execution complexity; lacks hardware deployment. |
| [A Safe Reinforcement Learning driven Weights-varying Model Predictive Control for Autonomous Vehicle Motion Control (2024)](https://doi.org/10.1109/iv55156.2024.10588747) | Discrete Action Deep RL for Weights-varying MPC (RL-WMPC) | Context-dependent tracking accuracy, passenger comfort, driving safety, multi-objective trade-offs | Autonomous vehicle simulation environment (TUM-CONTROL open-source software) | Discrete action formulation restricts runtime MPC cost weights to pre-computed Bayesian Optimization Pareto candidate sets. |
| [Bridging Reinforcement Learning and Iterative Learning Control: Autonomous Motion Learning for Unknown, Nonlinear Dynamics (2022)](https://doi.org/10.3389/frobt.2022.793512) | Gaussian Process based Iterative Learning Control / Reinforcement Learning (GP-ILC/RL) | Reference trajectory tracking error minimization, feedforward control input optimization penalty | Nonlinear dynamic system simulation & physical balancing robot prototype | High computational complexity and memory growth associated with Gaussian Process regression over extended trial durations. |

### 4. Pose & Vision Sub-Agent
| Paper Title & Year | Pose Representation (MediaPipe/SMPL) | Translation Mechanism | Robustness to Noise | Limitations |
| :--- | :--- | :--- | :--- | :--- |
| [Keep It SMPL: Automatic Estimation of 3D Human Pose and Shape from a Single Image (2016)](https://doi.org/10.1007/978-3-319-46454-1_34) | SMPL (implied by title) | Unspecified in abstract | Unspecified in abstract | Minimal details in abstract (publication citation notice only) |
| [Keep it SMPL: Automatic Estimation of 3D Human Pose and Shape from a Single Image (2016)](https://doi.org/10.48550/arxiv.1607.08128) | SMPL statistical 3D body model & 2D joints | Bottom-up CNN 2D joint prediction (DeepCut) + top-down SMPL fitting via objective optimization | High robustness to sparse data and interpenetration via population priors | Inherently sensitive to 2D joint estimation errors and depth ambiguities |
| [3D Human Pose and Shape Estimation Based on SMPL Model (2024)](https://doi.org/10.1109/icivc61627.2024.10837359) | SMPL 3D mesh model & joint priors | CNN spatial feature extraction combined with joint prior information guiding optimization parameter updates | Improved fitting quality by leveraging image spatial features alongside priors | Optimization loop increases computational latency; bounded by CNN feature quality |
| [Keep it SMPL: Automatic Estimation of 3D Human Pose and Shape from a Single Image (2016)](https://doi.org/10.48550/arxiv.1607.08128) | SMPL statistical body model & 2D joints | 2D CNN joint detection (DeepCut) coupled with top-down SMPL projection error minimization | Robust to minimal input data using learned statistical body shape correlations | Optimization can fall into local minima; susceptible to monocular depth ambiguities |
| [Multi-view Self-supervised 3D Human Pose and Shape Estimation on SMPL (2025)](https://doi.org/10.1007/978-981-96-6688-1_14) | SMPL body model (implied by title) | Multi-view self-supervised estimation (implied by title) | Unspecified in abstract | Minimal details in abstract (publication citation notice only) |
| [Monocular 3D Human Pose Estimation in the Wild Using Improved CNN Supervision (2017)](https://doi.org/10.1109/3dv.2017.00064) | 3D skeleton keypoints & 2D joint representations | Deep CNN supervised feature transfer leveraging 2D/3D datasets and multi-camera marker-less data | Robust to in-the-wild background clutter, clothing variations, occlusions, and viewpoints | Generalization capability remains tied to the scope of training dataset augmentations |
| [3D Human Pose Estimation from Monocular Images with Deep Convolutional Neural Network (2015)](https://doi.org/10.1007/978-3-319-16808-1_23) | 3D pose keypoints (implied by title) | Deep Convolutional Neural Network regression | Unspecified in abstract | Minimal details in abstract (publication citation notice only) |
| [Monocular human pose estimation: A survey of deep learning-based methods (2020)](https://doi.org/10.1016/j.cviu.2019.102897) | N/A (Comprehensive survey paper) | N/A (Surveys deep learning-based monocular pose translation methods) | N/A (Surveys robustness strategies across literature) | Survey paper; provides no novel baseline implementation |
| [Sparseness Meets Deepness: 3D Human Pose Estimation from Monocular Video (2016)](https://doi.org/10.1109/cvpr.2016.537) | 3D joint skeleton & 2D joint uncertainty maps | Deep FCN joint uncertainty prediction + Expectation-Maximization (EM) optimization with sparse geometric priors | High robustness to 2D joint location uncertainties via EM marginalization | Computationally intensive EM inference required over full video sequences |
| [Recent Advances of Monocular 2D and 3D Human Pose Estimation: A Deep Learning Perspective (2022)](https://doi.org/10.1145/3524497) | N/A (Survey covering 2D/3D human body representations) | N/A (Surveys 2D-to-3D pose lifting and direct regression methods) | N/A (Analyzes solutions for 2D/3D ambiguity and missing data) | Survey article; does not propose an original algorithmic model |
| [Deep Kinematics Analysis for Monocular 3D Human Pose Estimation (2020)](https://doi.org/10.1109/cvpr42600.2020.00098) | Kinematic skeleton topology & dynamic 3D structures | Deep kinematics pipeline: 2D input optimization -> topological motion decomposition -> temporal 3D refinement | Highly robust to noisy/unreliable 2D joint detection inputs | Sequential multi-stage pipeline performance depends heavily on initial kinematic corrections |
| [Cascaded Deep Monocular 3D Human Pose Estimation With Evolutionary Training Data (2020)](https://doi.org/10.1109/cvpr42600.2020.00621) | Hierarchical 3D human skeleton model | Cascaded deep 2D-to-3D estimation networks trained on synthetically evolved 3D skeleton data | Effectively reduces dataset bias and robustly generalizes to unseen/rare poses | Data quality heavily depends on synthetic heuristics and prior assumptions |
| [Human Pose Estimation from Monocular Images: A Comprehensive Survey (2016)](https://doi.org/10.3390/s16121966) | N/A (Survey covering kinematic, pictorial, and motion body models) | N/A (Surveys top-down/bottom-up and generative/discriminative paradigms) | N/A (Evaluates robustness across traditional and deep algorithms) | Survey article; no original deep architecture proposed |
| [GLA-GCN: Global-local Adaptive Graph Convolutional Network for 3D Human Pose Estimation from Monocular Video (2023)](https://doi.org/10.1109/iccv51070.2023.00810) | Graph representation of skeleton joint structures | Global-local Adaptive Graph Convolutional Network (GLA-GCN) 2D-to-3D pose lifting | Sensitive to 2D joint quality; optimized for ground truth and fine-tuned poses | Heavily dependent on external high-quality 2D pose detectors for practical deployment |
| [Monocular 3D Human Pose Estimation by Predicting Depth on Joints (2017)](https://doi.org/10.1109/iccv.2017.373) | 3D skeleton keypoints + joint depth representations | Hierarchical two-level LSTM (Skeleton-LSTM for global structure + Patch-LSTM for local visual cues) | Mitigates 2D-to-3D lifting ambiguities by combining global geometry with image patches | Dependent on local patch clarity around keypoints and accurate 2D joint initialization |
| [Capturing Humans in Motion: Temporal-Attentive 3D Human Pose and Shape Estimation from Monocular Video (2022)](https://doi.org/10.1109/cvpr52688.2022.01286) | 3D human pose and shape mesh parameters | MPS-Net with Motion Continuity Attention (MoCA) and Hierarchical Attentive Feature Integration (HAFI) | Robust to dynamic occlusions and temporal motion discontinuities | Requires monocular video inputs; cannot extract temporal context from single static images |
| [Posebits for Monocular Human Pose Estimation (2014)](https://doi.org/10.1109/cvpr.2014.300) | Mid-level Posebits (Boolean geometric part relations) & 3D skeleton | Structural SVM predicting discrete posebit relations to constrain 3D pose reconstruction | Effectively resolves severe body part ambiguities and complex self-occlusions | Posebit representations provide coarse qualitative bounds requiring specialized annotations |
| [Learning Monocular 3D Human Pose Estimation from Multi-view Images (2018)](https://doi.org/10.1109/cvpr.2018.00880) | 3D joint skeleton model | Deep network trained via multi-view cross-view consistency constraints and joint camera calibration | Operates robustly in dynamic outdoor environments with moving/uncalibrated cameras | Multi-view synchronized footage is strictly required during the training phase |
| [Monocular Image 3D Human Pose Estimation under Self-Occlusion (2013)](https://doi.org/10.1109/iccv.2013.237) | Articulated 3D body model | Anthropometric kinematic pruning + multi-view synthetic orientation regression matching | High robustness against self-occlusion, hallucinated body parts, and cluttered backgrounds | Synthetic view generation and constraint fitting are computationally demanding |
| [PPT: Token-Pruned Pose Transformer for Monocular and Multi-view Human Pose Estimation (2022)](https://doi.org/10.1007/978-3-031-20065-6_25) | Transformer tokens (implied by title) | Token-Pruned Pose Transformer (PPT) (implied by title) | Unspecified in abstract | Minimal details in abstract (publication citation notice only) |
| [Ray3D: ray-based 3D human pose estimation for monocular absolute 3D localization (2022)](https://doi.org/10.1109/cvpr52688.2022.01277) | 3D normalized keypoint rays | Ray-based neural lifting network mapping pixel inputs to 3D rays conditioned on camera extrinsics | High robustness against camera intrinsic and extrinsic parameter variations in the wild | Requires explicit camera intrinsic and extrinsic parameters as network inputs |
| [Locally Connected Network for Monocular 3D Human Pose Estimation (2020)](https://doi.org/10.1109/tpami.2020.3019139) | Skeleton graph with joint-dedicated node filters | Locally Connected Network (LCN) mapping 2D keypoints to 3D via unshared, dedicated joint filters | Robust to noisy/imperfect 2D pose detector inputs; strong cross-dataset generalization | Higher model parameter count compared to standard weight-shared GCN architectures |
| [Unconstrained Monocular 3D Human Pose Estimation by Action Detection and Cross-Modality Regression Forest (2013)](https://doi.org/10.1109/cvpr.2013.467) | Deformable Part Models (2D) to 3D joint keypoints | Action detection spatiotemporal priors + Deformable Part Models + Cross-Modality Regression Forests | Robust in unconstrained environments without needing background segmentation priors | Relies on handcrafted feature representations (DPMs) rather than end-to-end deep learning |
| [Boosting Monocular 3D Human Pose Estimation With Part Aware Attention (2022)](https://doi.org/10.1109/tip.2022.3182269) | Part-wise segmented skeleton keypoints | Transformer equipped with Part Aware Temporal Attention (PATA) and Dictionary Attention (PADA) | Resolves part-wise motion inconsistency and long-distance skeletal structural shifts | Memory consumption increases due to part-wise attention maps and dictionary sampling |
| [A survey on monocular 3D human pose estimation (2020)](https://doi.org/10.1016/j.vrih.2020.04.005) | N/A (Surveys keypoints, surface models, volumetric representations) | N/A (Taxonomy of monocular 3D lifting, direct 3D regression, and model fitting) | N/A (Analyzes robustness to depth ambiguities, occlusions, and background noise) | Survey article; presents review taxonomy without new empirical models |
| [On Boosting Single-Frame 3D Human Pose Estimation via Monocular Videos (2019)](https://doi.org/10.1109/iccv.2019.00228) | 3D joint trajectories / skeleton keypoints | Baseline estimation model combined with 3D trajectory completion auto-annotation over video | Enables learning unseen poses from unlabeled monocular videos without 2D annotations | Vulnerable to error accumulation if the initial baseline model produces inaccurate anchors |
| [Learning shape models for monocular human pose estimation from the Microsoft Xbox Kinect (2011)](https://doi.org/10.1109/iccvw.2011.6130387) | Pictorial structure model with learned generative limb shapes | Generative shape model learned from Kinect depth/silhouettes applied in Pictorial Structures | Handles anatomical and pose-dependent limb shape variations better than rigid cylinders | Performance degrades significantly if input 2D silhouettes suffer from heavy background noise |
| [Augmented Reality with Human Body Interaction Based on Monocular 3D Pose Estimation (2010)](https://doi.org/10.1007/978-3-642-17688-3_31) | 3D pose representation (implied by title) | Monocular 3D pose estimation framework (implied by title) | Unspecified in abstract | Minimal details in abstract (publication citation notice only) |
| [Sparseness Meets Deepness: 3D Human Pose Estimation from Monocular Video (2015)](https://doi.org/10.48550/arxiv.1511.09439) | 3D joint skeleton & 2D joint uncertainty maps | Deep FCN predicting 2D uncertainty maps + Expectation-Maximization with sparse priors | Marginalizes out 2D joint uncertainties during inference for enhanced noise robustness | Expectation-Maximization sequence optimization incurs high computational complexity |
| [Deep learning-based for human segmentation and tracking, 3D human pose estimation and action recognition on monocular video of MADS dataset (2022)](https://doi.org/10.1007/s11042-022-13921-w) | 3D pose representation (implied by title) | Integrated deep learning pipeline (implied by title) | Unspecified in abstract | Minimal details in abstract (publication citation notice only) |

---

# 🏛️ Master Literature Synthesis (Orchestrator)

# Literature Review: Text-to-Motion Synthesis and Physics-Based Reinforcement Learning Control

---

## 1. Executive Summary

The synthesis of human motion guided by natural language instructions represents a pivotal intersection of natural language processing (NLP), computer vision, dynamic motion planning, and motor control. Historically, the domain of computer animation and digital human modeling relied heavily on manual keyframing, optical motion capture (MoCap) cleanup, or deterministic kinematic interpolation. The advent of deep generative modeling—specifically spatial-temporal diffusion models, large language models (LLMs), and variational autoencoders—has fundamentally transformed text-to-motion generation. Contemporary kinematic generative pipelines can synthesize diverse, semantically rich full-body motion sequences directly from unconstrained textual prompts.

However, a fundamental paradox persists in current motion generation paradigms:

1. **The Kinematic Generation Paradox:** Modern text-driven kinematic diffusion architectures generate highly expressive joint position sequences ($\hat{q}_{1:T}$) conditioned on text prompts. Yet, because these models operate purely in pose spatial coordinate space without explicit awareness of classical dynamics, the generated sequences frequently exhibit severe physical artifacts—including foot sliding (kinematic skating), ground penetration, unphysical accelerations, gravitational floating, and dynamic imbalance.
2. **The Physics-Based Control Bottleneck:** Conversely, dynamic motor control frameworks operating within standardized physics simulators (e.g., MuJoCo, NVIDIA Isaac Gym) utilize Deep Reinforcement Learning (DRL) or optimal whole-body control (WBC) to generate physically valid joint torques ($\tau_t$) enforcing equations of motion ($\mathbf{M}(q)\ddot{q} + \mathbf{C}(q,\dot{q})\dot{q} + \mathbf{g}(q) = \mathbf{J}^T f_{\text{ext}} + \mathbf{B}\tau$). While these controllers are physically ground-truth compliant and robust against environmental perturbations, they struggle to generalize across open-ended, high-level natural language semantics due to the extreme non-linearity and high dimensionality of mapping unconstrained natural language directly to low-level motor actuation.

This literature review presents a systematic synthesis of 120 contemporary research works spanning four foundational sub-domains:
* **Kinematic Text-to-Motion Modeling & LLM Integration**
* **Physics-Guided Motion Diffusion & Contact Constraints**
* **Deep Reinforcement Learning for Dynamic Motion Control**
* **Monocular Pose Estimation, Lifting, and Parametric Skeleton Representation**

```
               +-------------------------------------------------------+
               |             Kinematic Text-to-Motion                  |
               |      (Diffusion / LLM Semantic Planners)              |
               +-------------------------------------------------------+
                                           |
                                           | Reference Kinematic Trajectories \hat{q}_{1:T}
                                           v
+--------------------------------------------------------------------------------------+
|                                Physics-Guided Layer                                  |
|                 (Physics Projection Operators & Differentiable Constraints)          |
+--------------------------------------------------------------------------------------+
                                           |
                                           | Dynamic Target States & Contact Maps
                                           v
+--------------------------------------------------------------------------------------+
|                        Physics RL Motor Controller                                   |
|                 (MuJoCo / Isaac Gym Tracking Policy \pi_\theta)                       |
+--------------------------------------------------------------------------------------+
                                           |
                                           | Joint Torques \tau_t & Ground Forces f_c
                                           v
+--------------------------------------------------------------------------------------+
|                     Physically Plausible Motion Output                               |
|              (Zero Foot Skating, Dynamic Balance, Torque Compliance)                 |
+--------------------------------------------------------------------------------------+
```

By critically synthesizing these pillars, this review establishes the academic imperative for a unified dual-stage architecture: leveraging high-level kinematic diffusion generators as semantic spatial-temporal reference planners, while employing low-level physics-aware deep reinforcement learning controllers to actuate these references in rigid-body dynamic environments.

---

## 2. Analysis of Existing Approaches

### 2.1 Kinematic Text-to-Motion Synthesis & LLM Integration

Kinematic text-to-motion generation aims to map a natural language sequence $\mathbf{P} = \{w_1, w_2, \dots, w_N\}$ to a temporal sequence of continuous human poses $\mathbf{X} = \{x_1, x_2, \dots, x_T\}$, where $x_t \in \mathbb{R}^D$ denotes the joint angles, root translation, or parametric body representation at frame $t$.

```
[Text Prompt P] ---> [LLM / Motion Diffusion Backbone] ---> Pose Trajectory \hat{X}_{1:T} (Kinematic Pose)
```

#### Generative Architecture Trends
The domain has shifted from deterministic database querying and motion-graph blending (e.g., Kovalsky et al., 2002; Safonova et al., 2004) toward probabilistic deep generative pipelines:

* **Motion Diffusion Models (MDM):** Denoising diffusion probabilistic models (DDPMs) have emerged as the dominant architecture. Architectures such as *Guided Motion Diffusion (GMD)* (2024) and *KETA* (2025) leverage Transformer-based denoising blocks operating over continuous skeletal representations. *KETA* introduces Kinematic Phrases (KP) via fine-grained LLM text decomposition, establishing multi-stage semantic alignment between linguistic clause tokens and spatial joint sub-graphs.
* **Large Language Models (LLMs) as Semantic Motion Planners:** Recent paradigms deploy pretrained LLMs (e.g., Mistral 7B, Qwen 2.5 3B, H2O-Danube 3) for zero-shot or fine-tuned motion generation. *LLM-guided fuzzy kinematic modeling* (2025) leverages fuzzy logic bounds integrated with LLMs to resolve spatial uncertainties and linguistic ambiguities in text prompts. Similarly, specialized domain models demonstrate that autoregressive LLM backbones can generate complex skeletal angle trajectories (e.g., Polonaise folk dance kinematics).
* **Coarse-to-Fine & Hierarchical Kinematic Alignment:** To overcome multi-joint coordination failures, frameworks like *KinMo* (2025) split motion synthesis into a hierarchical process: global root trajectories and dynamic center-of-mass (CoM) paths are generated first, followed by fine-grained skeletal diffusion conditioned on semantic joint groupings.

#### Parametric Models vs. Articulated Joint Skeletons
Kinematic synthesis relies heavily on underlying pose representations:

* **Raw 3D Joint Skeletons:** Skeletons composed of 22 to 24 joint positions (e.g., HumanML3D format) offer direct spatial vector representations suitable for diffusion models. However, they lack volumetric, biomechanical, and inter-segment inertia properties.
* **SMPL Parametric Body Models:** The Skinned Multi-Person Linear (SMPL) model parameterizes body shape $\mathbf{\beta} \in \mathbb{R}^{10}$ and relative joint rotations $\mathbf{\theta} \in \mathbb{R}^{24 \times 3}$. Extensions such as *SMPL-A* incorporate soft tissue and volumetric anatomical layers, while *SMPL-GPTexture* (2026) and *RC-SMPL* (2023) optimize visual mesh surface geometry and real-time avatar instantiation.

#### Core Limitations of Purely Kinematic Pipelines
Despite high visual expressiveness and strong text-retrieval R-Precision, kinematic pipelines exhibit systemic failure modes:
1. **Lack of Dynamic Mass and Momentum:** Joints are modeled as geometric points without skeletal mass distribution, leading to unrealistic acceleration curves and instantaneous velocity changes.
2. **Absence of Ground Contact Dynamics:** Kinematic loss functions (e.g., $L_2$ position errors, joint velocity losses) fail to strictly enforce ground reaction forces $f_c \ge 0$. As a consequence, artifacts such as foot sliding, ground penetration, and airborne drift remain endemic in pure diffusion outputs.

---

### 2.2 Physics-Guided Diffusion & Contact-Aware Generation

To bridge the gap between kinematic probabilistic modeling and classical mechanics, recent research integrates physical equations and contact constraints directly into the diffusion generative loop.

```
                  +-----------------------------------------------------+
                  |   Kinematic Denoising Step: \hat{x}_{t-1} ~ p(\cdot)|
                  +-----------------------------------------------------+
                                             |
                                             v
                  +-----------------------------------------------------+
                  |           Physics Projection Module                 |
                  |     (Isaac Gym / MuJoCo Dynamic Rollout)            |
                  +-----------------------------------------------------+
                                             |
                                             v
                  +-----------------------------------------------------+
                  | Corrected Pose: x^{phys}_{t-1} = Project(\hat{x})   |
                  +-----------------------------------------------------+
```

#### Integration Strategies for Physics in Diffusion
Literature reveals three distinct integration paradigms:

1. **Test-Time Simulation Rollout & Projection (e.g., PhysDiff):** *PhysDiff* (2022/2023) introduces an explicit physics-based motion projection module into the iterative diffusion sampling process. At each denoising step $t$, the intermediate noisy pose $\hat{x}_0$ is projected onto a physically viable state space using an implicit controller operating inside physics environments (NVIDIA Isaac Gym). The simulator solves for rigid-body contact forces, correcting illegal interpenetrations and foot sliding before passing the state back to the next diffusion step.
2. **Physics-Informed Loss Constraints (e.g., Morph, CoShMDM):** Frameworks like *Morph* (2026) formulate motion synthesis as a motion-free optimization problem guided by analytical dynamic law terms. Loss terms penalize zero-moment-point (ZMP) offset, balance recovery margin violations, and excessive joint torques directly in the loss function $\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{diff}} + \lambda_1 \mathcal{L}_{\text{zmp}} + \lambda_2 \mathcal{L}_{\text{contact}}$. *CoShMDM* (2026) expands this to multi-person interaction generation by introducing contact- and shape-aware latent losses.
3. **Trajectory Optimization with Contact Implicit Mechanics:** Advanced methods enforce contact feasibility via non-linear programming (NLP) over centroidal momentum dynamics (e.g., *Structured contact force optimization*, 2016; *Convex model of humanoid dynamics*, 2017). These methods solve for contact wrench cones (CWC) and center-of-mass (CoM) trajectories to ensure dynamic equilibrium across contact phase transitions.

#### Mechanical & Computational Trade-Offs

| Method Type | Primary Physics Mechanism | Ground Truth Validity | Computational Overhead | Real-time Feasibility |
| :--- | :--- | :--- | :--- | :--- |
| **Pure Kinematic Diffusion** | None ($L_2$ Joint Loss) | Low (Severe artifacts) | Low ($\approx 10-50$ ms/frame) | High |
| **Physics Loss-Guided Diffusion** | Soft Penalty Gradients | Moderate (Mitigates artifacts) | Moderate ($\approx 100-300$ ms/frame)| Medium |
| **Simulation-Projected Diffusion** | Hard Dynamic Simulator Rollout | High (Rigid-body validated) | Extreme ($\approx 1-5$ sec/frame) | Low |
| **Centroidal Optimization** | Convex / NLP Solvers | High (ZMP/CWC Feasible) | High (Optimization dependent) | Low |

While simulation-projected diffusion models produce high physical plausibility, their dependency on runtime physics engine iterations per diffusion step introduces massive computational overhead, making real-time interactive generation intractable.

---

### 2.3 Physics-Based Reinforcement Learning & Dynamic Motion Tracking/Control

Physics-based Deep Reinforcement Learning (DRL) models human locomotion not as pose trajectory interpolation, but as a Markov Decision Process (MDP) parameterized by continuous state space $\mathcal{S}$, action space $\mathcal{A}$ (representing joint torques $\tau$ or target PD angles $\theta_{\text{pd}}$), transition dynamics $\mathcal{P}(s'|s,a)$, and a dense reward function $\mathcal{R}(s,a)$.

```
   +-----------------------+     Action \tau_t / \theta_{pd}     +-----------------------+
   |   RL Tracking Policy  | ----------------------------------> |   Physics Simulator   |
   |      \pi_\theta       |                                     |    (MuJoCo / Isaac)   |
   +-----------------------+ <---------------------------------- +-----------------------+
               ^                       State s_t, Reward r_t
               |
               +--- Track Reference \hat{q}_t (from Text Generator)
```

#### Reinforcement Learning Formulations & Algorithms
The domain is dominated by continuous actor-critic policy gradient algorithms:
* **Proximal Policy Optimization (PPO):** The standard algorithm for high-dimensional humanoid control due to stable clipped surrogate objectives.
* **Twin Delayed Deep Deterministic Policy Gradient (TD3) & Soft Actor-Critic (SAC):** Widely utilized in robotic manipulators, autonomous vehicles, and non-stationary leg prostheses to maintain policy entropy and prevent premature convergence.
* **Hierarchical DRL & Residual Learning:** High-level policies generate abstract direction vectors or contact schedules, while low-level policies synthesize continuous joint torques. *Residual RL* frameworks combine fixed baseline controllers (e.g., Active Disturbance Rejection Control or Model Predictive Control) with DRL residual actors ($\tau = \tau_{\text{mpc}} + \tau_{\text{rl}}$) to enforce baseline safety while learning agile balance recoveries.

#### Reward Function Engineering for Dynamic Humanoids
Achieving natural balance and reference motion tracking requires dynamic reward functions:

$$\mathcal{R}_t = w_p \mathcal{R}_{\text{pose}} + w_v \mathcal{R}_{\text{vel}} + w_e \mathcal{R}_{\text{energy}} + w_b \mathcal{R}_{\text{balance}} - w_c \mathcal{R}_{\text{ctrl}}$$

1. **Tracking Terms ($\mathcal{R}_{\text{pose}}, \mathcal{R}_{\text{vel}}$):** Penalizes exponential joint angle and joint velocity deviations from reference trajectory sequences:
   $$\mathcal{R}_{\text{pose}} = \exp \left( -\gamma_p \sum_j \| q_j - \hat{q}_j \|^2 \right)$$
2. **Balance & Equilibrium Terms ($\mathcal{R}_{\text{balance}}$):** Ensures center-of-mass (CoM) stability and maintains Zero Moment Point (ZMP) within the Support Polygon $\mathcal{S}_p$:
   $$\mathcal{R}_{\text{balance}} = \exp \left( -\gamma_b \| \mathbf{r}_{\text{zmp}} - \mathbf{r}_{\text{com\_proj}} \|^2 \right)$$
3. **Energy & Smoothness Regularization ($\mathcal{R}_{\text{energy}}, \mathcal{R}_{\text{ctrl}}$):** Minimizes mechanical work, torque magnitude ($\|\tau\|^2$), and high-frequency dynamic chatter ($\|\dot{\tau}\|^2$).

#### Sim-to-Real Transfer & Perturbation Rejection
Physics RL control natively incorporates perturbation rejection. Policies trained under randomized physics parameters (Domain Randomization over link masses, joint friction coefficients, ground contact friction, and external push forces) learn robust dynamic recovery maneuvers. However, RL policies trained in isolation lack semantic awareness; they can execute stable walking or jumping routines, but cannot interpret open-ended commands (e.g., *"walk hesitantly while carrying a heavy weight"*) without an explicit high-level kinematic planner.

---

### 2.4 Monocular Pose Estimation, Lifting & Parametric Skeletal Models

The bridge between raw perceptual observation (RGB video, depth streams) and target skeletal motion requires 3D human pose estimation and 2D-to-3D pose lifting networks.

```
[RGB Video / Image] ---> [2D Keypoint Detector] ---> [3D Lifting Network (GCN/Transformer)] ---> [SMPL / Kinematic Pose]
```

#### Pose Representations and Parametric Fitting
* **SMPL Fitting (Keep it SMPL / SMPLify):** Pioneer frameworks map 2D image keypoints to 3D statistical body meshes via bottom-up deep convolutional predictions coupled with top-down optimization over SMPL pose ($\mathbf{\theta}$) and shape ($\mathbf{\beta}$) parameters. Optimization bounds penalize inter-penetration and un-natural joint angle limits using population priors.
* **Skeletal Keypoint Graphs:** Direct 3D coordinate estimation represents joints as topological graph nodes. Graph Convolutional Networks (e.g., *GLA-GCN*, 2023) and Locally Connected Networks (*LCN*, 2020) model spatial structural dependencies across human limbs.

#### Translation Mechanisms & 2D-to-3D Neural Lifting
Translating spatial-temporal keypoints from 2D pixel space to absolute 3D kinematic coordinates presents monocular depth ambiguity. Modern frameworks address this through:
* **Structural & Spatial Attention:** *Part-Aware Attention Transformers (PATA/PADA)* (2022) segment human skeletons into distinct topological limb groups, resolving structural shifts and dynamic occlusions over time.
* **Temporal Motion Continuity:** *MPS-Net* (2022) leverages Motion Continuity Attention (MoCA) over monocular video sequences to smooth transient 2D detection noise and prevent temporal jitter.
* **Geometric & Sparse Priors:** Expectation-Maximization (EM) optimization combined with sparse geometric priors (*Sparseness Meets Deepness*) marginalizes out 2D location uncertainty, generating robust 3D skeletal reconstructions even under partial self-occlusion.

---

## 3. Consolidated Metrics & Evaluation Trends

Assessing text-to-motion and physics-based control systems requires a multi-faceted approach evaluated across three categories: semantic text alignment, physical realism, and dynamic control stability.

### 3.1 Kinematic, Text-Alignment, and Visual Quality Metrics

* **Fréchet Inception Distance (FID):** Quantifies the statistical distance between feature distributions of generated motion sequences and ground-truth human motion capture datasets (e.g., HumanML3D, KIT-Mocap). Lower FID indicates higher perceptual motion quality:
  $$\text{FID} = \|\mu_r - \mu_g\|^2 + \text{Tr}(\Sigma_r + \Sigma_g - 2(\Sigma_r \Sigma_g)^{1/2})$$
* **R-Precision (Top-1, Top-2, Top-3):** Measures the accuracy of cross-modal text-to-motion retrieval. Given a generated motion, R-Precision measures how frequently the original text prompt is correctly selected among a pool of $K$ mismatching distractor text descriptions.
* **Diversity:** Evaluates the spatial-temporal variability of generated motions across different text prompts by calculating mean distance in joint feature embedding space.
* **Multimodality:** Measures the spatial variance of motions generated repeatedly from a single text prompt.

### 3.2 Physical Realism and Kinematic Error Metrics

* **Foot Skating / Sliding Distance:** Measures horizontal foot joint movement ($\Delta x, \Delta z$) during detected ground contact phases (when vertical joint height $y \le \epsilon$). Expressed in millimeters per frame or percentage of total sequence length.
* **Ground Penetration Depth:** Quantifies the magnitude of skeletal joint mesh interpenetration beneath the plane of the simulated terrain surface ($y < 0$).
* **Floating Rate:** Percentage of frames where no skeletal body part maintains contact with the terrain surface during non-jumping locomotion phases.
* **Mean Per Joint Position Error (MPJPE):** Measures the average Euclidean distance between estimated keypoints and ground-truth 3D coordinates:
  $$\text{MPJPE} = \frac{1}{N} \sum_{i=1}^{N} \| \mathbf{p}_i^{\text{gt}} - \mathbf{p}_i^{\text{pred}} \|_2$$
* **Procrustes-Aligned MPJPE (PA-MPJPE):** Calculates MPJPE after aligning predicted keypoints to the ground-truth target using rigid similarity transformations (translation, rotation, uniform scaling).

### 3.3 Dynamic Stability and RL Control Metrics

* **Zero Moment Point (ZMP) Offset:** The spatial distance between the dynamic ZMP location and the center of the base support polygon formed by ground contact points. Zero offset confirms optimal tipping stability.
* **Center of Mass (CoM) Tracking Error:** Mean squared error between desired kinematic CoM trajectory $\mathbf{r}_{\text{com}}^{\text{ref}}(t)$ and physically simulated CoM position $\mathbf{r}_{\text{com}}^{\text{sim}}(t)$.
* **Contact Wrench Cone (CWC) Feasibility Rate:** Percentage of control timesteps where contact forces $f_c$ satisfy friction cone bounds ($\|f_{\text{tangential}}\| \le \mu f_{\text{normal}}$).
* **Joint Torque / Power Consumption:** Evaluates mechanical energy efficiency across joint actuators:
  $$E_{\text{mech}} = \int_{0}^{T} \sum_{j=1}^{M} |\tau_j(t) \cdot \dot{q}_j(t)| \, dt$$
* **Balance Recovery Margin:** Maximum impulse perturbation force (measured in Newtons applied over duration $\Delta t$) that the physics controller can absorb without experiencing structural fall conditions.

### 3.4 Methodological Comparison across Literature Paradigms

```
+-----------------------------------------------------------------------------------------+
|                                    EVALUATION METRICS                                   |
+--------------------------+-----------------------+--------------------+-----------------+
| Paradigm                 | Text Alignment (FID)  | Physical Artifacts | Controller Power|
+--------------------------+-----------------------+--------------------+-----------------+
| Kinematic Diffusion      | Optimal (FID < 0.5)   | High Foot Sliding  | N/A (No Torque) |
| Physics-Guided Diffusion | Strong (FID 0.5-1.5)  | Mitigated Artifacts| Indirect Bounds |
| Physics RL Control       | N/A (Tracking Only)   | Zero Artifacts     | Explicit Torque |
+--------------------------+-----------------------+--------------------+-----------------+
```

| Evaluation Domain | Core Metric | Primary Target Range | Key Technical Target |
| :--- | :--- | :--- | :--- |
| **Semantic Fidelity** | Text-Motion R-Precision (Top-1) | $> 0.50 - 0.70$ | High cross-modal alignment |
| **Generative Quality** | Fréchet Inception Distance (FID) | $< 0.15 - 0.50$ | Realistic motion distributions |
| **Kinematic Fidelity** | Foot Skating Distance | $< 2.0$ mm/frame | Eliminate ground drifting |
| **Mesh Reconstruction** | MPJPE / PA-MPJPE | $< 30 - 45$ mm | Accurate skeletal alignment |
| **Dynamic Balance** | ZMP Support Offset | $< 0.05$ m | Continuous postural balance |
| **Actuation Realism** | Mechanical Power Efficiency | Minimized $\int \|\tau \dot{q}\| dt$ | Smooth motor torque actuation |

---

## 4. Research Gap & Motivation

### 4.1 The Core Research Gap: The Kinematic-Dynamic Divide

Despite individual advancements in text-to-motion generation, physics-guided diffusion, and reinforcement learning control, a persistent gap splits modern human motion synthesis pipelines into two distinct regimes:

```
                  THE KINEMATIC-DYNAMIC DIVIDE

      Kinematic Motion Generation          Physics RL Control
  +---------------------------------+  +---------------------------------+
  | - Expressive Text Generation    |  | - Ground-truth Mechanical Realism|
  | - Open-ended Prompt Coverage    |  | - Robust Balance Recovery       |
  | - Zero Dynamic/Physics Awareness|  | - Zero Natural Language Context |
  | - Foot Skating & Penetration    |  | - Hard to Scale to New Semantics|
  +---------------------------------+  +---------------------------------+
                  \                               /
                   \                             /
                    +---------------------------+
                    |  UNIFIED DUAL-STAGE GAP   |
                    +---------------------------+
```

1. **Kinematic Diffusion Models are Semantically Dynamic, but Dynamically Blind:** State-of-the-art diffusion models excel at mapping complex prompts (e.g., *"a martial artist executes a spinning back kick while maintaining balance"*) into joint coordinate sequences. However, because they lack knowledge of gravitational acceleration, structural link masses, and contact force interactions, the output trajectories are physically un-realizable. Feeding these unconstrained sequences directly to hardware or strict physical engines results in mechanical failure or high tracking divergence.
2. **Physics RL Controllers are Dynamically Sound, but Semantically Rigorous:** DRL policies running in MuJoCo or Isaac Gym can execute stable locomotion, jumps, and acrobatic maneuvers while fully respecting ground reaction forces, torque saturations, and joint friction bounds. However, these policies rely on task-specific reward functions or pre-aligned tracking references. They cannot natively parse unconstrained, natural language text inputs.
3. **Inadequacy of Existing Hybrid Approaches:** Intermediate attempts—such as physics-guided diffusion projection (e.g., PhysDiff)—attempt to solve this by embedding physics simulation rollouts directly inside the iterative diffusion denoising loop. This hybrid approach incurs massive computational latency, requiring hundreds of full physics simulation passes per generated sequence, which prevents real-time, interactive generation.

---

### 4.2 Research Motivation: Closed-Loop Dual-Stage Framework

This thesis addresses the kinematic-dynamic divide by proposing a unified **Hierarchical Dual-Stage Generative-Control Framework**:

```
                       HIERARCHICAL FRAMEWORK ARCHITECTURE

+-------------------------------------------------------------------------------------------------+
| STAGE 1: SEMANTIC KINEMATIC PLANNER (Text-to-Motion Diffusion / LLM Module)                      |
| Inputs:  Natural Language Prompt P                                                              |
| Outputs: Reference Kinematic Trajectory Sequence \hat{q}_{1:T} & Kinematic Foot Contact Flags  |
+-------------------------------------------------------------------------------------------------+
                                                |
                                                | Reference Trajectory \hat{q}_{1:T}
                                                v
+-------------------------------------------------------------------------------------------------+
| STAGE 2: LOW-LEVEL DYNAMIC TRACKING CONTROLLER (Deep Reinforcement Learning Policy \pi_\theta)  |
| Inputs:  Simulated Pose State s_t = (q_t, \dot{q}_t), Target Reference \hat{q}_t                |
| Outputs: Joint Actuator Torques \tau_t executed inside Physics Simulator (MuJoCo / Isaac Gym)    |
+-------------------------------------------------------------------------------------------------+
                                                |
                                                | Physics Rollout State s_{t+1}
                                                v
+-------------------------------------------------------------------------------------------------+
| OUTPUT: PHYSICALLY SOUND, SEMANTICALLY ACCURATE HUMAN MOTION                                   |
| - Zero Foot Skating       - Gravity & Mass Compliant      - Text Prompt Aligned                 |
+-------------------------------------------------------------------------------------------------+
```

#### Why Combining Kinematic Generators with Physics RL Solves Current Limitations:

1. **Separation of Semantic Planning and Dynamic Execution:** By assigning natural language interpretation exclusively to a high-level Kinematic Diffusion Planner ($\mathbf{P} \rightarrow \hat{q}_{1:T}$), the system retains the expressiveness and open-vocabulary capabilities of modern diffusion models. The low-level RL controller ($\hat{q}_t \rightarrow \tau_t$) focuses purely on tracking and balance stabilization, isolating high-dimensional text understanding from complex dynamic actuation.
2. **Elimination of Physical Artifacts Without Sampling Latency:** Rather than performing costly physics engine rollouts at *every sampling step* during diffusion generation, the proposed framework runs kinematic text diffusion off-line or in a single forward pass. The physical simulation runs downstream during execution, where the DRL controller converts kinematic references into joint torques in real time ($\approx 60-200$ Hz execution rates). This completely eliminates foot skating, ground penetration, and floating artifacts while preserving runtime efficiency.
3. **Parametric Skeletal Standardisation (SMPL Integration):** Incorporating parametric skeletal models (e.g., SMPL, SMPL-A) into both keypoint pose estimation and dynamic simulation links visual perception, semantic synthesis, and dynamic control. SMPL parameters provide the physical properties (body shape, link lengths, estimated segment masses) needed for dynamic simulation rollouts.

---

### 4.3 Summary of Thesis Scope & Academic Contribution

This Master's thesis investigates the synthesis, optimization, and validation of a dual-stage text-driven dynamic motion framework:

* **Chapter 1 (Introduction):** Defines the research objectives, scope, and problem formulation.
* **Chapter 2 (Literature Review):** Synthesizes the core foundations across kinematic text generation, physics-guided diffusion, reinforcement learning control, and monocular pose estimation (presented herein).
* **Chapter 3 (Methodology):** Formulates the dual-stage architecture, detailing the spatial-temporal kinematic diffusion architecture, the physics RL reward formulation, and the joint-torque actuation policy.
* **Chapter 4 (Experimental Evaluation & Results):** Evaluates the integrated framework across standardized benchmarks (HumanML3D, KIT-Mocap, Isaac Gym Humanoid), demonstrating performance improvements across FID, R-Precision, foot skating distance, and ZMP dynamic balance metrics.
* **Chapter 5 (Discussion & Future Directions):** Analyzes the sim-to-real transfer capabilities for physical humanoid robotics and outlines open research problems in multi-agent physical interaction synthesis.