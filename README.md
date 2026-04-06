# 🤖 Robrick Self-Assembly Algorithm

### Decentralized Swarm Intelligence for Lunar & Planetary Servicing Robots
**Team 11 — CS7–CS9 Self-Assembly Subteam**
**Author: Azra Bano | Rutgers University, ECE**

---

## 🌕 What is this? (The 2nd-grade version)

Imagine you have a bunch of little robots on the Moon. They need to build a staircase **out of themselves** so a bigger robot can climb up and fix something. But there's no boss robot telling everyone what to do. Each little robot just looks at its neighbors, asks "should I connect here?" and decides on its own. Together, they build the whole staircase — no instructions needed. That's exactly what this code does.

---

## 🚀 The real version (for the MIT engineer)

This repository contains the **decentralized self-assembly algorithm** for the Robrick robots in Team 11's Lunar & Planetary Servicing Swarm Robotics project. The algorithm enables a collective of autonomous, triangular-prism-shaped Robrick units to self-organize into load-bearing structures (ramps, stairs, bridges) using only **local sensor data and short-range IR communication** — no centralized controller, no global map, no pre-planned blueprint.

The algorithm is modeled on two biological and algorithmic precedents:
1. **Fire-ant bridge formation** — ants self-assemble using local load sensing and neighbor density, not top-down coordination
2. **S-DASH (Scalable Distributed Assembly Heuristic)** — Harvard's Kilobot algorithm for gradient-based shape formation that self-heals when robots are removed

The intended output structure is a **staircase configuration** that gives the Repairer Bot access to elevated positions for inspection and maintenance tasks during autonomous lunar surface operations.

---

## 📋 My Task & How I Completed It

I was assigned to **CS7–CS9 (Self-Assembly subteam)** within the 10-person CS team. My deliverable:

> Write the **pseudocode for the Robrick swarm self-assembly algorithm** — the logic that governs how individual Robricks decide when to move, when to connect, and how to collectively form a structure without any central controller.

**How I did it:**

**Step 1 — Literature review.** I read and synthesized 4 peer-reviewed papers on swarm robotics and modular self-assembly. I focused on: what makes docking reliable, how swarm algorithms create structure from local rules, and what failure modes look like on real hardware.

**Step 2 — Algorithm design.** I identified two core inspirations: FireAnt's current-based dock quality sensing, and Kilobot's S-DASH gradient propagation. I adapted both to our specific hardware constraints: triangular prism geometry, retractable wheels, and a latch mechanism whose bond quality can be estimated through motor current.

**Step 3 — Finite state machine.** I mapped the full robot lifecycle into 6 states (ROAMING → SENSING → EVALUATING → ALIGNING → DOCKING → ATTACHED) plus 2 interrupt handlers (RECONFIGURING, RECOVERY). Every state transition has explicit triggers and exit conditions.

**Step 4 — Integration specs.** I documented exactly what CS4–CS6 (swarm registry) needs from this algorithm, what the mechanical team needs to expose in hardware, and how the 8-byte communication packet is structured for ROS2.

---

## 📚 Papers Used — Full Citations

### 1. FireAnt: A Modular Robot with Full-Body Continuous Docks
**Authors:** Petras Swissler, Michael Rubenstein
**Venue:** 2018 IEEE International Conference on Robotics and Automation (ICRA), pp. 6812–6817

**What it contributed:**
FireAnt introduced the continuous dock — a strip of conductive PLA plastic that melts on contact with another strip, forming a rigid bond at any point on the robot's body without requiring alignment. The biological analogy is direct: fire ants grab each other wherever they can reach, not at designated connectors.

The key insight we borrowed: **current flow as a bond quality proxy**. As two docks melt together, contact area grows → resistance drops → current rises. By integrating current over time (target: 5.35 amp-seconds from the paper), the robot knows it has a strong bond without any dedicated force sensor. This is the basis for our entire DOCKING state.

The three dock voltage states — SEEKING (+24V), ACCEPTING (GND), BLOCKED (high-Z) — map directly to our dock_state enum.

FireAnt demonstrated 100% success across 200 attachment trials at 5kg pull force, and average failure load of 23.9kg — over 20× the robot's own weight. We used this to set MAX_LOAD_RATIO = 3.0, giving a safety factor of ~7.6×.

---

### 2. FireAnt3D: A 3D Self-Climbing Robot Towards Non-Latticed Robotic Self-Assembly
**Authors:** Petras Swissler, Michael Rubenstein
**Venue:** 2020 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)
**Code/CAD:** https://github.com/pswiss/Swissler-2020-FireAnt3D-Design

**What it contributed:**
FireAnt3D extends continuous docking into 3D — docks become hemispheres instead of wheels, enabling attachment at any 3D contact angle. The new component is the ground-return hoop: a conductive ring that sweeps around the hemisphere to find the contact point before melting begins.

