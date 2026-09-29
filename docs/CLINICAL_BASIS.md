# Clinical basis, norms and limitations

PunarGati automates what a physiotherapist does with a stopwatch, a goniometer and a tally counter. It measures and coaches, and leaves prescribing and diagnosing to the clinician.

## The problem, with sources

| Claim | Source |
|---|---|
| Knee osteoarthritis prevalence in India is about 28.7% in pooled studies | Pal CP et al. *Epidemiology of knee osteoarthritis in India and related factors.* Indian J Orthop. 2016;50(5):518–522 |
| India has about 101 million people with diabetes | Anjana RM et al. ICMR-INDIAB-17. *Lancet Diabetes Endocrinol.* 2023;11(7):474–489 |
| Adhesive capsulitis (frozen shoulder) affects about 13% of people with diabetes vs 2–5% of the general population | Zreik NH, Malik RA, Charalambous CP. *Muscles Ligaments Tendons J.* 2016;6(1):26–34 |
| Roughly 28–35% of people aged 65+ fall each year | WHO *Global Report on Falls Prevention in Older Age*, 2007 |
| Adherence to physiotherapist-prescribed home exercise is a well-documented problem | Peek K et al. *Physiotherapy.* 2016;102(2):127–135 |

## Screening tests implemented

### 30-second chair stand
- **Protocol**: the patient sits in the middle of a firm chair with arms crossed over the chest, then stands fully and sits as many times as possible in 30 s.
- **Detection**: the signal is shoulder height above the feet, median-filtered and self-calibrated to the patient's own seated and standing heights, so it works **from the front or the side**. Knee angle fails from the front because the seated thigh points at the camera and the knee looks straight. A stand counts at 80% of the seated→standing range, and the next one only after dropping below 35% (hysteresis).
- **Validation**: on the CDC's own demonstration video (front view, public domain), 3 of 3 stands are counted, matching a hand count. This clip is a regression test (`tests/test_video.py`).
- **Interpretation**: the CDC STEADI "below average" thresholds, where a lower score indicates fall risk:

| Age | Men | Women |
|---|---|---|
| 60–64 | < 14 | < 12 |
| 65–69 | < 12 | < 11 |
| 70–74 | < 12 | < 10 |
| 75–79 | < 11 | < 10 |
| 80–84 | < 10 | < 9 |
| 85–89 | < 8 | < 8 |
| 90–94 | < 7 | < 4 |

Sources: CDC STEADI *Assessment: 30-Second Chair Stand*; Jones CJ, Rikli RE, Beam WC. *Res Q Exerc Sport* 1999;70(2):113–119. Under age 60 no threshold is shown, and the app tracks the patient's own trend instead.

### Single-leg stance (eyes open)
- **Protocol**: the patient faces the camera with arms crossed and lifts one foot. The clock starts when one ankle rises more than 6% of body height above the other. It stops when they're level again for 5 frames, or at 45 s.
- **Reference means** (Springer BA et al. *J Geriatr Phys Ther* 2007;30(1):8–15): 18–39 y ≈ 43 s · 40–49 ≈ 40 s · 50–59 ≈ 37 s · 60–69 ≈ 27 s · 70–79 ≈ 15 s · 80+ ≈ 6 s. Under 5 s is flagged because inability to stand on one leg for 5 s predicted injurious falls (Vellas BJ et al. *J Am Geriatr Soc* 1997;45(6):735–738).

### Active range of motion
- Shoulder flexion (side view), shoulder abduction (front view) and knee flexion (side view, standing heel-to-buttock). The score is the best **median-of-5-frames** value over 15 s, so a single-frame keypoint glitch can't set a record.
- Reference values from the American Academy of Orthopaedic Surgeons (*Joint Motion: Method of Measuring and Recording*, 1965): shoulder flexion 180°, abduction 180°, knee flexion 135°. Results under 80% of the reference are marked "limited".

## Exercise measurements

| Exercise | Signal (2-D, pixels) | Rest → movement → target |
|---|---|---|
| Mini squat | knee flexion, mean of visible sides | < 20° → > 40° → 75° |
| Sit to stand | 90° − knee flexion | seated → standing |
| Seated knee extension | knee flexion per side, reported as degrees short of straight | 90° → ≤ 10° |
| Shoulder forward / side raise | hip–shoulder–elbow angle per side | < 30° → > 65° → 150° |
| Elbow curl | elbow flexion per side | < 35° → > 75° → 120° |
| Standing hip abduction | thigh vs the trunk's downward axis, per side | < 8° → > 16° → 28° |
| Standing march | hip flexion per side | < 20° → > 45° → 70° |

**Rep quality** = range reached ÷ target range × a tempo factor (0.85 if the rep is faster than 45% of ideal tempo) × a form factor (−20% per fault, floor 40%).

**Form rules** fire only after persisting for 4 consecutive frames, and only in the camera view where they're observable. For example, knee valgus is checked only from the front, and trunk lean in a squat only from the side.

## Limitations (stated in the app and the report)

1. **2-D projection.** A single camera measures angles in the image plane. When the moving segment isn't square to the camera, the angle is under-estimated. PunarGati tells the patient which view each exercise needs ("turn side-on", "face the camera") and reports trends rather than single readings.
2. **17 keypoints.** MoveNet has no feet or hands, so there's no ankle dorsiflexion or wrist/finger ROM yet. The roadmap adds AI Hub's RTMPose wholebody (133 keypoints).
3. **Not validated against a goniometer yet.** Counting is validated on real footage: 3/3 stands on the CDC chair-stand video and 2/2 on the squat clip. The synthetic-skeleton unit tests recover joint angles to within 0.5°. A validation study against a clinical goniometer with a physiotherapist is the next step.
4. **One person in frame.** MoveNet is a single-person model. If a caregiver stands next to the patient, the tracker can switch to them, so the app asks for one person in view. We saw this on the side-view part of the CDC video, where the assessor stands behind the patient.
5. **Not a medical device.** It doesn't diagnose, doesn't change the prescription, and escalates red-flag symptoms to the clinician.
