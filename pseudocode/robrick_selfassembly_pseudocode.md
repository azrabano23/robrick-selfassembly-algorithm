# Robrick Self-Assembly Algorithm — Pseudocode
**CS7–CS9 Subteam | Lunar & Planetary Servicing Swarm Robots — Team 11**
**Author: Azra Bano | Rutgers University, ECE**

---

## Overview

Each Robrick operates as a **fully decentralized agent** — no global map, no central controller, no prior knowledge of the final structure. All decisions emerge from **local interaction rules**: what the robot can directly sense (neighbor IR signals, load on its own frame, dock current) and what it receives over short-range communication.

Modeled on:
- **Fire-ant bridge formation** — ants attach based on local load and neighbor density, not a blueprint
- **S-DASH** — each robot propagates a gradient from a seed and decides whether to attach based on its position in that gradient field

Six states: ROAMING → SENSING → EVALUATING → ALIGNING → DOCKING → ATTACHED
Two interrupt handlers: RECONFIGURING, RECOVERY

---

## Constants

```
COMM_RANGE          = 8 * ROBOT_RADIUS    // max IR communication range (Kilobot paper)
DOCK_RANGE          = 1.2 * ROBOT_RADIUS  // proximity needed to attempt physical docking
MAX_LOAD_RATIO      = 3.0                 // max load as multiple of own mass
HEARTBEAT_HZ        = 10                  // broadcast rate (Hz)
LATCH_CURRENT_MIN   = 0.4                 // amps — minimum for confirmed contact (FireAnt)
LATCH_CURRENT_OK    = 0.8                 // amps — confirmed strong bond
INTEGRATED_AMP_S    = 5.35               // amp-seconds for full melt bond (FireAnt 2D)
COOL_TIME_MS        = 2000               // hold time after melt before trusting bond
DOCKING_TIMEOUT_MS  = 30000              // abort if docking takes longer than 30 sec
MAX_RETRIES         = 3                  // attempts before blacklisting a target
BLACKLIST_TIMEOUT   = 60000             // ms to avoid a failed target
REPAIRER_ELEV_REQ   = true              // if true, bias toward stair/ramp formation
NUM_STAIR_STEPS     = 4                 // elevation levels in target staircase
DOCK_VOLTAGE        = 24                // volts (from FireAnt design)
```

---

## Data Structures

```
RobrickState {
    id              : int           // unique robot ID (set at boot)
    state           : enum          // current FSM state
    position        : (x, y)        // local position estimate from SLAM/odometry
    orientation     : float         // heading in degrees
    dock_state      : enum          // FREE | SEEKING | ACCEPTING | BLOCKED
    gradient_val    : int           // S-DASH gradient (0=seed, increases outward, 255=INF)
    load_estimate   : float         // load on own frame in kg (proxied from motor stall current)
    neighbor_list   : List<Neighbor>
    structure_role  : enum          // ANCHOR | BRIDGE | STAIR_STEP_N | AVAILABLE
    target          : Neighbor      // current docking candidate
    retry_count     : int
    blacklist       : Map<id, expiry_time>
    amp_seconds     : float         // accumulated during docking
    timer           : int
}

Neighbor {
    id              : int
    distance        : float         // from IR RSSI measurement, ±2mm accuracy
    gradient_val    : int
    dock_state      : enum
    load_estimate   : float
    structure_role  : enum
    last_heard_ms   : int           // drop if > 2 * HEARTBEAT_PERIOD
}
```

---

## Main Loop

```
FUNCTION main():
    INITIALIZE:
        state        ← ROAMING
        gradient_val ← 255            // INF — not yet part of structure
        dock_state   ← FREE
        retry_count  ← 0
        amp_seconds  ← 0

    LOOP forever:
        receive_messages()            // passive IR receive, always on, non-blocking
        update_neighbor_list()        // expire neighbors not heard in 2 * HEARTBEAT_PERIOD
        broadcast_status()            // transmit 8-byte heartbeat at HEARTBEAT_HZ

        MATCH state:
            ROAMING       → run_roaming()
            SENSING       → run_sensing()
            EVALUATING    → run_evaluating()
            ALIGNING      → run_aligning()
            DOCKING       → run_docking()
            ATTACHED      → run_attached()
            RECONFIGURING → run_reconfiguring()
            RECOVERY      → run_recovery()
```

---

## State 1: ROAMING

```
FUNCTION run_roaming():
    move_forward(speed = SLOW)

    IF obstacle_detected():
        turn(random_angle in [-90°, +90°])
        RETURN

    FOR EACH neighbor n in neighbor_list:
        IF n in blacklist AND current_time < blacklist[n.id]: CONTINUE
        IF n.gradient_val < 255:
            state ← SENSING
            RETURN
```

The random walk prevents clustering. The gradient field acts like a beacon — robots near the structure hear low gradient values and transition to SENSING.