Critical insight for our project: **non-latticed structures**. Every other robotic self-assembly system constrains robots to fixed docking points, forcing rigid lattice formations. FireAnt3D allows amorphous connections — attach anywhere, at any angle. This is far more robust in a lunar environment where surface is uneven and robots are mass-produced with loose tolerances.

Average tensile strength across 10 trials: 767N (min 540N, max 1036N), equivalent to 23× the robot's weight. The six-phase locomotion sequence — Detach → Flip → Prepare → Flip → Settle → Attach — directly inspired our state machine structure.

---

### 3. Kilobot: A Robotic Module for Demonstrating Behaviors in a Large Scale (2¹⁰ Units) Collective
**Authors:** Michael Rubenstein, Radhika Nagpal
**Venue:** IEEE ICRA Workshop on Modular Robotics: State of the Art, Anchorage, AK, May 2010, pp. 47–51
**Repository:** Harvard DASH — http://nrs.harvard.edu/urn-3:HUL.InstRepos:5504015

**What it contributed:**
Kilobot is a ~$15 robot built specifically for thousand-robot swarm experiments. Its IR emitter/receiver bounces light off the floor to communicate with neighbors at up to 750 packets/second with ±2mm distance accuracy. This is the hardware basis for our COMM_RANGE, DOCK_RANGE, and neighbor distance measurement in the SENSING state.

The **S-DASH algorithm** introduced here is the engine of our gradient propagation system:
- One robot is designated the seed (gradient_val = 0)
- Each robot that successfully attaches sets gradient_val = parent.gradient_val + 1 and re-broadcasts
- The structure grows outward like an expanding wavefront from the seed
- If robots are removed, S-DASH automatically rescales the gradient → built-in self-healing

We adopted S-DASH's gradient field directly as our gradient_val field. The core evaluation heuristic — attach only if target.gradient_val < self.gradient_val — comes straight from this paper.

---

### 4. Implementing Collective Behaviors Using the Kilobot Platform
**Authors:** Franchesca Agatha V. Beltran, Hazel Anne P. Cruzat, Gia Nadine M. De Sagun, Elmer R. Magsino
**Venue:** Proceedings of IMECS 2018, Vol. II, pp. 601–606, Hong Kong
**ISSN:** 2078-0958 (Print), 2078-0966 (Online)

**What it contributed:**
This paper provided empirical results from physical hardware — 10 real Kilobots running real algorithms in a real arena. Essential for grounding our design in reality rather than simulation.

Key findings we incorporated:
- Target-surrounding success rate was only 60% due to locomotion noise → motivated our RECOVERY state and blacklist mechanism
- Communication overflow causes follower dropout at scale → motivated our fixed 8-byte packet format with XOR checksum and HEARTBEAT_HZ = 10 cap
- Surface smoothness is critical → flagged as a lunar regolith risk in our known limitations

---

## 🧠 How the Algorithm Works

### The big idea in one sentence
Every Robrick runs the same program. None of them knows what the final structure looks like. Smart collective behavior emerges from simple local rules — the same way ant colonies, bird flocks, and fish schools work. This is called **emergent behavior**.

### The Finite State Machine

```
                    ┌──────────────────────────────────────┐
                    │                                      │
          neighbor  │                        load too      │
          detected  ▼                        high / full   │
ROAMING ─────────► SENSING ──── in range ──► EVALUATING ──┘
   ▲                                              │
   │                                              │ attach = true
   │                                              ▼
   │                                          ALIGNING
   │                                              │
   │                                              │ aligned
   │                                              ▼
   │                          latch fail ───── DOCKING ──── confirmed ──► ATTACHED
   │                               │                                          │
   │                               ▼                                          │
   │◄──────── retrying ────── RECOVERY                         new task cmd  │
   │                                                                   ▼     │
   │◄──────────────── detached, re-enter ────────────────── RECONFIGURING ◄──┘
```

### The six states

| State | Plain English | Technical description |
|---|---|---|
| **ROAMING** | Looking for a job | Random walk, broadcasting gradient=INF |
| **SENSING** | Looking more carefully | Stops, measures IR distances to all neighbors |
| **EVALUATING** | Should I connect here? | Runs 3 local heuristics: load, gradient, role |
| **ALIGNING** | Getting into position | Navigates to within DOCK_RANGE of target |
| **DOCKING** | Connecting! | Engages latch, monitors amp-seconds for bond quality |
| **ATTACHED** | Part of the structure | Load-bearing, monitoring, re-broadcasting gradient |

### The three evaluation heuristics (the heart of the algorithm)

Before any robot commits to docking, it runs three checks — all must pass:

1. **Load check** — Is the target already overloaded? Prevents structural collapse. From fire-ant load-based attachment logic.
2. **Gradient check** — Am I one step further from the seed than my target? The S-DASH invariant — ensures outward-only growth with no loops.
3. **Role check** — If building a staircase, am I filling the right elevation step? Produces the layered structure the Repairer Bot needs.

### The two interrupt handlers

