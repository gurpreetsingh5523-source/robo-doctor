# Pilot Clinic Guide (DRAFT)

How to run a real-world Robo Doctor pilot with one clinic — the fastest
path to credibility with government health institutions.

## Before the pilot

0. **Print and bring [docs/clinic_intro_letter.md](docs/clinic_intro_letter.md)**
   — a one-page invitation letter for the doctor.
1. **Get a licensed doctor as champion.** Robo Doctor never replaces them;
   the pilot measures how much *time it saves them*.
2. **Ethics & consent.** Print consent forms (general + genomic) in the
   local language. Every registered patient signs before data entry.
3. **Offline check.** Core flow (register → symptoms → tests → draft →
   doctor approval) works with zero internet. Verify on the clinic's machine.

## Suggested pilot scope (4 weeks)

- 1 doctor, 1 assistant, 50–100 patients
- Use: registration, symptom → test advice, blood panel analysis,
  early-signal trends on returning patients
- Do NOT use: genomic features (requires separate ethics approval)

## What to measure

| Metric | How |
|---|---|
| Doctor minutes saved per patient | Doctor logs time with/without system |
| Early signals later confirmed | Compare trend alerts vs. doctor's eventual diagnosis |
| Patient satisfaction | 3-question form after visit |
| Errors caught by doctor | Count of drafts modified/rejected — this is a *safety feature working*, report it positively |

## Feedback loop

Weekly 30-min review with the doctor. File every issue on GitHub.
After 4 weeks: write a public summary report — that document is what you
show to government health missions.

## Red lines

- Doctor sees and approves EVERY prescription draft
- No patient data leaves the clinic machine
- Any adverse event → pause pilot, review, fix