---

## State 2: SENSING

```
FUNCTION run_sensing():
    stop_motors()
    dock_state ← SEEKING

    FOR EACH neighbor n in neighbor_list:
        IF n in blacklist: CONTINUE
        n.distance     ← measure_IR_distance(n.id)
        n.gradient_val ← parse_gradient(n.last_message)

    best ← NULL
    FOR EACH neighbor n in neighbor_list:
        IF n.distance > COMM_RANGE: CONTINUE
        IF n.dock_state == BLOCKED: CONTINUE
        IF best == NULL OR n.gradient_val < best.gradient_val:
            best ← n

    IF best != NULL:
        target ← best
        state  ← EVALUATING
    ELSE:
        state  ← ROAMING
```

---

## State 3: EVALUATING

```
FUNCTION run_evaluating():

    // Heuristic 1: Load Check (fire-ant load-based attachment)
    IF target.load_estimate > MAX_LOAD_RATIO * SELF_MASS:
        state ← ROAMING
        RETURN

    // Heuristic 2: Gradient Check (S-DASH rule)
    // Only attach if target is closer to seed — guarantees outward growth, no loops
    IF target.gradient_val >= self.gradient_val:
        state ← ROAMING
        RETURN

    // Heuristic 3: Role Check (staircase formation for Repairer Bot)
    IF REPAIRER_ELEV_REQ:
        desired_layer ← (target.gradient_val + 1) MOD NUM_STAIR_STEPS
        IF desired_layer != expected_next_step():
            IF stair_position_available_elsewhere():
                state ← ROAMING
                RETURN

    // All checks passed — commit
    self.gradient_val ← target.gradient_val + 1
    dock_state        ← SEEKING
    state             ← ALIGNING
```

---

## State 4: ALIGNING

```
FUNCTION run_aligning():
    angle_to_target ← compute_bearing(self.position, target.position)
    turn_to(angle_to_target)

    WHILE distance_to(target) > DOCK_RANGE:
        move_forward(speed = SLOW)
        update_position_estimate()

        IF distance_to(target) > COMM_RANGE * 1.5:
            state ← SENSING
            RETURN

        IF obstacle_between(self, target):
            navigate_around_obstacle()

    stop_motors()
    state ← DOCKING
```

---

## State 5: DOCKING

```
FUNCTION run_docking():
    dock_state  ← SEEKING
    amp_seconds ← 0
    timer       ← 0

    press_toward_target(force = NOMINAL_PRESS_FORCE)
    enable_dock_current(voltage = DOCK_VOLTAGE)

    LOOP:
        current ← read_current_sensor()
        timer   ← timer + dt

        IF timer > DOCKING_TIMEOUT_MS:
            log_event(DOCK_TIMEOUT, target.id)
            state ← RECOVERY
            RETURN

        IF current > SMOKE_THRESHOLD:
            disable_dock_current()
            log_event(DOCK_SMOKE, target.id)
            state ← RECOVERY
            RETURN

        IF current > LATCH_CURRENT_MIN:
            amp_seconds ← amp_seconds + (current * dt)

        IF amp_seconds >= INTEGRATED_AMP_S:
            BREAK

    disable_dock_current()
    hold_position(duration = COOL_TIME_MS)

    pulse_test_current()
    final_current ← read_current_sensor()

    IF final_current >= LATCH_CURRENT_OK:
        dock_state     ← BLOCKED
        structure_role ← assign_role()
        retry_count    ← 0
        state          ← ATTACHED
    ELSE:
        state ← RECOVERY
```

Current as quality proxy: contact area ↑ → resistance ↓ → current ↑. Integrating to 5.35 amp-seconds yields a bond strong enough to resist 5kg pull force with no dedicated force sensor required.

---

## State 6: ATTACHED

```
FUNCTION run_attached():
    load_estimate ← read_load_proxy()

    IF load_estimate > MAX_LOAD_RATIO * SELF_MASS:
        broadcast_flag(DISTRESS)

    IF receive(TASK_PRIORITY_CHANGED):
        state ← RECONFIGURING
        RETURN

    IF receive(ROBOT_DROPOUT, id = dropped_id):
        IF dropped_id IN self.neighbor_list:
            state ← RECONFIGURING
            RETURN

    // gradient re-broadcast handled automatically by broadcast_status() in main loop
```

---

## Interrupt: RECONFIGURING

```
FUNCTION run_reconfiguring():
    // Re-melt bond at 180% of attachment energy (prevents spike formation — FireAnt paper)
    enable_dock_current(voltage = DOCK_VOLTAGE)
    wait_until(amp_seconds_detach >= MELT_DETACH_MS)

    pull_away_from_target(speed = VERY_SLOW)
    spin_dock_during_detach()          // presses down warm spikes
    disable_dock_current()

    dock_state     ← FREE
    structure_role ← AVAILABLE
    gradient_val   ← 255
    amp_seconds    ← 0
    state          ← ROAMING
```

