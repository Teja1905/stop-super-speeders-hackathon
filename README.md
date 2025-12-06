# Stop-Super-Speeders-Hackathon
Families for Safe Streets - DSSG NYC: building a public transportation alert and warning system for New York State and city DMVs to alert super speeders violations.

### Background:

Intelligent Speed Assistance (ISA) devices are used to monitor the driving speeds of vehicles they installed. They are commonly referred to as “speed limiters” due to often being used with high-risk drivers.

NYCDOT’s study of drivers concluded that those with 16 or more speed safety camera violations are twice as likely to kill. Bill ([A.2299/S.4045](https://www.nysenate.gov/legislation/bills/2025/S4045/amendment/A)) proposes mandatory installation of ISA devices for drivers accumulating 11 or more points within a 24-month period, or receiving sixteen or more speed-camera tickets within 12 months. Such individuals must install a speed limiter in any vehicle they own or operate for at least 12 months. The Senate version of this bill passed in 2025, but the Assembly needs to approve this in 2026. 
The goal of this hackathon is to simulate the creation of an end to end data management system for monitoring driver license plates and drivers ids that would trigger the installation of an ISA device. Participants are to create a lightweight, versatile system that can be used to simulate how different NYC counties and agencies could easily run this system themselves.



## Prerequisites: TODOs before the hackathon
- Complete volunteer [registration](http://www.nyc-dssg.org) on DSSG-NYC website
- Join DSSG-NYC [Slack Group](https://join.slack.com/t/nyc-dssg/shared_invite/zt-3hz16bb3r-cHPu_q43IPn0eZxYO99aLw)
- Review DSSG [Anti-harassment Policy](https://github.com/dssg/hitchhikers-guide/blob/master/sources/dssg-manual/conduct-culture-and-communications/README.md), and [ethical standards](https://dssgfellowship.org/2015/09/18/an-ethical-checklist-for-data-science/)
- Review Family for Safe Streets Problem Statement: https://www.familiesforsafestreets.org/about
- Review [Data Mapping Documentation and Architecture](https://docs.google.com/document/d/17KtxoxqKwIKNLGwd1zQ5g4ZBZgqkQ4PuH2VLyByReq4/edit?usp=sharing)




## Task
- Design a working end to end system that can execute the following:
- Ingest historical data of traffic and speeding tickets
- Combine updated data with historical data, without duplicates
- Generate dataset lists of license plates and drivers ids that trigger the ISA threshold
- Display the results in a dashboard
- Trigger an email sending list of plates and driver as a CSV

## Deliverables
1. Make two Output Datasets containing:
   
 i) drivers’ table: 
> - primary key license
> - Type of violation
> - how many violations
> - Violation points
> - county registered

 ii) vehicle table: count
> - primary key
> - primary key license
> - number of violations
> - county where the vehicle is registered
- Total # drivers who currently trigger 11+ points in 24 month trailing window
- Total # plates who currently trigger 16 tickets in 12 month trailing window
4. Basic visual dashboard to display information and/or export CSV
5. Email alert system sent to: 1. The violator 2. Vendor 3. DMV
- Total # plates who, over the previous 12 month trailing window, who have triggered the list in November
- Total # drivers who, over the previous 24 month trailing window, who have triggered the list in November
- Warning systems for those that are just below the threshold and about to commit the violation
- Only send list of plates and drivers that are new and triggered the threshold
6. Presentation: Audience are technocrats for legislative processes and policy staff members

## Quickstart: running the lightweight ISA monitoring pipeline
The repository now includes a self-contained pipeline that ingests historical and incremental ticket files, de-duplicates them, computes driver/vehicle roll-ups, and emits dashboard/CSV/email artifacts.

1. Install dependencies (in a virtual environment):
   ```bash
   pip install -r <(python - <<'PY'
from pathlib import Path
import tomllib
deps = tomllib.loads(Path('pyproject.toml').read_text())['project']['dependencies']
print('\n'.join(deps))
PY
)
   ```
2. Populate `data/historical_tickets.csv` and `data/updates_tickets.csv` using the provided sample schema (`ticket_id,driver_id,license_number,plate,violation_type,violation_date,county`). Example seed files live in `data/`.
3. Run the end-to-end flow:
   ```bash
   python -m src.isa_pipeline
   ```
4. Review outputs in `outputs/`:
   - `drivers_table.csv` and `vehicle_table.csv` hold the required roll-ups and counts.
   - `triggered_*.csv` contain cohort members crossing ISA thresholds; `warning_*.csv` captures near-misses.
   - `newly_flagged_*.csv` list only net-new drivers/plates relative to the previous run; the persisted `alert_state.csv` tracks history.
   - `dashboard.html` provides a lightweight visual summary, and `outputs/emails/*.eml` captures the email payloads with CSV attachments for violators, vendors, and the DMV.

  
BONUS: 
- Create small database files for the offenders (bonus)
- Generate new visualizations and actionable insights for DMV officers
- Deploy as a web app

***
## How to Set up environment for the Hackathon:
>
>


***

## Hackathon Day Schedule (10 AM – 6 PM)

### 10:00 – 10:30 AM  
- Registration & Check-In  
- Volunteers at desk
- Coffee & light snack

### 10:30 – 11:00 AM  
- Kickoff & Welcome  
- Intro to schedule, rules, deliverables  
- Quick orientation on data
- Introduce captains, volunteers, and judges  

### 11:00 – 1:00 PM  
- Hacking Session #1: If there is enough participants, Split two teams competing with each other
- Teams brainstorm, form groups (if not pre-formed)  
- Mentors circulate to assist  
- Pacers check on setup 

### 1:00 – 2:00 PM  
- Lunch & Networking  
- Relax and mingle with other participants and mentors  

### 2:00 – 4:30 PM  
- Hacking Session #2  
- Focused development sprint  
- Pacers check teams’ progress and encourage testing  
- Organizers keep reminding about deliverables submission process  

### 4:30 – 5:00 PM  
- Break

### 5:00 – 6:00 PM  
- Submission Deadline Reminder & Final Touches  
- Timekeeper announces countdown (15 min left, 5 min left, final submission call)  
- Collect all project links (Google Form/Devpost/etc.)  

### 6:00 – 6:30 PM  
- Project Demos & Judging  
- Each team presents demo (5 mins each, adjust if many teams)  
- Judges score based on criteria: Innovation, Impact, Functionality, Presentation    
- Winners Announced & Group Thank You  
- Prizes awarded, photos taken, closing remarks  

***

## Celebration

### 6:30 PM – onwards  
- **Happy Hour at local bar**  
- Casual networking, celebration of winners, and socializing after event  

***

***

## Pre-Hackathon Preparations Checklist

### Venue and Logistics
- Confirm venue booking (size large enough for teams, strong Wi-Fi, power supply, breakout areas).  
- Test **internet bandwidth** and ensure guest Wi-Fi credentials.  
- Arrange **tables, seating, and power strips** (at least 1 outlet per participant).  
- Order **A/V equipment**, microphones, projectors, and screens.  
- Prepare **check-in desk** setup: tables, lanyards/badges, pens, markers.  
- Print **signage** for directions (restrooms, food area, hackathon space).  

### Food & Beverages
- Order **meal catering** (breakfast, lunch, dinner if longer event, snacks).  
- Arrange **coffee/tea station** and water refill stations.  
- Consider **dietary needs** (vegetarian, vegan, gluten-free, halal/kosher options).  

### Sponsorship & Budget
- Finalize **sponsors** (API credits, prizes, food, venue).  
- Prepare **budget breakdown**: venue, food, swag, printing, prizes.  
- Order **prizes** (gift cards, tech gadgets, mentorship sessions).  

### Volunteers & Staff
- Recruit **volunteers** for registration, logistics, and team support.  
- Assign **mentors/tech helpers** 
- Designate **judges** (partners, sponsors, technical experts).  
- Train volunteers on **registration flow** and **timekeeping process**.  

### Marketing & Communication
- Launch **event website or registration portal**.  
- Confirm participant registrations and waitlist.  
- Send **pre-event email** with details: schedule, APIs, rules, starter kit links.  
- Create a **Slack server** for participant communication.  

### Judging & Deliverables
- Define **judging criteria** (e.g. Innovation, Functionality, Impact, Technical Implementation, Presentation).  
- Create a **submission form** (Devpost, Google Forms, or GitHub submission guidelines).  
- Prepare **presentation schedule** for final demos.  

***


