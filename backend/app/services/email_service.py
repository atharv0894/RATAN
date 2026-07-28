import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.environ.get("RESEND_API")

class EmailService:
    @staticmethod
    def send_verification_email(to_email: str, token: str):
        # We assume the frontend runs on localhost:3000 for local dev or the deployed Vercel domain.
        # In a real setup, this would be an env var. For this task, we will use a relative URL or fallback to localhost if not specified.
        # But we need an absolute URL for emails.
        domain = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        
        # If the domain is just a vercel domain without https, we could format it, but usually FRONTEND_URL is full.
        verification_url = f"{domain}/personal/verify-email?token={token}"

        html_content = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
            <h2 style="color: #2563EB;">Verify your RATAN account</h2>
            <p>Welcome to RATAN!</p>
            <p>Please verify your email address by clicking the button below.</p>
            <div style="margin: 30px 0;">
                <a href="{verification_url}" style="background-color: #2563EB; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Verify Email</a>
            </div>
            <p>If you didn't create this account, you can safely ignore this email.</p>
            <p style="font-size: 12px; color: #666; margin-top: 40px;">This verification link expires in 24 hours.</p>
        </div>
        """

        if not os.environ.get("RESEND_API"):
            print("Warning: RESEND_API key not found. Email not sent.")
            return False
            
        try:
            params = {
                "from": "RATAN <onboarding@resend.dev>",
                "to": [to_email],
                "subject": "Verify your RATAN account",
                "html": html_content,
            }
            email = resend.Emails.send(params)
            return True
        except Exception as e:
            print(f"Failed to send verification email (likely due to Resend free tier restrictions): {e}")
            return False
