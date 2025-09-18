from __future__ import annotations

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import set_key

from .analysis import list_teams_sorted, find_team_context, fetch_games, compute_summary, persist_outputs
from .plotting import generate_all_charts
from .reporting import ReportBuilder
from .emailer import send_summary_email
from .utils import Settings, logger


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

    @app.route("/", methods=["GET"]) 
    def index():
        teams = list_teams_sorted()
        return render_template("index.html", teams=teams)

    @app.route("/run", methods=["POST"]) 
    def run():
        try:
            team_abbr = request.form.get("team_abbr")
            send_email = request.form.get("send_email") == "on"
            settings = Settings()

            teams_sorted = list_teams_sorted()
            idx = next((i for i, t in enumerate(teams_sorted) if t["abbreviation"].lower() == team_abbr.lower()), None)
            if idx is None:
                flash("Invalid team abbreviation.", "error")
                return redirect(url_for("index"))

            ctx = find_team_context(idx)
            logger.info("Web run: %s (%s)", ctx.name, ctx.abbr)

            # Fetch and persist
            df = fetch_games(ctx.id)
            summary = compute_summary(df)
            persist_outputs(df, summary, ctx.abbr, settings)

            # Generate trend + extended charts
            generate_all_charts(df, ctx.abbr, settings)

            # Update .env context for downstream compatibility
            set_key(".env", "LAST_TEAM_ABBR", ctx.abbr)
            set_key(".env", "LAST_TEAM_NAME", ctx.name)

            # Build PDF
            ReportBuilder(settings).build_pdf(ctx.abbr, ctx.name)

            # Optionally send email
            if send_email:
                send_summary_email(settings, ctx.abbr, ctx.name)
                flash("Pipeline completed and email sent.", "success")
            else:
                flash("Pipeline completed.", "success")
        except Exception as e:
            logger.exception("Web run failed: %s", e)
            flash(f"Error: {e}", "error")
        return redirect(url_for("index"))

    return app
