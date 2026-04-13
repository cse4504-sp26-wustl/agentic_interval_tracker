"""
Infrastructure: SMTP email sender.

Implements email delivery via SMTP protocol using environment variables
for configuration.
"""

import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional


class SMTPConfigError(Exception):
    """Raised when SMTP configuration is missing or invalid."""
    pass


class EmailSender:
    """
    Sends emails with PDF attachments via SMTP.
    
    Configuration is loaded from environment variables:
    - SMTP_HOST: SMTP server hostname
    - SMTP_PORT: SMTP server port (default: 587)
    - SMTP_USERNAME: Username for authentication
    - SMTP_PASSWORD: Password for authentication
    - SMTP_FROM_EMAIL: From email address (optional, defaults to username)
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self._load_config()
    
    def _load_config(self) -> None:
        """Load and validate SMTP configuration from environment variables."""
        # Support both naming conventions for backwards compatibility
        self.host = os.getenv('SMTP_HOST')
        self.port = int(os.getenv('SMTP_PORT', '587'))
        self.username = os.getenv('SMTP_USERNAME')
        self.password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('SMTP_FROM_EMAIL') or os.getenv('SMTP_SENDER_EMAIL') or self.username
        
        if not all([self.host, self.username, self.password]):
            missing = []
            if not self.host:
                missing.append('SMTP_HOST')
            if not self.username:
                missing.append('SMTP_USERNAME')
            if not self.password:
                missing.append('SMTP_PASSWORD')
            
            raise SMTPConfigError(
                f"Missing required SMTP environment variables: {', '.join(missing)}"
            )
    
    def send_report(
        self, 
        to_email: str, 
        runner_name: str, 
        pdf_path: Path,
        subject: Optional[str] = None,
    ) -> bool:
        """
        Send a PDF report as an email attachment.
        
        Args:
            to_email: Recipient email address
            runner_name: Name of the runner for personalization
            pdf_path: Path to the PDF file to attach
            subject: Email subject (optional, auto-generated if not provided)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not pdf_path.exists():
            print(f"  [!] PDF not found: {pdf_path}")
            return False
        
        if not subject:
            subject = f"Your Interval Training Report - {runner_name}"
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Email body
        body = f"""Hello {runner_name},

Please find attached your latest interval training report.

This report includes your recent workout performance, statistics, and progress tracking.

Best regards,
Interval Training Tracker
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        with open(pdf_path, 'rb') as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
            pdf_attachment.add_header(
                'Content-Disposition', 
                'attachment', 
                filename=pdf_path.name
            )
            msg.attach(pdf_attachment)
        
        if self.dry_run:
            print(f"  [DRY RUN] Would send email to {to_email} with attachment {pdf_path.name}")
            return True
        
        try:
            # Send email
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            print(f"  [✓] Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"  [!] Failed to send email to {to_email}: {str(e)}")
            return False
