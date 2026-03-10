"""Email service — sends transactional emails via SMTP."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_smtp_connection() -> smtplib.SMTP:
    """Create and return an SMTP connection."""
    smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
    if settings.SMTP_USE_TLS:
        smtp.starttls()
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    return smtp


def send_email(*, to: str, subject: str, html_body: str) -> None:
    """Send an email. Logs and swallows errors so callers aren't blocked."""
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM_EMAIL}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        with _get_smtp_connection() as smtp:
            smtp.send_message(msg)
        logger.info("Email sent to %s — %s", to, subject)
    except Exception:
        logger.exception("Failed to send email to %s", to)


def send_invite_email(
    *,
    to_email: str,
    org_name: str,
    inviter_name: str,
    role: str,
    token: str,
) -> None:
    """Send an organisation invite email with a clickable accept link."""
    accept_url = f"{settings.FRONTEND_URL}/invite/{token}"

    html = f"""\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
</head>
<body style="margin:0;padding:0;background-color:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5;padding:40px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td style="background-color:#18181b;padding:24px 32px;">
              <h1 style="margin:0;color:#ffffff;font-size:20px;font-weight:600;">Tenantrix</h1>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              <h2 style="margin:0 0 8px;color:#18181b;font-size:18px;font-weight:600;">You're invited!</h2>
              <p style="margin:0 0 24px;color:#71717a;font-size:14px;line-height:1.6;">
                <strong style="color:#18181b;">{inviter_name}</strong> has invited you to join
                <strong style="color:#18181b;">{org_name}</strong> as a <strong style="color:#18181b;">{role}</strong>.
              </p>
              <!-- CTA Button -->
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 24px;">
                <tr>
                  <td style="background-color:#18181b;border-radius:8px;">
                    <a href="{accept_url}"
                       style="display:inline-block;padding:12px 32px;color:#ffffff;font-size:14px;font-weight:600;text-decoration:none;">
                      Accept Invitation
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin:0 0 8px;color:#a1a1aa;font-size:12px;line-height:1.5;">
                Or copy and paste this link into your browser:
              </p>
              <p style="margin:0 0 24px;color:#3b82f6;font-size:12px;word-break:break-all;">
                <a href="{accept_url}" style="color:#3b82f6;text-decoration:none;">{accept_url}</a>
              </p>
              <hr style="border:none;border-top:1px solid #e4e4e7;margin:24px 0;" />
              <p style="margin:0;color:#a1a1aa;font-size:11px;line-height:1.5;">
                This invitation expires in 72 hours. If you didn't expect this email, you can safely ignore it.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color:#fafafa;padding:16px 32px;border-top:1px solid #e4e4e7;">
              <p style="margin:0;color:#a1a1aa;font-size:11px;text-align:center;">
                &copy; Tenantrix &mdash; Project Management Platform
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    send_email(
        to=to_email,
        subject=f"{inviter_name} invited you to join {org_name} on Tenantrix",
        html_body=html,
    )
