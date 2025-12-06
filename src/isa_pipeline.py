from __future__ import annotations

from datetime import date, timedelta
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

import polars as pl

DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
POINT_VALUE_FILE = Path("seeds/point_values.csv")
PREVIOUS_ALERTS_FILE = OUTPUT_DIR / "alert_state.csv"


def _ensure_output_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "emails").mkdir(parents=True, exist_ok=True)


def load_points(path: Path = POINT_VALUE_FILE) -> pl.DataFrame:
    """Load violation point values."""
    return pl.read_csv(path)


def load_ticket_batches(paths: Iterable[Path]) -> list[pl.DataFrame]:
    frames: list[pl.DataFrame] = []
    for path in paths:
        frames.append(
            pl.read_csv(path, try_parse_dates=True).with_columns(
                pl.col("violation_date").cast(pl.Date, strict=False)
            )
        )
    return frames


def merge_and_score_tickets(frames: list[pl.DataFrame], points: pl.DataFrame) -> pl.DataFrame:
    """Combine all tickets, de-duplicate by ticket_id, and attach point values."""
    combined = pl.concat(frames, how="vertical_relaxed").unique(subset=["ticket_id"])
    scored = combined.join(
        points.rename({"violation_points": "violation_type", "points": "violation_points"}),
        on="violation_type",
        how="left",
    ).with_columns(
        pl.col("violation_points").fill_null(0)
    )
    return scored


def build_driver_table(tickets: pl.DataFrame) -> pl.DataFrame:
    return (
        tickets.group_by("license_number")
        .agg(
            pl.col("violation_type").unique().alias("violation_types"),
            pl.len().alias("violation_count"),
            pl.col("violation_points").sum().alias("violation_points"),
            pl.col("county").mode().first().alias("county_registered"),
        )
        .with_columns(pl.col("violation_types").list.join("; "))
        .sort("license_number")
    )


def build_vehicle_table(tickets: pl.DataFrame) -> pl.DataFrame:
    return (
        tickets.group_by("plate", "license_number")
        .agg(
            pl.len().alias("violation_count"),
            pl.col("county").mode().first().alias("county_registered"),
        )
        .sort(["plate", "license_number"])
    )


def reference_date(tickets: pl.DataFrame) -> date:
    value = tickets["violation_date"].max()
    return value if isinstance(value, date) else value.item()


def window_start(anchor: date, days: int) -> date:
    return anchor - timedelta(days=days)


def detect_driver_thresholds(tickets: pl.DataFrame, anchor: date) -> tuple[pl.DataFrame, pl.DataFrame]:
    window = window_start(anchor, 730)
    recent = tickets.filter(pl.col("violation_date") >= window)
    driver_points = (
        recent.group_by("license_number")
        .agg(
            pl.col("violation_points").sum().alias("points_last_24m"),
            pl.len().alias("violations_last_24m"),
            pl.col("violation_date").max().alias("last_violation_date"),
        )
        .with_columns(pl.col("last_violation_date").dt.month().alias("last_violation_month"))
    )
    triggered = driver_points.filter(pl.col("points_last_24m") >= 11)
    warnings = driver_points.filter(pl.col("points_last_24m").is_between(9, 10, closed="both"))
    return triggered, warnings


def detect_plate_thresholds(tickets: pl.DataFrame, anchor: date) -> tuple[pl.DataFrame, pl.DataFrame]:
    window = window_start(anchor, 365)
    recent = tickets.filter(pl.col("violation_date") >= window)
    plate_counts = (
        recent.group_by("plate", "license_number")
        .agg(
            pl.len().alias("tickets_last_12m"),
            pl.col("violation_date").max().alias("last_violation_date"),
        )
        .with_columns(pl.col("last_violation_date").dt.month().alias("last_violation_month"))
    )
    triggered = plate_counts.filter(pl.col("tickets_last_12m") >= 16)
    warnings = plate_counts.filter(pl.col("tickets_last_12m").is_between(14, 15, closed="both"))
    return triggered, warnings


def load_prior_alerts(path: Path = PREVIOUS_ALERTS_FILE) -> pl.DataFrame:
    if not path.exists():
        return pl.DataFrame(
            {
                "entity_type": pl.Series([], dtype=pl.Utf8),
                "identifier": pl.Series([], dtype=pl.Utf8),
            }
        )
    return pl.read_csv(path)


def persist_alert_state(triggered_drivers: pl.DataFrame, triggered_plates: pl.DataFrame, path: Path = PREVIOUS_ALERTS_FILE) -> None:
    driver_records = triggered_drivers.select(
        pl.lit("driver").alias("entity_type"),
        pl.col("license_number").alias("identifier"),
    )
    plate_records = triggered_plates.select(
        pl.lit("plate").alias("entity_type"),
        pl.col("plate").alias("identifier"),
    )
    state = pl.concat([driver_records, plate_records])
    state.write_csv(path)


def detect_new_entities(
    triggered: pl.DataFrame, prior_state: pl.DataFrame, key: str, entity_type: str
) -> pl.DataFrame:
    previous = prior_state.filter(pl.col("entity_type") == entity_type)
    return triggered.join(previous, left_on=key, right_on="identifier", how="anti")


def write_csv(path: Path, df: pl.DataFrame) -> None:
    df.write_csv(path)


