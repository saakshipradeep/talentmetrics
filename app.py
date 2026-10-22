import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="TalentMetrics | Recruitment Operations", page_icon="📊", layout="wide")

STAGES = ["Applied", "Screening", "Assessment", "Interview Scheduling", "Interview", "Hiring Review", "Offer", "Hired", "Rejected", "Withdrawn"]
ACTIVE = STAGES[:7]
ROLES = ["Client Service Associate", "Campus Recruitment Coordinator", "Summer Analyst Intern"]
UNIVERSITIES = ["Northeastern University", "NYU", "Columbia University", "Rutgers University", "Boston University", "Fordham University", "Cornell University", "University of Michigan"]
RECRUITERS = ["Alex Morgan", "Jordan Lee", "Taylor Chen", "Sam Rivera"]

@st.cache_data
def generate_data(n=240, seed=2027):
    rng = np.random.default_rng(seed)
    anchor = pd.Timestamp("2027-05-31")
    records = []
    stage_probs = [0.12, 0.13, 0.11, 0.09, 0.12, 0.09, 0.06, 0.09, 0.13, 0.06]
    for i in range(n):
        applied = anchor - pd.Timedelta(days=int(rng.integers(5, 125)))
        stage = str(rng.choice(STAGES, p=stage_probs))
        elapsed = (anchor - applied).days
        assessment_at = applied + pd.Timedelta(days=int(rng.integers(3, 10))) if stage in STAGES[2:] else pd.NaT
        interview_invited_at = applied + pd.Timedelta(days=int(rng.integers(7, 18))) if stage in STAGES[3:] else pd.NaT
        interview_at = interview_invited_at + pd.Timedelta(days=int(rng.integers(2, 15))) if pd.notna(interview_invited_at) and stage in STAGES[4:] else pd.NaT
        offer_at = interview_at + pd.Timedelta(days=int(rng.integers(3, 15))) if pd.notna(interview_at) and stage in ["Offer", "Hired"] else pd.NaT
        hired_at = offer_at + pd.Timedelta(days=int(rng.integers(1, 12))) if pd.notna(offer_at) and stage == "Hired" else pd.NaT
        # Keep all milestones within the reporting date; avoid impossible future events.
        for label in ["assessment_at", "interview_invited_at", "interview_at", "offer_at", "hired_at"]:
            value = locals()[label]
            if pd.notna(value) and value > anchor:
                if label == "assessment_at": assessment_at = pd.NaT
                elif label == "interview_invited_at": interview_invited_at = pd.NaT
                elif label == "interview_at": interview_at = pd.NaT
                elif label == "offer_at": offer_at = pd.NaT
                else: hired_at = pd.NaT
        # Stage durations are independently simulated, not inferred from complete audit history.
        stage_days = int(rng.integers(1, min(28, elapsed + 1)))
        task_due = anchor + pd.Timedelta(days=int(rng.integers(-14, 18))) if stage in ACTIVE else pd.NaT
        records.append({
            "candidate_id": f"SIM-{i+1:04d}",
            "candidate_name": f"Candidate {i+1:03d}",
            "role": str(rng.choice(ROLES)),
            "university": str(rng.choice(UNIVERSITIES)),
            "recruiter": str(rng.choice(RECRUITERS)),
            "application_date": applied,
            "stage": stage,
            "days_in_current_stage": stage_days,
            "assessment_date": assessment_at,
            "interview_invitation_date": interview_invited_at,
            "interview_date": interview_at,
            "offer_date": offer_at,
            "hire_date": hired_at,
            "follow_up_due": task_due,
            "task_status": str(rng.choice(["Open", "In progress", "Done"], p=[0.55, 0.30, 0.15])) if stage in ACTIVE else "Not applicable",
            "reschedule_count": int(rng.choice([0, 1, 2], p=[0.78, 0.18, 0.04])),
        })
    df = pd.DataFrame(records)
    df["overdue"] = df["follow_up_due"].notna() & (df["follow_up_due"] < anchor) & (df["task_status"] != "Done")
    df["scheduling_days"] = (df["interview_date"] - df["interview_invitation_date"]).dt.days
    df["application_to_offer_days"] = (df["offer_date"] - df["application_date"]).dt.days
    return df

