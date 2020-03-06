import pickle

from googleapiclient.discovery import build
from datetime import datetime


class GmailStatistics:

    def __init__(self, gm_credentials, chat_id):
        self.chat_id = chat_id
        self.credentials = pickle.loads(gm_credentials)

    def by_date(self, date, user_id='me'):
        service = build('gmail', 'v1', credentials=self.credentials)

        conversations_statistics = {}

        threads = service.users().threads().list(userId=user_id).execute().get('threads', [])
        for thread in threads:
            tdata = service.users().threads().get(userId=user_id, id=thread['id']).execute()
            nmsgs = len(tdata['messages'])

            if nmsgs > 0:  # skip if <3 msgs in thread
                msg = tdata['messages'][0]['payload']
                subject = ''
                msg_date = datetime.fromtimestamp(int(tdata['messages'][0]['internalDate']) / 1000.0)
                for header in msg['headers']:
                    if header['name'] == 'Subject':
                        subject = header['value']
                        break
                if subject and msg_date >= date:  # skip if no Subject line and date < msg_date
                    conversations_statistics[subject] = nmsgs
        return "\n".join("{!s} : {!r}".format(key, val) for (key, val) in conversations_statistics.items())
