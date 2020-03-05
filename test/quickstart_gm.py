# from __future__ import print_function
# import pickle
# import os.path
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
# import json
#
# # If modifying these scopes, delete the file token.user.
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
#
#
# # function authGmail() => token(credentials)
# # from file or from response oauth google
# # todo: save JSON credentials in db and get from db when exist
# def auth_gmail() -> object:
#     creds = None
#
#     # The file token.user stores the user's access and refresh tokens, and is
#     # created automatically when the authorization flow completes for the first
#     # time.
#     if os.path.exists('token.user'):
#         with open('token.user', 'rb') as token:
#             creds = pickle.load(token)
#
#     # If there are no (valid) credentials available, let the user log in.
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 'credentials.json', SCOPES)
#             creds = flow.run_local_server(port=0)
#
#         # Save the credentials for the next run
#         with open('token.user', 'wb') as token:
#             pickle.dump(creds, token)
#
#     return creds
#
#
# def main():
#     """
#     Shows basic usage of the Gmail API.
#     POLLING(LISTENING) GMAIL LETTERS
#     """
#     creds = auth_gmail()
#
#
# if __name__ == '__main__':
#     main()