raw = generate_data()
AS_OF = pd.Timestamp("2027-05-31")
st.title("TalentMetrics")
st.caption("Recruitment Operations & Hiring Funnel Analytics · Fictional portfolio case study")
st.info("All candidate records, hiring outcomes, and performance figures are **synthetic**. Reporting snapshot: **May 31, 2027**. This dashboard does not contain real applicant information.")

with st.sidebar:
    st.header("Filters")
    roles = st.multiselect("Position", sorted(raw.role.unique()), default=sorted(raw.role.unique()))
    universities = st.multiselect("University", sorted(raw.university.unique()), default=sorted(raw.university.unique()))
    recruiters = st.multiselect("Recruiter", sorted(raw.recruiter.unique()), default=sorted(raw.recruiter.unique()))
    start_date, end_date = st.date_input("Application date range", value=(raw.application_date.min().date(), raw.application_date.max().date()), min_value=raw.application_date.min().date(), max_value=raw.application_date.max().date())
    st.caption("Metrics describe the filtered applicant cohort, not the entire organization's recruiting performance.")

mask = raw.role.isin(roles) & raw.university.isin(universities) & raw.recruiter.isin(recruiters) & raw.application_date.dt.date.between(start_date, end_date)
df = raw.loc[mask].copy()
if df.empty:
    st.warning("No applicants match these filters. Adjust your selections.")
    st.stop()

# Current-stage snapshots are not a full historical funnel. Reached-stage rates below
# are calculated only where milestone evidence exists, with terminal stage as additional evidence.
def reached_interview(data):
    return data.interview_date.notna() | data.stage.isin(["Interview", "Hiring Review", "Offer", "Hired"])
def reached_offer(data):
    return data.offer_date.notna() | data.stage.isin(["Offer", "Hired"])

interviewed = reached_interview(df)
offered = reached_offer(df)
hired = df.stage.eq("Hired")
withdrawn = df.stage.eq("Withdrawn")

st.subheader("Recruitment scorecard")
metrics = [
    ("Applications", f"{len(df):,}", "Applicants in selected cohort"),
    ("Interview reach rate", f"{interviewed.mean():.1%}", "Share with interview milestone or later stage"),
    ("Interview → offer", f"{offered.sum()/interviewed.sum():.1%}" if interviewed.sum() else "N/A", "Offers / candidates reaching interview"),
    ("Offer → hire", f"{hired.sum()/offered.sum():.1%}" if offered.sum() else "N/A", "Hires / candidates reaching offer; proxy for acceptance"),
    ("Overdue follow-ups", str(int(df.overdue.sum())), "Open tasks due before snapshot date"),
    ("Median scheduling time", f"{df.scheduling_days.median():.0f} days" if df.scheduling_days.notna().any() else "N/A", "Invitation to interview date, where recorded"),
]
for row in (metrics[:3], metrics[3:]):
    cols = st.columns(3)
    for col, (label, value, help_text) in zip(cols, row):
        col.metric(label, value, help=help_text)

left, right = st.columns(2)
with left:
    st.subheader("Current pipeline stage")
    stage_counts = df.stage.value_counts().reindex(STAGES, fill_value=0).reset_index()
    stage_counts.columns = ["Stage", "Candidates"]
    fig = px.bar(stage_counts, x="Candidates", y="Stage", orientation="h", title="Current status (not historical funnel conversion)")
    fig.update_layout(yaxis={"categoryorder": "array", "categoryarray": list(reversed(STAGES))}, height=470)
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Application volume")
    weekly = df.assign(week=df.application_date.dt.to_period("W").apply(lambda x: x.start_time)).groupby("week").size().reset_index(name="Applications")
    st.plotly_chart(px.line(weekly, x="week", y="Applications", markers=True, title="Applications by week"), use_container_width=True)
    st.subheader("Applications by university")
    uni = df.university.value_counts().reset_index()
    uni.columns = ["University", "Applications"]
    st.plotly_chart(px.bar(uni, x="Applications", y="University", orientation="h"), use_container_width=True)