def compose_email(recipient: str, subject: str, body: str, attachments: list[Path]) -> EmailMessage:
    msg = EmailMessage()
    msg["To"] = recipient
    msg["From"] = "alerts@isa.example"
    msg["Subject"] = subject
    msg.set_content(body)
    for attachment in attachments:
        with attachment.open("rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="text",
                subtype="csv",
                filename=attachment.name,
            )
    return msg


def save_email(msg: EmailMessage, path: Path) -> None:
    with path.open("w") as f:
        f.write(msg.as_string())


def render_dashboard(
    anchor: date,
    driver_table: pl.DataFrame,
    vehicle_table: pl.DataFrame,
    triggered_drivers: pl.DataFrame,
    triggered_plates: pl.DataFrame,
    warning_drivers: pl.DataFrame,
    warning_plates: pl.DataFrame,
    november_driver_count: int,
    november_plate_count: int,
) -> str:
    def _html_table(df: pl.DataFrame) -> str:
        if df.is_empty():
            return "<p>No records.</p>"
        return df.to_pandas().to_html(index=False)

    summary_html = f"""
    <h1>ISA Threshold Monitoring</h1>
    <p>Run date anchor: {anchor}</p>
    <ul>
        <li>Total drivers triggering 11+ points in last 24 months: {len(triggered_drivers)}</li>
        <li>Total plates triggering 16+ tickets in last 12 months: {len(triggered_plates)}</li>
        <li>Drivers triggered in November (last 24 months window): {november_driver_count}</li>
        <li>Plates triggered in November (last 12 months window): {november_plate_count}</li>
    </ul>
    <h2>Drivers table</h2>
    {_html_table(driver_table)}
    <h2>Vehicle table</h2>
    {_html_table(vehicle_table)}
    <h2>Triggered drivers (11+ points / 24 months)</h2>
    {_html_table(triggered_drivers)}
    <h2>Triggered plates (16+ tickets / 12 months)</h2>
    {_html_table(triggered_plates)}
    <h2>Warning drivers (9-10 points)</h2>
    {_html_table(warning_drivers)}
    <h2>Warning plates (14-15 tickets)</h2>
    {_html_table(warning_plates)}
    """
    return """
    <html>
    <body>
    {content}
    </body>
    </html>
    """.format(content=summary_html)


def save_dashboard(html: str, path: Path) -> None:
    path.write_text(html)


def run_pipeline(
    historical_path: Path = DATA_DIR / "historical_tickets.csv",
    update_path: Path = DATA_DIR / "updates_tickets.csv",
) -> None:
    _ensure_output_dirs()
    points = load_points()
    batches = load_ticket_batches([historical_path, update_path])
    tickets = merge_and_score_tickets(batches, points)
    anchor = reference_date(tickets)

    driver_table = build_driver_table(tickets)
    vehicle_table = build_vehicle_table(tickets)

    triggered_drivers, warning_drivers = detect_driver_thresholds(tickets, anchor)
    triggered_plates, warning_plates = detect_plate_thresholds(tickets, anchor)

    november_driver_count = triggered_drivers.filter(pl.col("last_violation_month") == 11).height
    november_plate_count = triggered_plates.filter(pl.col("last_violation_month") == 11).height

    write_csv(OUTPUT_DIR / "drivers_table.csv", driver_table)
    write_csv(OUTPUT_DIR / "vehicle_table.csv", vehicle_table)
    write_csv(OUTPUT_DIR / "triggered_drivers.csv", triggered_drivers)
    write_csv(OUTPUT_DIR / "triggered_plates.csv", triggered_plates)
    write_csv(OUTPUT_DIR / "warning_drivers.csv", warning_drivers)
    write_csv(OUTPUT_DIR / "warning_plates.csv", warning_plates)

    prior_state = load_prior_alerts()
    new_drivers = detect_new_entities(triggered_drivers, prior_state, "license_number", "driver")
    new_plates = detect_new_entities(triggered_plates, prior_state, "plate", "plate")

    write_csv(OUTPUT_DIR / "newly_flagged_drivers.csv", new_drivers)
    write_csv(OUTPUT_DIR / "newly_flagged_plates.csv", new_plates)
    persist_alert_state(triggered_drivers, triggered_plates)

    dashboard_html = render_dashboard(
        anchor,
        driver_table,
        vehicle_table,
        triggered_drivers,
        triggered_plates,
        warning_drivers,
        warning_plates,
        november_driver_count,
        november_plate_count,
    )
    save_dashboard(dashboard_html, OUTPUT_DIR / "dashboard.html")

    email_recipients = ["violator@example.com", "vendor@example.com", "dmv@example.com"]
    attachments = [
        OUTPUT_DIR / "newly_flagged_drivers.csv",
        OUTPUT_DIR / "newly_flagged_plates.csv",
    ]
    subject = "ISA Alert: New drivers and plates triggering thresholds"
    summary_line = (
        f"New drivers: {len(new_drivers)} | New plates: {len(new_plates)} | "
        f"Run anchor: {anchor}"
    )
    body = (
        summary_line
        + "\nAttached are the latest CSV exports for new threshold crossings. "
        "Warning cohorts are available in the dashboard output."
    )
    for recipient in email_recipients:
        msg = compose_email(recipient, subject, body, attachments)
        save_email(msg, OUTPUT_DIR / "emails" / f"{recipient.replace('@', '_at_')}.eml")


if __name__ == "__main__":
    run_pipeline()
