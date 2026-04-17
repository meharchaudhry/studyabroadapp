import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

class NotificationService:
    @staticmethod
    def send_otp_email(email: str, otp: str):
        """
        Sends a professional OTP email via SMTP.
        """
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print(f"📧 [MOCK EMAIL] OTP for {email}: {otp} (Set SMTP_USER/PASSWORD to send real emails)")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{otp} is your StudyPathway verification code"
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.SMTP_USER}>"
        msg["To"] = email

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa;">
            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                    <td style="padding: 40px 0;">
                        <table align="center" border="0" cellpadding="0" cellspacing="0" width="400" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden;">
                            <tr>
                                <td align="center" style="padding: 40px 40px 20px 40px; background-color: #7C6FF7;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">StudyPathway</h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px;">
                                    <p style="margin: 0 0 20px 0; font-size: 16px; color: #333333; line-height: 1.5;">Hello,</p>
                                    <p style="margin: 0 0 30px 0; font-size: 16px; color: #555555; line-height: 1.5;">Use the verification code below to complete your registration. This code will expire in 10 minutes.</p>
                                    
                                    <div style="background-color: #f0efff; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 30px;">
                                        <span style="font-size: 36px; font-weight: 800; color: #1a1a1a; letter-spacing: 8px;">{otp}</span>
                                    </div>
                                    
                                    <p style="margin: 0; font-size: 14px; color: #888888; text-align: center;">If you didn't request this code, you can safely ignore this email.</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 20px; background-color: #fafbfc; text-align: center;">
                                    <p style="margin: 0; font-size: 12px; color: #aaaaaa;">&copy; 2026 StudyPathway. All rights reserved.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USER, email, msg.as_string())
            print(f"✅ OTP email successfully sent to {email}")
        except Exception as e:
            print(f"❌ Failed to send OTP email: {str(e)}")
            # For local debugging, we still print the OTP if it fails
            print(f"⚠️  OTP for {email} was: {otp}")

notification_service = NotificationService()
