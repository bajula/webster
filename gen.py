from HTMLParser import HTMLParser
import random
import socket
import sys
import time
import traceback
import urllib2
import urlparse
try:
    import argparse
except ImportError:
    sys.stderr.write("Update python!")
    sys.exit(1)

# Data source
TOP_URL_FILE = "Quantcast-Top-Million.txt"
URLS = []
# Number of links to follow from a page
LINK_DEPTH = 3
# Delays between web pages
MIN_WAIT = 30
MAX_WAIT = 300
# Delays between following links in pages
LINKS_MIN_WAIT = 10
LINKS_MAX_WAIT = 60


class HTMLLinkParser(HTMLParser):
   
    links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr in attrs:
                if attr[0] == "href":
                    self.links.append(attr[1])

    def get_any_link(self):
        if not self.links:
            return ""
        return self.links[len(self.links)/2]


def parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--proxy", help="HTTP proxy address. Format: 192.168.168.1:8080")
    parser.add_argument("-d", "--depth", help="How many links will be visited on each web page. Default is 3", type=int)
    return parser.parse_args()


def verify_proxy(proxy):
    try:
        addr, port = proxy.split(":", 1)
        port = int(port)
        socket.inet_aton(addr)
    except (socket.error, ValueError):
        sys.stderr.write("Invalid proxy address. Should be '<IPv4 address>:<port>' got %s\n" % repr(proxy))
        sys.exit(1)


def verify_url(url):
    if not url:
        raise(urllib2.URLError("Empty URL"))
    parsed = urlparse.urlparse(url, scheme="http")
    if not parsed.netloc and not parsed.path:
        sys.stderr.write("Un-fixable url: %s\n" % repr(url))
        raise(urllib2.URLError("Invalid URL: %s" % repr(url)))
    if not parsed.netloc:
        url = "//www.%s" % url
        parsed = urlparse.urlparse(url, scheme="http")
    return parsed.geturl() 


def init_top_urls():
    with open(TOP_URL_FILE, "r") as fin:
        for line in fin:
            if not line or line.startswith("#"):
                continue
            try:
                rank, url = line.split()
            except ValueError:
                continue
            else:
                URLS.append(url)
            

def get_top_url():
    url_idx = random.randint(0, len(URLS))
    return URLS[url_idx]


def get_web_page(url, depth=0):
    try:
        url = verify_url(url)
        page_data = urllib2.urlopen(url).read()
    except Exception as e:
        return

    sys.stdout.write("GET: %s\t" % url)

    link_parser = HTMLLinkParser()
    try:
        link_parser.feed(page_data)
    except UnicodeError:
        return

    sys.stdout.write("%s links\n" % len(link_parser.links))

    if depth < LINK_DEPTH:
        time.sleep(random.randint(LINKS_MIN_WAIT, LINKS_MAX_WAIT))
        next_hop = link_parser.get_any_link()
        get_web_page(next_hop, depth + 1)


def generate_traffic():
    sys.stdout.write("Infinitely browsing the web, ctrl-c to quit...\n")
    while True:
        try:
            get_web_page(get_top_url())
        except Exception as e:
            sys.stderr.write("\n%s\n" % traceback.format_exc())
            sys.stderr.write("Hackish catch-all caught uncaught exception: %s\n" % e)
        else:
            time.sleep(random.randint(MIN_WAIT, MAX_WAIT))
            sys.stdout.write(".")


def main(args):
    if args.proxy:
        verify_proxy(args.proxy)
        proxy = {"http": args.proxy}
        opener = urllib2.build_opener(urllib2.ProxyHandler(proxy))
        sys.stderr.write("Using proxy: %s\n" % proxy)
    else:
        opener = urllib2.build_opener()
        sys.stderr.write("No web proxy in use\n")
    opener.addheaders = [("User-agent", "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1")]
    urllib2.install_opener(opener)
    init_top_urls()
    generate_traffic()


if __name__ == "__main__":
    cli_args = parse_cli_args()
    main(cli_args)
