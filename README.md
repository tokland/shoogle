Introduction
============

_shoogle_ is a tool to use the Google API from the command line. *shoogle* does not know about the details of each API, instead, it uses the Google Discovery API . It works on any platform -GNU/Linux, BSD, OS X, Windows, ...- that runs Python.

Dependencies
============

  * [Python 3.x](http://www.python.org).
  * Packages: [google-api-python-client](https://developers.google.com/api-client-library/python).

```
$ sudo pip install google-api-python-client jsmin httplib2
```

Install
=======

```
$ wget https://github.com/tokland/shoogle/archive/master.zip
$ unzip master.zip
$ cd shoogle-master
$ sudo python setup.py install
```

  * Or run directly from sources:

```
$ bin/shoogle ...
```

Features
========

* Provides infrastructure for Oauth2 authentication (console and browser).
* Exposes all services supported by the Python Gooogle API.

Examples
========

* Show details of services/resources/methods:

```
$ bin/shoogle show url
urlshortener:v1 - URL Shortener API
```

```
$ bin/shoogle show urlshortener:v1
urlshortener:v1.url
```

```
$ bin/shoogle show urlshortener:v1.url
urlshortener:v1.url.get - Expands a short URL or gets creation time and analytics.
urlshortener:v1.url.insert - Creates a new short URL.
urlshortener:v1.url.list - Retrieves a list of URLs shortened by a user.
```

```
$ bin/shoogle show urlshortener:v1.url.get
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
  "key": "MY_API_SECRET_KEY", // You can use JS comments
  "shortUrl": "http://goo.gl/Du5PSN"
}

$ shoogle run -c your_client_id.json urlshortener:v1.url.get get-longurl.json
{
  "part": "snippet",
  "body": {
    "snippet": {"title": "My great video"}
  }
}
```

* Upload a video:

```
$ cat get-longurl.json
{
  "part": "snippet",
  "body": {
    "snippet": {"title": "My great video"}
  }
}

$ shoogle run -c your_client_id.json youtube:v3.videos.insert upload-video.json -f video.mp4
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

* [Donations](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=pyarnau%40gmail%2ecom&lc=US&item_name=youtube%2dupload&no_note=0&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHostedGuest).
