Introduction
============

_shoogle_ is a tool to use the Google API from the command line. It works on any platform -GNU/Linux, BSD, OS X, Windows, ...- that runs Python 3.x.

Install
=======

```
$ wget https://github.com/tokland/shoogle/archive/master.zip
$ unzip master.zip
$ cd shoogle-master
$ sudo python setup.py install
```

Features
========

* Provides infrastructure for Oauth2 authentication (console or QT/GTK browser).
* Exposes all services supported by the Gooogle Python API.
* Inspect the services/resources/method of the API.
* Generates template to send JSON requests.
* Credentials are created/reused depending on the scopes needed.

Notes
=====

* You must enable the APIs you want to use and create the required keys or secret in the [API Manager](https://console.developers.google.com/apis/). Each service has its own policies, check the Google documentation for more details.

Examples
========

* Show details (incrementally) of services/resources/methods:

```
$ shoogle show url
urlshortener:v1 - URL Shortener API
```

```
$ shoogle show urlshortener:v1
urlshortener:v1.url
```

```
$ shoogle show urlshortener:v1.url
urlshortener:v1.url.get - Expands a short URL or gets creation time and analytics.
urlshortener:v1.url.insert - Creates a new short URL.
urlshortener:v1.url.list - Retrieves a list of URLs shortened by a user.
```

```
$ shoogle show urlshortener:v1.url.get
[INFO] Response (level=0, --debug-response-level=N to change):
{
  "$ref": "Url"
}
[INFO] Request (level=1, --debug-request-level=N to change):
{
  "shortUrl": "(string) The short URL, including the protocol - required"
}
```

* Expand a short URL:

```
$ cat get-longurl.json 
{
  "key": "MY_SECRET_KEY", // You can use JS comments!
  "shortUrl": "http://goo.gl/Du5PSN"
}

$ shoogle execute -c your_client_id.json urlshortener:v1.url.get get-longurl.json
{
  "part": "snippet",
  "body": {
    "snippet": {"title": "My great video"}
  }
}
```

* Upload a video:

```
$ cat upload-video.json
{
  "part": "snippet",
  "body": {
    "snippet": {
      "title": "My great video"
    }
  }
}

$ shoogle execute -c your_client_id.json youtube:v3.videos.insert upload-video.json -f video.mp4
{
  "snippet": {
    "channelId": "UCn_xs2hBuoziv_X_4EIeO9Q",
    "categoryId": "22",
    "localized": {
      "title": "My great video",
      "description": ""
    },
  "kind": "youtube#video",
  "id": "OaL345345J0",
  ...
}
```

More
====

* License: [GNU/GPLv3](http://www.gnu.org/licenses/gpl.html).

Feedback
========

* Issues: Please open only issues for bugs of the package. If you have problems regarding how to use the API itself (how to send the auth keys, create the secret files, build the parameters, manage quotas, etc), use the [Google Forums](https://developers.google.com/) or [StackOverflow](http://stackoverflow.com/questions/tagged/google-api) instead.

* [Donations](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=pyarnau%40gmail%2ecom&lc=US&item_name=youtube%2dupload&no_note=0&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHostedGuest).
