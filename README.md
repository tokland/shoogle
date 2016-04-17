Introduction
============

_shoogle_ is a tool to use the Google API from the command line. *shoogle* does not know about the details of each API, instead, it uses the Google Discovery API . It works on any platform -GNU/Linux, BSD, OS X, Windows, ...- that runs Python.

Dependencies
============

  * [Python 3.x](http://www.python.org).
  * Packages: [google-api-python-client](https://developers.google.com/api-client-library/python).

```
$ sudo pip install google-api-python-client
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

* Expand a short URL:

```
$ cat > get-longurl.json << EOF
{
  "key": "MY_API_SECRET_KEY", // You can add comments
  "shortUrl": "http://goo.gl/Du5PSN"
}
EOF

$ shoogle run -c client_id.json urlshortener:v1.url.get get-longurl.json
{
  "part": "snippet",
  "body": {
    "snippet": {"title": "My great video"}
  }
}
```

* Upload a video:

```
$ cat > get-longurl.json << EOF
{
  "part": "snippet",
  "body": {
    "snippet": {"title": "My great video"}
  }
}
EOF

$ shoogle run youtube:v3.videos.insert upload-video.json -f video.mp4
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
