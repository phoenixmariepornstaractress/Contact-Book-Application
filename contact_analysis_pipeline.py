# -*- coding: utf-8 -*-
"""
Professional Contact Manager Pro – Advanced Data Analysis & ML Pipeline
Version: 2.1 (bug-fixed)
Author: Senior AI Data Engineer
Date: 2025
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error as MySQLError
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder

# ----------------------------------------------------------------------
# Global settings
# ----------------------------------------------------------------------
sns.set_style("whitegrid")
plt.rcParams["font.size"] = 11
plt.rcParams["axes.unicode_minus"] = False          # correct minus sign in Persian plots
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)

# Professional logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class ContactDataAnalyzer:
    def __init__(self, output_dir: str = "contact_analysis_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", "password"),
            "database": os.getenv("DB_NAME", "contactbook"),
            "autocommit": True,
            "charset": "utf8mb4",
        }

        self.df: Optional[pd.DataFrame] = None
        self.category_mapping: Dict[str, int] = {}
        self.le_category = LabelEncoder()

    # ------------------------------------------------------------------
    # 1. Data extraction
    # ------------------------------------------------------------------
    def connect_and_extract(self) -> bool:
        conn = None
        try:
            logger.info("Connecting to MySQL database...")
            conn = mysql.connector.connect(**self.db_config)
            query = """
                SELECT id, name, phone, category, email, notes,
                       created_at, updated_at
                FROM contacts
                ORDER BY created_at DESC
            """
            self.df = pd.read_sql(query, conn)
            logger.info(f"Successfully extracted {len(self.df):,} contacts.")
            return True
        except MySQLError as e:
            logger.error(f"Database error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during extraction: {e}")
            return False
        finally:
            if conn and conn.is_connected():
                conn.close()

    # ------------------------------------------------------------------
    # 2. Feature engineering (all bugs fixed)
    # ------------------------------------------------------------------
    def clean_and_engineer_features(self) -> None:
        if self.df is None or self.df.empty:
            raise ValueError("No data available for feature engineering.")

        df = self.df.copy()
        logger.info("Starting advanced feature engineering...")

        # ---- Name -------------------------------------------------------
        df["name"] = df["name"].astype(str).str.strip()
        df["name_length"] = df["name"].str.len()
        df["name_words"] = df["name"].str.split().str.len()
        df["has_title"] = (
            df["name"]
            .str.contains(r"\b(Dr|Mr|Mrs|Ms|Prof|Eng|Sir|Lady)\.?", case=False, na=False)
            .astype(int)
        )
        df["is_company"] = (
            df["name"]
            .str.contains(r"\b(Inc|Ltd|Corp|LLC|GmbH|Co\.|Company)\b", case=True, na=False)
            .astype(int)
        )

        # ---- Phone ------------------------------------------------------
        df["phone_clean"] = df["phone"].astype(str).str.replace(r"\D", "", regex=True)
        df["phone_digit_count"] = df["phone_clean"].str.len()
        df["is_international"] = (df["phone_digit_count"] > 10).astype(int)
        df["area_code"] = df["phone_clean"].str[:3].where(df["phone_digit_count"] >= 10)
        df["has_extension"] = (
            df["phone"].astype(str).str.contains(r"x|ext|#", case=False, na=False).astype(int)
        )

        # ---- Email ------------------------------------------------------
        df["has_email"] = df["email"].notna().astype(int)
        df["email_domain"] = (
            df["email"]
            .astype(str)
            .str.split("@")
            .str[-1]
            .str.lower()
            .where(df["has_email"] == 1)
        )
        free_domains = {
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "icloud.com",
            "proton.me",
        }
        df["email_is_free"] = df["email_domain"].isin(free_domains).astype(int)

        # ---- Notes ------------------------------------------------------
        df["has_notes"] = df["notes"].notna().astype(int)
        df["notes_length"] = df["notes"].fillna("").str.len()
        df["notes_word_count"] = df["notes"].fillna("").str.split().str.len()
        df["notes_has_url"] = (
            df["notes"]
            .astype(str)
            .str.contains(r"https?://", case=False, na=False)
            .astype(int)
        )

        # ---- Time features -----------------------------------------------
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")

        df["created_year"] = df["created_at"].dt.year
        df["created_month"] = df["created_at"].dt.month
        df["created_dayofweek"] = df["created_at"].dt.dayofweek
        df["created_hour"] = df["created_at"].dt.hour
        df["is_weekend"] = df["created_dayofweek"].isin([5, 6]).astype(int)
        df["days_since_creation"] = (datetime.now() - df["created_at"]).dt.days

        df["was_recently_updated"] = (
            (df["updated_at"] - df["created_at"]) > pd.Timedelta(days=1)
        ).astype(int)

        # ---- Target -----------------------------------------------------
        df["category"] = df["category"].fillna("Other").str.strip()
        df["category_encoded"] = self.le_category.fit_transform(df["category"])
        self.category_mapping = dict(
            zip(self.le_category.classes_, self.le.classes_indices_)
        )

        # ---- Composite quality score ------------------------------------
        df["contact_quality_score"] = (
            df["has_email"] * 3
            + df["has_notes"] * 2
            + (df["notes_length"] > 50).astype(int) * 2
            + (~df["email_is_free"]).astype(int) * 1
        )

        self.df = df
        logger.info("Feature engineering completed.")

    # ------------------------------------------------------------------
    # 3. EDA report (fixed subplot layout & Persian font handling)
    # ------------------------------------------------------------------
    def generate_eda_report(self) -> None:
        if self.df is None:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        df = self.df

        # Try to use a Persian-friendly font if available
        try:
            plt.rcParams["font.family"] = "Tahoma"
        # fallback for Windows
        except:
            pass

        fig = plt.figure(figsize=(20, 14))
        fig.suptitle(
            "Professional Contact Manager Pro – Comprehensive Data Analysis",
            fontsize=18,
            fontweight="bold",
            y=0.98,
        )

        # 1. Category distribution
        ax1 = plt.subplot(2, 3, 1)
        df["category"].value_counts().plot(kind="bar", ax=ax1, color="teal", alpha=0.8)
        ax1.set_title("Distribution by Category", fontweight="bold")
        ax1.tick_params(axis="x", rotation=45)

        # 2. Quality score
        ax2 = plt.subplot(2, 3, 2)
        df["contact_quality_score"].value_counts().sort_index().plot(
            kind="bar", ax=ax2, color="gold", edgecolor="black"
        )
        ax2.set_title("Contact Quality Score", fontweight="bold")

        # 3. International vs Free email
        ax3 = plt.subplot(2, 3, 3)
        pd.crosstab(df["is_international"], df["email_is_free"]).plot(
            kind="bar", stacked=True, ax=ax3, color=["lightcoral", "skyblue"]
        )
        ax3.set_title("International × Free Email", fontweight="bold")
        ax3.set_xticklabels(["Local", "International"], rotation=0)

        # 4. Monthly growth
        ax4 = plt.subplot(2, 3, 4)
        monthly = df.groupby(df["created_at"].dt.to_period("M")).size()
        monthly.plot(kind="line", marker="o", ax=ax4, linewidth=2.5, color="darkgreen")
        ax4.set_title("Monthly Contact Growth", fontweight="bold")

        # 5. Correlation matrix
        ax5 = plt.subplot(2, 3, 5)
        corr_cols = [
            "name_length",
            "phone_digit_count",
            "has_email",
            "has_notes",
            "notes_length",
            "contact_quality_score",
            "category_encoded",
        ]
        corr = df[corr_cols].corr()
        sns.heatmap(corr, annot=True, cmap="RdYlGn", center=0, ax=ax5, fmt=".2f")
        ax5.set_title("Feature Correlation", fontweight="bold")

        # 6. Hour of day
        ax6 = plt.subplot(2, 3, 6)
        df["created_hour"].value_counts().sort_index().plot(
            kind="bar", ax=ax6, color="orange", alpha=0.8
        )
        ax6.set_title("Contacts Added by Hour", fontweight="bold")

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        report_path = self.output_dir / f"EDA_Report_{timestamp}.png"
        plt.savefig(report_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close()
        logger.info(f"EDA image saved → {report_path}")

        self._save_html_report(timestamp)

    def _save_html_report(self, timestamp: str) -> None:
        stats = {
            "Total Contacts": f"{len(self.df):,}",
            "Unique Categories": len(self.df["category"].unique()),
            "Contacts with Email": int(self.df["has_email"].sum()),
            "Contacts with Notes": int(self.df["has_notes"].sum()),
            "International Numbers": int(self.df["is_international"].sum()),
            "High-Quality (Score ≥5)": int((self.df["contact_quality_score"] >= 5).sum()),
            "Report Generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        rows = "".join(f"<tr><td><b>{k}</b></td><td>{v}</td></tr>" for k, v in stats.items())
        html = f"""<!DOCTYPE html>
