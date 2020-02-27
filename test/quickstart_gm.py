from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


# function authGmail() => token(credentials)
# from file or from response oauth google
def auth_gmail() -> object:
    creds = None

    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def watch_inbox(service):
    request = {
        'labelIds': ['INBOX'],
        'topicName': '*'
    }

    result = service.users().watch(userId='me', body=request).execute()
    print(result)


def show_chatty_threads(service, user_id='me'):
    threads = service.users().threads().list(userId=user_id).execute().get('threads', [])
    for thread in threads:
        tdata = service.users().threads().get(userId=user_id, id=thread['id']).execute()
        nmsgs = len(tdata['messages'])

        if nmsgs > 2:    # skip if <3 msgs in thread
            msg = tdata['messages'][0]['payload']
            subject = ''
            for header in msg['headers']:
                if header['name'] == 'Subject':
                    subject = header['value']
                    break
            if subject:  # skip if no Subject line
                print('- %s (%d msgs)' % (subject, nmsgs))


def show_labels(service):
    # Call the Gmail API
    results = service.users().messages().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = auth_gmail()

    service = build('gmail', 'v1', credentials=creds)

    # show_chatty_threads(service)
    watch_inbox(service)


if __name__ == '__main__':
    main()
