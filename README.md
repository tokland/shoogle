# Shoogle

Use the Google API from the shell. An example, get the long URL using the *urlshortener* service:

```shell
$ echo '{"shortUrl": "http://goo.gl/Du5PSN"}' | shoogle execute urlshortener:v1.url.get -
{
  "status": "OK",
  "id": "http://goo.gl/Du5PSN",
  "longUrl": "http://1.bp.blogspot.com/-R0HSXDqlJI8/Tr67i-kr7hI/AAAAAAABMko/gaId6iYuhjA/s1600/12_%252520Cross%252520that%252520bridge%252520when%252520we%252520come%252520to%252520it.jpg",
  "kind": "urlshortener#url"
}
```

## Install

### Dependencies

* Python >= 3.0 

### From PyPi

```shell
$ sudo pip install shoogle
```

### From sources

```shell
$ wget https://github.com/tokland/shoogle/archive/master.zip
$ unzip master.zip
$ cd shoogle-master
$ sudo python setup.py install
```

## Features

* Exposes agnostically all the services in the API.
* Provides infrastructure for the Oauth2 authentication (console or QT/GTK browser).
* Shows information from the Google Discovery API to help build the JSON requests.
* Save credentials for each set of scopes.

## Setup: configure the API and secret keys

* You must enable the services you want to use and create the required keys or secret file in the [API Manager](https://console.developers.google.com/apis/). Each service has its own policies, check the Google documentation for more details.

## Commands

### show

Incrementally show details of services/resources/methods:

```shell
$ shoogle show
adexchangebuyer2:v2beta1 - Ad Exchange Buyer API II
adexchangebuyer:v1.2 - Ad Exchange Buyer API
...
youtubeAnalytics:v1beta1 - YouTube Analytics API
youtubereporting:v1 - YouTube Reporting API
```

```shell
$ shoogle show short
urlshortener:v1 - URL Shortener API
```

```shell
$ shoogle show urlshortener:v1
urlshortener:v1.url
```

```shell
$ shoogle show urlshortener:v1.url
urlshortener:v1.url.get - Expands a short URL or gets creation time and analytics.
urlshortener:v1.url.insert - Creates a new short URL.
urlshortener:v1.url.list - Retrieves a list of URLs shortened by a user.
```

```shell
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

### execute

* Expand a short URL:

```shell
$ cat get-longurl.json 
{
  "key": "YOUR_SECRET_KEY", // You can use JS comments!
  "shortUrl": "http://goo.gl/Du5PSN"
}

$ shoogle execute urlshortener:v1.url.get get-longurl.json
{
  "status": "OK",
  "id": "http://goo.gl/Du5PSN",
  "longUrl": "http://1.bp.blogspot.com/-R0HSXDqlJI8/Tr67i-kr7hI/AAAAAAABMko/gaId6iYuhjA/s1600/12_%252520Cross%252520that%252520bridge%252520when%252520we%252520come%252520to%252520it.jpg",
  "kind": "urlshortener#url"
}
```

* [jq](https://stedolan.github.io/jq/) is a command-line JSON builder/parser. This example shows how to upload a video from a JSON template and extract the ID from the response:

```shell
$ cat upload-video.template.json
{
  "part": "snippet",
  "body": {
    "snippet": {
      "title": $title,
      "description": $description
    }
  }
}
```

```shell
$ jq -n -f upload-video.template.json --arg title "Chess" --arg description "Norway Chess" |
    shoogle execute -c your_client_id.json youtube:v3.videos.insert - -f chess.mp4 |
    jq -r '.id'
wUArz2nPGqA
```
 
## More

* License: [GNU/GPLv3](http://www.gnu.org/licenses/gpl.html).

## Feedback

* Issues: Please open issues only to report bugs of the package. If you have problems regarding how to use the API itself (what auth is required, how to create those auth files, how to build the request parameters, quotas management, etc), use the [Google Forums](https://developers.google.com/groups/) or [StackOverflow](http://stackoverflow.com/questions/tagged/google-api).

* [Want to donate?](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=pyarnau%40gmail%2ecom&lc=US&item_name=youtube%2dupload&no_note=0&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHostedGuest)
