"""Wrapper for Google OAuth2 API."""
import googleapiclient.discovery
import oauth2client.client
from oauth2client.file import Storage

from . import console
from . import browser

def _get_credentials_interactively(flow, storage, get_code_callback):
    """Return the credentials asking the user."""
    flow.redirect_uri = oauth2client.client.OOB_CALLBACK_URN
    authorize_url = flow.step1_get_authorize_url()
    code = get_code_callback(authorize_url)
    if code:
        credential = flow.step2_exchange(code, http=None)
        storage.put(credential)
        credential.set_store(storage)
        return credential

def get_credentials(client_secrets_file, credentials_file, 
        scope, get_code_callback=console.get_code):
    """Return the user credentials from the file or run the interactive flow."""
    get_flow = oauth2client.client.flow_from_clientsecrets
    flow = get_flow(client_secrets_file, scope=scope)
    storage = oauth2client.file.Storage(credentials_file)
    existing_credentials = storage.get()
    if existing_credentials and not existing_credentials.invalid:
        return existing_credentials
    else:
        return _get_credentials_interactively(flow, storage, get_code_callback)