**RECONFIGURING** — New orders or neighbor dropout. Graceful detach: re-melt bond at 180% amp-seconds, pull away slowly, spin dock during separation to prevent spike formation (a failure mode documented in the FireAnt paper). Reset gradient to INF, re-enter as a fresh agent.

**RECOVERY** — Docking failed. Back away, log to telemetry, retry up to MAX_RETRIES. If still failing, blacklist that target for BLACKLIST_TIMEOUT and return to ROAMING.

---

## 📡 Communication Protocol

```
8-byte fixed-length heartbeat packet (broadcast at HEARTBEAT_HZ = 10):

Byte  Field           Values
────  ──────────────  ──────────────────────────────────────────────────────
 0    sender_id       Unique robot ID (set at boot)
 1    gradient_val    0–254 = hops from seed; 255 = INF (not attached)
 2    dock_state      0=FREE, 1=SEEKING, 2=ACCEPTING, 3=BLOCKED
 3    structure_role  0=AVAILABLE, 1=ANCHOR, 2=BRIDGE, 3–6=STAIR_STEP_N
 4    load_hi         High byte of load_estimate (kg × 100, big-endian)
 5    load_lo         Low byte of load_estimate
 6    flags           Bit0=DISTRESS, Bit1=TASK_CHANGED, Bit2=DROPOUT, Bit3=COMPLETE
 7    checksum        XOR of bytes 0–6
```

---

## 🔗 Integration Points

### CS4–CS6 (Swarm Registry & Task Allocation)
Subscribe to: dock_state, structure_role, gradient_val from every robot heartbeat.
Must implement: mutex on slot claiming to prevent simultaneous bids. Tiebreak: lower robot ID wins, other re-enters ROAMING immediately.

### CS1–CS3 (Localization, Mobility & Arm Movement)
ALIGNING needs: move_forward(), turn_to(), update_position_estimate() from the SLAM/odometry stack.
RECOVERY needs: back_away_from_target() motor control primitive.

### Mechanical Team (ME4–ME6)
1. Dock surfaces accessible from multiple approach angles — no single required alignment angle
2. Motor stall current readable as a load proxy
3. 3 independent dock faces on the triangular prism, each with its own dock_state
4. Retractable wheels that lock in place once structural position is achieved

---

## 📊 Milestone Alignment

| MVP Milestone | Algorithm Contribution | Target Metric |
|---|---|---|
| M3 — Docking feasibility | DOCKING state current loop | ≥95% latch success |
| M5 — Autonomous docking (bench) | Full States 1–5 pipeline | ≥90% assembly accuracy |
| M9 — Multi-robot localization | Gradient field + neighbor list sync | Consistent gradient across swarm |
| M10 — Cooperative motion | ATTACHED + load broadcast | Load balanced across structure |
| M11 — End-to-end mission | Full FSM with REPAIRER_ELEV_REQ=true | Staircase formed in <10 min |
| M12 — Stress test | RECOVERY + RECONFIGURING handlers | Zero crashes in 20-min run |

---

## ⚠️ Known Limitations

1. **Dock mechanism TBD** — assumes current-sensor bond quality; if ME uses magnets or mechanical latches, DOCKING and RECONFIGURING states need revision
2. **Lunar regolith locomotion** — Kilobot empirical results show noise on non-smooth surfaces; ALIGNING may need dead-reckoning correction
3. **Slot collision handling** — depends on CS4–CS6 registry mutex; without it two robots can simultaneously attempt the same point → both enter RECOVERY
4. **Seed election** — assumes one pre-designated seed; dynamic election if seed fails is not yet implemented

---

## 📁 Repository Structure

```
robrick-selfassembly-algorithm/
├── README.md
└── pseudocode/
    └── robrick_selfassembly_pseudocode.md
```

---

## 📖 Full References

1. Swissler, P., & Rubenstein, M. (2018). FireAnt: A modular robot with full-body continuous docks. *2018 IEEE International Conference on Robotics and Automation (ICRA)*, 6812–6817.

2. Swissler, P., & Rubenstein, M. (2020). FireAnt3D: A 3D self-climbing robot towards non-latticed robotic self-assembly. *2020 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)*.

3. Rubenstein, M., & Nagpal, R. (2010). Kilobot: A robotic module for demonstrating behaviors in a large scale (2¹⁰ units) collective. *Proceedings of the IEEE ICRA Workshop on Modular Robotics: State of the Art*, 47–51. Harvard DASH: http://nrs.harvard.edu/urn-3:HUL.InstRepos:5504015

4. Beltran, F. A. V., Cruzat, H. A. P., De Sagun, G. N. M., & Magsino, E. R. (2018). Implementing collective behaviors using the Kilobot platform. *Proceedings of IMECS 2018*, Vol. II, 601–606. ISBN: 978-988-14048-8-6.

---

*CS7–CS9 Self-Assembly Subteam | Team 11 | Rutgers University ECE*