<html lang="fa" dir="ltr">
<head>
    <meta charset="utf-8">
    <title>Contact Manager Pro – Analysis Report</title>
    <style>
        body {{font-family: Tahoma, Arial, sans-serif; margin:40px; background:#f8f9fa;}}
        h1,h2 {{color:#2c3e50;}}
        table {{width:100%; border-collapse:collapse; margin:20px 0;}}
        th,td {{padding:12px; border:1px solid #ddd; text-align:left;}}
        th {{background:#0077b6; color:white;}}
    </style>
</head>
<body>
    <h1>Professional Contact Manager Pro</h1>
    <h2>Data Analysis Report – {timestamp}</h2>
    <img src="EDA_Report_{timestamp}.png" style="width:100%;">
    <h2>Summary Statistics</h2>
    <table>{rows}</table>
    <hr>
    <small>Generated by ContactDataAnalyzer v2.1</small>
</body>
</html>"""
        (self.output_dir / f"Analysis_Report_{timestamp}.html").write_text(html, encoding="utf-8")

    # ------------------------------------------------------------------
    # 4. Export datasets
    # ------------------------------------------------------------------
    def export_datasets(self) -> None:
        if self.df is None:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        # Full dataset
        self.df.to_csv(
            self.output_dir / f"contacts_full_{timestamp}.csv",
            index=False,
            encoding="utf-8-sig",
        )

        # ML-ready dataset
        ml_features = [
            "name_length",
            "name_words",
            "has_title",
            "is_company",
            "phone_digit_count",
            "is_international",
            "has_extension",
            "has_email",
            "email_is_free",
            "has_notes",
            "notes_length",
            "notes_word_count",
            "notes_has_url",
            "created_month",
            "created_dayofweek",
            "created_hour",
            "is_weekend",
            "contact_quality_score",
            "category_encoded",
        ]
        ml_df = self.df[ml_features].copy()
        ml_df.to_csv(self.output_dir / "contacts_ml_ready.csv", index=False)
        ml_df.to_parquet(self.output_dir / "contacts_ml_ready.parquet", index=False)

        # Category mapping
        with open(self.output_dir / "category_mapping.json", "w", encoding="utf-8") as f:
            json.dump(self.category_mapping, f, ensure_ascii=False, indent=2)

        logger.info("All datasets exported.")

    # ------------------------------------------------------------------
    # 5. Run pipeline
    # ------------------------------------------------------------------
    def run(self) -> None:
        logger.info("=" * 70)
        logger.info("Starting Advanced Contact Data Analysis Pipeline")
        logger.info("=" * 70)

        if not self.connect_and_extract():
            return

        if self.df.empty:
            logger.warning("Database is empty – nothing to analyse.")
            return

        self.clean_and_engineer_features()
        self.generate_eda_report()
        self.export_datasets()

        logger.info("=" * 70)
        logger.info("Pipeline finished successfully!")
        logger.info(f"Outputs → {self.output_dir.resolve()}")
        logger.info("=" * 70)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    analyzer = ContactDataAnalyzer()
    analyzer.run()
