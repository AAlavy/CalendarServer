from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI
from flask import request
from api import app
import json
import os

client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY")
)

async def aiEvent(data):
  try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
          {"role": "system", "content": 'You are a scheduling assistant responsible for creating events. In the following format, fill all fields and return it as JSON: {"summary": _, "location": _, "description": _, "start": { "dateTime": _(ISO), "timeZone": _(IANA), }, "end": {  "dateTime": _(ISO, if no end time is provided, an hour after starttime), "timeZone": _(IANA), }, }'},
          {"role": "user", "content": data}
        ]
      )
    return response.choices[0].message.content
  except HttpError as error:
    return f"An error occurred: {error}"


@app.route("/event", methods=["GET"])
def getEvents():
  return "Hello"

@app.route("/event", methods=["POST"])
async def newEvent():
  data = request.get_json(force=True)['eventInvite']
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", [os.getenv("SCOPE_URI")])
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", [os.getenv("SCOPE_URI")]
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)
    response = await aiEvent(data)
  
    # Call the Calendar API
    event = service.events().insert(calendarId='primary', body=json.loads(response)).execute()
    return 'Event created: ' + event.get('htmlLink')

  except HttpError as error:
    return f"An error occurred: {error}"