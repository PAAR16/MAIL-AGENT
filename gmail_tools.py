# gmail_tools.py (Corrected Version)

import os
import base64
from email.message import EmailMessage  # <-- Important new import

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly", # Read emails
    "https://www.googleapis.com/auth/gmail.compose"   # Draft and send emails
]
TOKEN_PATH = "token.json"
CREDENTIALS_PATH = "credentials.json"

def get_gmail_service():
    """Authenticates with Google and returns a Gmail service object."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
            
    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def list_last_n_mails(n=5):
    """Lists the subject, sender, and snippet of the last N emails."""
    service = get_gmail_service()
    if not service: return "Could not connect to Gmail."

    try:
        results = service.users().messages().list(userId="me", maxResults=n).execute()
        messages = results.get("messages", [])
        
        if not messages:
            return "No messages found."

        email_list = []
        for message in messages:
            msg = service.users().messages().get(userId="me", id=message["id"], format="metadata").execute()
            headers = msg["payload"]["headers"]
            subject = next((header["value"] for header in headers if header["name"] == "Subject"), "No Subject")
            sender = next((header["value"] for header in headers if header["name"] == "From"), "Unknown Sender")
            email_list.append(f"From: {sender}\nSubject: {subject}\nSnippet: {msg['snippet']}\n---")
        
        return "\n".join(email_list)
    except HttpError as error:
        return f"An error occurred: {error}"

def search_and_group_mails(keywords_str="job opening,hr,university"):
    """Searches for emails containing keywords and groups them."""
    # (This function remains the same, no changes needed)
    service = get_gmail_service()
    if not service: return "Could not connect to Gmail."
    
    keywords = [k.strip() for k in keywords_str.split(',')]
    grouped_results = {}

    for keyword in keywords:
        try:
            results = service.users().messages().list(userId="me", q=keyword, maxResults=5).execute()
            messages = results.get("messages", [])
            
            if messages:
                keyword_results = []
                for message in messages:
                    msg = service.users().messages().get(userId="me", id=message["id"], format="metadata").execute()
                    subject = next((h["value"] for h in msg["payload"]["headers"] if h["name"] == "Subject"), "No Subject")
                    sender = next((h["value"] for h in msg["payload"]["headers"] if h["name"] == "From"), "Unknown Sender")
                    keyword_results.append(f"  - From: {sender}, Subject: {subject}")
                grouped_results[keyword] = "\n".join(keyword_results)
            else:
                grouped_results[keyword] = "  - No recent messages found."

        except HttpError as error:
            grouped_results[keyword] = f"An error occurred while searching: {error}"
    
    output = ""
    for keyword, results in grouped_results.items():
        output += f"Results for '{keyword}':\n{results}\n\n"
    return output.strip()


# --- THIS IS THE CORRECTED FUNCTION ---
def draft_email(to: str, subject: str, body: str) -> str:
    """Creates and saves a draft email in the user's Gmail account."""
    service = get_gmail_service()
    if not service:
        return "Could not connect to Gmail."
    
    try:
        # Create a proper email message object
        message = EmailMessage()
        message.set_content(body)
        message["To"] = to
        message["Subject"] = subject
        
        # Encode the message in a way the Gmail API understands
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        create_message_request = {
            'message': {
                'raw': encoded_message
            }
        }
        
        # This is the actual API call that creates the draft
        draft = service.users().drafts().create(
            userId='me',
            body=create_message_request
        ).execute()
        
        return f"Success! A draft has been created for '{to}' with subject '{subject}'. Please check your Drafts folder in Gmail to review and send it."

    except HttpError as error:
        return f"An error occurred while creating the draft: {error}"
    except Exception as e:
        return f"A general error occurred: {e}"