---

## Interrupt: RECOVERY

```
FUNCTION run_recovery():
    disable_dock_current()
    back_away_from_target(distance = 2 * ROBOT_RADIUS)
    dock_state  ← FREE
    amp_seconds ← 0

    log_event(DOCK_FAILURE, target.id, timestamp, reason)

    retry_count ← retry_count + 1

    IF retry_count < MAX_RETRIES:
        state ← SENSING
    ELSE:
        retry_count ← 0
        blacklist[target.id] ← current_time + BLACKLIST_TIMEOUT
        state ← ROAMING
```

---

## Communication Protocol

```
8-byte heartbeat packet (broadcast at HEARTBEAT_HZ):

Byte  Field           Description
────  ──────────────  ──────────────────────────────────────────────────
 0    sender_id       Unique robot ID (assigned at boot)
 1    gradient_val    0–254 = hops from seed; 255 = INF (not attached)
 2    dock_state      0=FREE, 1=SEEKING, 2=ACCEPTING, 3=BLOCKED
 3    structure_role  0=AVAILABLE, 1=ANCHOR, 2=BRIDGE, 3–6=STAIR_STEP_N
 4    load_hi         High byte of load_estimate (kg × 100, big-endian)
 5    load_lo         Low byte
 6    flags           Bit0=DISTRESS, Bit1=TASK_CHANGED, Bit2=DROPOUT, Bit3=COMPLETE
 7    checksum        XOR of bytes 0–6

Expiry: drop neighbor if (current_time - last_heard_ms) > 2 * HEARTBEAT_PERIOD
```

---

## S-DASH Gradient Initialization

```
FUNCTION initialize_seed():
    self.gradient_val  ← 0
    self.structure_role ← ANCHOR
    self.dock_state    ← ACCEPTING
    self.state         ← ATTACHED
    // broadcasts continuously — origin of the gradient field
    // all others hear gradient=0, increment as they attach, re-broadcast
```

Self-healing: if robots are removed, remaining robots re-propagate from seed with corrected hop counts. Structure re-forms at smaller scale proportional to remaining count. No manual intervention.

---

## Staircase Role Assignment

```
FUNCTION assign_role():
    layer ← self.gradient_val MOD NUM_STAIR_STEPS
    MATCH layer:
        0 → RETURN GROUND_LEVEL
        1 → RETURN STAIR_STEP_1
        2 → RETURN STAIR_STEP_2
        3 → RETURN STAIR_STEP_3
        _ → RETURN BRIDGE_TOP

// Robots at STAIR_STEP_N:
//   Accept docking only from robots with gradient_val = self.gradient_val - 1
//   Present top dock face as ACCEPTING for next elevation layer
//   Side faces set to BLOCKED
```

---

## Failure Modes & Mitigations

| Failure | Detection | Response |
|---|---|---|
| Spike formation | Elevated contact resistance after detach | Spin dock + 180% amp-seconds before pulling |
| Smoke / arc | Current exceeds SMOKE_THRESHOLD | Cut current immediately → RECOVERY |
| Comm dropout | Neighbor expires from list | RECONFIGURING if structural neighbor |
| Slot bid collision | Two robots same point (CS4–CS6) | Lower ID wins, other re-enters SENSING |
| Load over limit | Motor stall current proxy | Broadcast DISTRESS, await reinforcement |
| Gradient disconnect | Discontinuity after robot removal | S-DASH self-heal: rescale, fill gap |
| Docking timeout | timer > DOCKING_TIMEOUT_MS | RECOVERY → retry or blacklist + ROAMING |

---

## Integration: CS4–CS6 (Swarm Registry)

Produces (subscribe to):
- dock_state — slot availability per robot per heartbeat
- structure_role — structural position this robot occupies
- gradient_val — position in gradient field

Must implement:
- Mutex on slot claiming (prevent simultaneous bids)
- Tiebreak: lower robot ID wins; other immediately re-enters ROAMING
- Task priority broadcast that triggers RECONFIGURING across attached robots

---

## Integration: Mechanical Team (ME4–ME6)

1. Multi-angle dock access — no single required alignment angle (FireAnt/FireAnt3D insight)
2. Current-readable motor — stall current accessible to MCU as structural load proxy
3. 3 independent dock faces — triangular prism; each face needs its own dock_state
4. Wheel lockout — retractable wheels must lock so robot holds position without motor power

---

*References: Swissler & Rubenstein 2018 (FireAnt ICRA), Swissler & Rubenstein 2020 (FireAnt3D IROS), Rubenstein & Nagpal 2010 (Kilobot/S-DASH), Beltran et al. 2018 (Kilobot Collective Behaviors IMECS), Team 11 MVP Development Master Document*
