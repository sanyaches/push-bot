from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from time import sleep
import datetime
import config

# If modifying these scopes, delete the file token.user.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


# function authGmail() => token(credentials)
# from file or from response oauth google
def auth_gmail() -> object:
    creds = None

    # The file token.user stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.user'):
        with open('token.user', 'rb') as token:
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
        with open('token.user', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def watch_inbox(service):
    request = {
        'labelIds': ['INBOX'],
        'topicName': config.TOPIC_NAME_GMAIL
    }

    result = service.users().watch(userId='me', body=request).execute()
    print(result)


def explicit():
    from google.cloud import storage

    # Explicitly use service account credentials by specifying the private key
    # file.
    storage_client = storage.Client.from_service_account_json(
        'credentials.json')

    # Make an authenticated API request
    buckets = list(storage_client.list_buckets())
    print(buckets)


def receive_messages(project_id, subscription_name, timeout=None):
    """Receives messages from a pull subscription."""
    # [START pubsub_subscriber_async_pull]
    # [START pubsub_quickstart_subscriber]
    from google.cloud import pubsub_v1

    # TODO project_id = "Your Google Cloud Project ID"
    # TODO subscription_name = "Your Pub/Sub subscription name"
    # TODO timeout = 5.0  # "How long the subscriber should listen for
    # messages in seconds"

    subscriber = pubsub_v1.SubscriberClient()
    # The `subscription_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/subscriptions/{subscription_name}`
    subscription_path = subscriber.subscription_path(
        project_id, subscription_name
    )

    def callback(message):
        print("Received message: {}".format(message))
        message.ack()

    streaming_pull_future = subscriber.subscribe(
        subscription_path, callback=callback
    )
    print("Listening for messages on {}..\n".format(subscription_path))

    # result() in a future will block indefinitely if `timeout` is not set,
    # unless an exception is encountered first.
    try:
        streaming_pull_future.result(timeout=timeout)
    except:  # noqa
        streaming_pull_future.cancel()
    # [END pubsub_subscriber_async_pull]
    # [END pubsub_quickstart_subscriber]


def get_messages(service, user_id='me'):
    messages = []
    threads = service.users().threads().list(userId=user_id).execute().get('threads', [])
    for thread in threads:
        thread_data = service.users().threads().get(userId=user_id, id=thread['id']).execute()
        for msg in reversed(thread_data['messages']):
            messages.append(msg)
            if len(messages) == 20:
                return messages
    return messages


def search_diff_messages(old_messages, new_messages):
    diff = []

    for index, new_message in enumerate(new_messages):
        for old_message in old_messages:
            if new_message['id'] == old_message['id']:
                return new_messages[:index]

    return new_messages


# SIMPLE USE SERVICE
def show_chatty_threads(service, user_id='me'):
    threads = service.users().threads().list(userId=user_id).execute().get('threads', [])
    for thread in threads:
        tdata = service.users().threads().get(userId=user_id, id=thread['id']).execute()
        nmsgs = len(tdata['messages'])

        if nmsgs > 1:    # skip if <3 msgs in thread
            msg = tdata['messages'][0]['payload']
            subject = ''
            for header in msg['headers']:
                if header['name'] == 'Subject':
                    subject = header['value']
                    break
            if subject:  # skip if no Subject line
                print('- %s (%d msgs)' % (subject, nmsgs))


def polling_gmail(service):
    old_messages = get_messages(service)

    while True:
        sleep(5)

        new_messages = get_messages(service)

        diff = search_diff_messages(old_messages, new_messages)
        if len(diff) != 0:
            for msg in diff:
                date = datetime.datetime.fromtimestamp(int(msg['internalDate']) / 1000.0)
                print(date, ' Получено новое письмо: ',  msg['snippet'], ' from ', msg['payload']['headers'][16]['value'])

        old_messages = new_messages


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = auth_gmail()

    service = build('gmail', 'v1', credentials=creds)

    polling_gmail(service)


if __name__ == '__main__':
    main()
