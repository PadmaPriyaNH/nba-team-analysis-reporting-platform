from __future__ import annotations

import os
from datetime import datetime
from typing import List

import pandas as pd
from fpdf import FPDF

from .utils import Settings, logger


class ReportBuilder:
    def __init__(self, settings: Settings):
        self.settings = settings

    def build_pdf(self, team_abbr: str | None = None, team_name: str | None = None,
                  summary_file: str | None = None, plots_dir: str | None = None,
                  output_path: str | None = None) -> str | None:
        team_abbr = team_abbr or self.settings.last_team_abbr
        team_name = team_name or self.settings.last_team_name
        plots_dir = plots_dir or self.settings.plots_dir
        output_path = output_path or os.path.join(self.settings.reports_dir, f"{team_abbr}_report.pdf")
        summary_file = summary_file or os.path.join(self.settings.data_dir, f"{team_abbr}_summary.csv")

        # Load summary
        try:
            summary = pd.read_csv(summary_file, index_col=0).squeeze("columns")
        except FileNotFoundError:
            logger.error("Summary file not found: %s", summary_file)
            return None

        # Collect plots
        graph_files: List[str] = []
        if os.path.isdir(plots_dir):
            for f in os.listdir(plots_dir):
                if f.startswith(team_abbr) and f.lower().endswith((".png", ".jpg", ".jpeg")):
                    graph_files.append(os.path.join(plots_dir, f))
        graph_files.sort()
        if not graph_files:
            logger.warning("No graphs found for %s in %s", team_abbr, plots_dir)
            return None

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_author("N H Padma Priya")
        pdf.set_title(f"{team_name} Weekly Report")
        pdf.add_page()
        try:
            pdf.set_font("Arial", "B", 20)
        except Exception:
            pdf.set_font("helvetica", "B", 20)
        pdf.set_text_color(0, 102, 204)
        pdf.cell(0, 10, f"{team_name} Weekly Report", ln=True, align="C")

        try:
            pdf.set_font("Arial", "", 12)
        except Exception:
            pdf.set_font("helvetica", "", 12)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, datetime.now().strftime("Date: %B %d, %Y"), ln=True, align="C")
        pdf.ln(8)

        pdf.set_text_color(0, 0, 0)
        for key, value in summary.items():
            try:
                pdf.set_font("Arial", "B", 12)
            except Exception:
                pdf.set_font("helvetica", "B", 12)
            pdf.cell(50, 10, f"{key}:", ln=0)
            try:
                pdf.set_font("Arial", "", 12)
            except Exception:
                pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 10, str(value), ln=1)

        pdf.ln(5)

        first_chart = next((g for g in graph_files if "trend" in g.lower()), graph_files[0])
        if os.path.exists(first_chart):
            try:
                pdf.set_font("Arial", "B", 12)
            except Exception:
                pdf.set_font("helvetica", "B", 12)
            pdf.cell(0, 10, "Scoring Trend Chart:", ln=True)
            pdf.image(first_chart, x=10, w=190)
        pdf.ln(5)

        for g in graph_files:
            if g == first_chart:
                continue
            pdf.add_page()
            try:
                pdf.set_font("Arial", "B", 14)
            except Exception:
                pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, os.path.basename(g), ln=True)
            pdf.image(g, x=10, w=190)

        pdf.output(output_path)
        logger.info("PDF report generated with %d charts → %s", len(graph_files), output_path)
        return output_path