st.subheader("Recruiter workload")
workload = df.groupby("recruiter").agg(
    assigned_candidates=("candidate_id", "count"),
    overdue_followups=("overdue", "sum"),
    median_days_in_stage=("days_in_current_stage", "median")
).reset_index().rename(columns={"recruiter": "Recruiter", "assigned_candidates": "Assigned candidates", "overdue_followups": "Overdue follow-ups", "median_days_in_stage": "Median days in current stage"})
st.dataframe(workload, use_container_width=True, hide_index=True)

st.subheader("Operational attention queue")
threshold = st.slider("Flag candidates waiting at least this many days in current stage", 3, 30, 10)
queue = df[df.stage.isin(ACTIVE) & ((df.days_in_current_stage >= threshold) | df.overdue)].copy()
queue["attention_reason"] = np.select(
    [queue.overdue & (queue.days_in_current_stage >= threshold), queue.overdue],
    ["Overdue task + prolonged stage", "Overdue task"],
    default="Prolonged stage"
)
queue = queue.sort_values(["overdue", "days_in_current_stage"], ascending=[False, False])
st.dataframe(queue[["candidate_id", "role", "recruiter", "stage", "days_in_current_stage", "follow_up_due", "attention_reason"]], use_container_width=True, hide_index=True)

st.subheader("Stage-duration diagnostics")
st.caption("Days in current stage are simulated snapshot estimates. This is not a measured historical time-to-stage analysis.")
durations = df[df.stage.isin(ACTIVE)].groupby("stage").days_in_current_stage.median().reindex(ACTIVE).dropna().reset_index()
durations.columns = ["Stage", "Median days"]
st.plotly_chart(px.bar(durations, x="Stage", y="Median days", title="Median current-stage age"), use_container_width=True)

with st.expander("Methodology, definitions & limitations", expanded=False):
    st.markdown("""
    **Dataset:** Reproducible fictional applicant cohort generated with a fixed random seed. All dates and figures are synthetic. Snapshot date: May 31, 2027.

    **Applications:** Number of candidate records after filtering.

    **Interview reach rate:** Candidates with an interview date or a current stage at/after interview, divided by all filtered applicants. This is not a mature-cohort conversion rate: many applications are still in progress.

    **Interview → offer:** Candidates with offer evidence divided by candidates with interview evidence. Open cases remain in the denominator, so the ratio is a snapshot progression indicator.

    **Offer → hire:** Current hired records divided by candidates with offer evidence. This is a **proxy**, not a validated offer acceptance rate, because separate offer acceptance and start events are not captured.

    **Scheduling turnaround:** Calendar days between interview invitation and scheduled interview date for records where both exist. This measures lead time, not the administrative time taken to schedule.

    **Overdue follow-ups:** Follow-up due before the snapshot date, with task not marked done.

    **Current-stage age:** A simulated per-record value, not a reconstructed stage transition history.

    **Limitations:** Some synthetic milestones are incomplete; no real ATS integration, recruiter productivity benchmarking, causal inference, fairness audit, or real candidate outcomes. Use real event logs and explicit offer accepted/declined dates to calculate robust historical funnel conversion and true offer acceptance rates.
    """)

st.subheader("Export data")
st.download_button("Download filtered simulated candidate records (CSV)", data=df.to_csv(index=False).encode("utf-8"), file_name="talentmetrics_simulated_candidates.csv", mime="text/csv")
st.download_button("Download recruiter workload (CSV)", data=workload.to_csv(index=False).encode("utf-8"), file_name="talentmetrics_recruiter_workload.csv", mime="text/csv")
st.caption("Built with Python, Streamlit, Pandas, NumPy and Plotly · Portfolio demonstration only")
