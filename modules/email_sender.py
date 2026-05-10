import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from jinja2 import Environment, FileSystemLoader
from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT, DIGEST_MODE


def _render_html(summary: dict, subreddits: list[str]) -> str:
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    template = env.get_template("email.html")
    return template.render(
        summary=summary,
        subreddits=subreddits,
        today=date.today().strftime("%d de %B de %Y"),
    )


def _render_plain(summary: dict, subreddits: list[str]) -> str:
    lines = [f"Reddit Digest — {date.today().strftime('%d/%m/%Y')}", "=" * 40]
    for name in subreddits:
        data = summary.get("subreddits", {}).get(name, {})
        if not data:
            continue
        lines.append(f"\nr/{name}")
        lines.append(f"Temas: {', '.join(data.get('main_themes', []))}")
        lines.append(f"Tendências: {', '.join(data.get('trends', []))}")
        lines.append(f"Sentimento: {data.get('sentiment', 'n/a')}")
    insights = summary.get("cross_subreddit_insights", [])
    if insights:
        lines.append("\nInsights entre subreddits:")
        for i in insights:
            lines.append(f"  - {i}")
    return "\n".join(lines)


def send_digest_email(summary: dict, subreddits: list[str]) -> None:
    today_str = date.today().strftime("%d/%m/%Y")
    label = "Semanal" if DIGEST_MODE == "weekly" else "Diário"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Reddit Digest {label} — {today_str}"
    msg["From"] = GMAIL_SENDER
    msg["To"] = GMAIL_RECIPIENT

    msg.attach(MIMEText(_render_plain(summary, subreddits), "plain", "utf-8"))
    msg.attach(MIMEText(_render_html(summary, subreddits), "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())

    print(f"Email enviado para {GMAIL_RECIPIENT}")
