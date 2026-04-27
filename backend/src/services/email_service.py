"""
Email Service — sends campaign results via Gmail SMTP.

Adapts the logic from send-gmail.ts to Python using the standard library's
smtplib and email modules. Sends HTML emails with .docx attachments.
Includes top-3 tweets with generated comments when available.
"""

from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List

from src.models.campaign import Campaign, Tweet
from src.models.tweet_analysis import TweetAnalysis
from src.models.tweet_comment import TweetComment
from src.core.logging_config import get_logger

logger = get_logger("services.email_service")

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


class EmailService:
    """Sends emails via Gmail SMTP with attachments."""

    def __init__(self, sender_email: str, smtp_password: str) -> None:
        self._sender = sender_email
        self._password = smtp_password

    # ─── Public API ──────────────────────────────────────────────────────────

    def send_campaign_results(
        self,
        recipient: str,
        campaign: Campaign,
        document_path: str,
        top_tweets: Optional[List[Tweet]] = None,
        top_analyses: Optional[List[TweetAnalysis]] = None,
        top_comments: Optional[List[TweetComment]] = None,
    ) -> None:
        """
        Send an email with the campaign results document attached.

        When top_tweets, top_analyses, and top_comments are provided the email
        body includes a formatted section with the top-3 tweets and their
        generated comments.

        Raises RuntimeError on SMTP failures.
        """
        msg = self.create_message(recipient, campaign, top_tweets, top_analyses, top_comments)
        self._attach_document(msg, document_path)

        try:
            with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
                server.starttls()
                server.login(self._sender, self._password)
                server.send_message(msg)
            logger.info("Email sent to %s for campaign %s", recipient, campaign.id)
        except smtplib.SMTPAuthenticationError as exc:
            logger.error("SMTP authentication failed: %s", exc)
            raise RuntimeError("SMTP authentication failed — check credentials") from exc
        except smtplib.SMTPException as exc:
            logger.error("SMTP error: %s", exc)
            raise RuntimeError(f"Failed to send email: {exc}") from exc

    # ─── Message construction ─────────────────────────────────────────────────

    def create_message(
        self,
        recipient: str,
        campaign: Campaign,
        top_tweets: Optional[List[Tweet]] = None,
        top_analyses: Optional[List[TweetAnalysis]] = None,
        top_comments: Optional[List[TweetComment]] = None,
    ) -> MIMEMultipart:
        """
        Create the email message with subject and HTML body.

        Includes a top-3 tweets section when the relevant data is provided.
        """
        msg = MIMEMultipart()
        msg["From"] = self._sender
        msg["To"] = recipient
        msg["Subject"] = f"🚀 Twitter Scraping: {campaign.results_count} Approved Results"

        top_section = self._build_top_tweets_html(top_tweets, top_analyses, top_comments)

        body_html = f"""
        <html>
          <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px;">
              <h2 style="color: #1DA1F2;">🐦 Twitter Scraping Campaign - Results Ready</h2>
              <p>Hello! Your campaign has been successfully completed.</p>
              <p><strong>Campaign:</strong> {campaign.name}</p>
              <p><strong>Total results:</strong> {campaign.results_count} tweets</p>
              <p><strong>Status:</strong> {campaign.status.value.upper()}</p>
              <p><strong>Completed:</strong> {campaign.completed_at.strftime('%Y-%m-%d %H:%M UTC') if campaign.completed_at else 'N/A'}</p>

              {top_section}

              <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">

              <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <p style="margin: 0;"><strong>📎 Attachment:</strong> All {campaign.results_count} tweets are in the attached Word file.</p>
              </div>

              <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">

              <p><strong>Next steps:</strong></p>
              <ul style="line-height: 1.8;">
                <li>Review the tweets in the attachment</li>
                <li>Access the platform to see detailed results</li>
                <li>Download the document from your dashboard</li>
              </ul>

              <small style="color: #999;">Twitter Scraping SaaS Platform | Automated Tweet Collection</small>
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(body_html, "html"))
        return msg

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _build_top_tweets_html(
        self,
        top_tweets: Optional[List[Tweet]],
        top_analyses: Optional[List[TweetAnalysis]],
        top_comments: Optional[List[TweetComment]],
    ) -> str:
        """Return an HTML block for the top-3 tweets section, or empty string."""
        if not top_tweets:
            return ""

        # Build lookup maps
        analysis_map = {a.tweet_id: a for a in (top_analyses or [])}
        comment_map = {c.tweet_id: c for c in (top_comments or [])}

        items_html = ""
        for i, tweet in enumerate(top_tweets[:3], 1):
            analysis = analysis_map.get(tweet.id)
            comment = comment_map.get(tweet.id)

            score_badge = ""
            if analysis:
                color = "#28a745" if analysis.verdict.value == "APPROVED" else "#dc3545"
                score_badge = (
                    f'<span style="background:{color};color:#fff;padding:2px 8px;'
                    f'border-radius:12px;font-size:12px;margin-left:8px;">'
                    f'{analysis.verdict.value} — {analysis.average_score:.1f}/10</span>'
                )

            comment_block = ""
            if comment:
                comment_block = f"""
                <div style="background:#e8f4fd;border-left:3px solid #1DA1F2;padding:10px;margin-top:8px;border-radius:4px;">
                  <strong style="font-size:11px;color:#1DA1F2;text-transform:uppercase;">Generated Comment</strong>
                  <p style="margin:6px 0 0;font-size:14px;">{comment.comment_text}</p>
                  <small style="color:#888;">{comment.char_count} characters</small>
                </div>
                """

            items_html += f"""
            <div style="border:1px solid #e0e0e0;border-radius:8px;padding:15px;margin-bottom:12px;">
              <div style="margin-bottom:6px;">
                <strong>#{i} @{tweet.author}</strong>{score_badge}
                <span style="color:#888;font-size:12px;margin-left:8px;">
                  ❤️ {tweet.likes}  🔁 {tweet.reposts}  💬 {tweet.replies}
                </span>
              </div>
              <p style="margin:0 0 8px;color:#333;">{tweet.text}</p>
              <a href="{tweet.url}" style="font-size:12px;color:#1DA1F2;">Ver no Twitter ↗</a>
              {comment_block}
            </div>
            """

        return f"""
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <h3 style="color:#333;">⭐ Top 3 Tweets</h3>
        {items_html}
        """

    def _attach_document(self, msg: MIMEMultipart, file_path: str) -> None:
        """Attach a .docx file to the email message."""
        if not os.path.exists(file_path):
            logger.warning("Document file not found: %s", file_path)
            return

        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={filename}",
        )
        msg.attach(part)
        logger.debug("Attached document: %s", filename)
