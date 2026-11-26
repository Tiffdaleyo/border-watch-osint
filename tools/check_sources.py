"""Checks which official press-release feeds and pages answer from GitHub (run by the check-sources workflow)."""
import re
import sys
import requests

CANDIDATES = [
    ("US CBP", ["https://www.cbp.gov/rss/newsroom/national-media-release", "https://www.cbp.gov/rss/newsroom/media-releases",
                "https://www.cbp.gov/newsroom/rss-feeds", "https://www.cbp.gov/newsroom/media-releases/all"]),
    ("UK Border Force", ["https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=border-force"]),
    ("UK Home Office", ["https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=home-office"]),
    ("UK NCA", ["https://www.nationalcrimeagency.gov.uk/news?format=feed&type=rss", "https://www.nationalcrimeagency.gov.uk/news"]),
    ("JCF", ["https://jcf.gov.jm/feed/", "https://jcf.gov.jm/category/news/feed/", "https://jcf.gov.jm/"]),
    ("PICA", ["https://www.pica.gov.jm/feed/", "https://www.pica.gov.jm/rss.xml", "https://www.pica.gov.jm/news", "https://www.pica.gov.jm/"]),
    ("Jamaica Customs", ["https://www.jacustoms.gov.jm/feed/", "https://www.jacustoms.gov.jm/rss.xml",
                         "https://www.jacustoms.gov.jm/media/press-releases", "https://www.jacustoms.gov.jm/"]),
    ("JIS", ["https://jis.gov.jm/feed/", "https://jis.gov.jm/category/news/feed/"]),
    ("Frontex", ["https://www.frontex.europa.eu/feed/news-release/", "https://www.frontex.europa.eu/media-centre/news/news-release/rss/",
                 "https://www.frontex.europa.eu/media-centre/news/news-release/"]),
    ("INTERPOL", ["https://www.interpol.int/en/RSS-feeds", "https://www.interpol.int/en/rss/news",
                  "https://www.interpol.int/en/News-and-Events/News"]),
    ("Europol", ["https://www.europol.europa.eu/rss/news", "https://www.europol.europa.eu/rss.xml",
                 "https://www.europol.europa.eu/media-press/newsroom"]),
    ("US ICE", ["https://www.ice.gov/feeds/news.rss", "https://www.ice.gov/rss/news/281", "https://www.ice.gov/newsroom"]),
    ("US DHS", ["https://www.dhs.gov/news-releases/rss.xml", "https://www.dhs.gov/news-releases/press-releases"]),
    ("US DOJ", ["https://www.justice.gov/news/rss?type=press_release", "https://www.justice.gov/feeds/opa/justice-news.xml"]),
    ("CARICOM IMPACS", ["https://caricomimpacs.org/feed/", "https://caricomimpacs.org/news/"]),
    ("UNODC", ["https://www.unodc.org/unodc/en/press/allpress.html", "https://www.unodc.org/unodc/feed/press-releases.xml"]),
    ("IOM", ["https://www.iom.int/rss.xml", "https://www.iom.int/news"]),
    ("US Coast Guard", ["https://www.news.uscg.mil/RSS/", "https://www.news.uscg.mil/Press-Releases/"]),
    ("RCMP", ["https://www.rcmp-grc.gc.ca/en/news/rss", "https://rcmp.ca/en/news"]),
    ("CBSA", ["https://www.canada.ca/en/border-services-agency/news.html",
              "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=canadaborderservicesagency&type=newsreleases&sort=publishedDate&orderBy=desc&pick=50&format=atom&atomtitle=CBSA"]),
]
PAGES = [
    ("Frontex", "https://www.frontex.europa.eu/media-centre/news/news-release/", "/media-centre/news/news-release/"),
    ("US ICE", "https://www.ice.gov/newsroom", "/news/releases/"),
    ("US DHS", "https://www.dhs.gov/news-releases/press-releases", "/news/20"),
    ("UNODC", "https://www.unodc.org/unodc/en/press/allpress.html", "/press/releases/"),
    ("IOM", "https://www.iom.int/news", "/news/"),
    ("PICA", "https://www.pica.gov.jm/news", "/news/"),
    ("CBP page", "https://www.cbp.gov/newsroom/media-releases/all", "/newsroom/"),
]
H = {"User-Agent": "Mozilla/5.0 (compatible; BorderWatchOSINT/1.0; +https://github.com)"}
for name, urls in CANDIDATES:
    for u in urls:
        try:
            r = requests.get(u, headers=H, timeout=25)
            t = r.text
            items = len(re.findall(r"<item[\s>]|<entry[\s>]", t))
            links = len(re.findall(r"<a\s[^>]*href=", t))
            first = re.search(r"<item>.*?<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>|<entry>.*?<title[^>]*>(.*?)</title>", t, re.S)
            ft = (first.group(1) or first.group(2))[:80] if first else ""
            print(f"{name:16} {r.status_code} {r.headers.get('content-type','')[:30]:30} items={items:3} links={links:4} {u}  | {ft}")
        except Exception as e:
            print(f"{name:16} ERR {type(e).__name__} {u}")
    sys.stdout.flush()

print("\n--- pages: links that look like releases ---")
import urllib.parse
for name, url, pat in PAGES:
    try:
        t = requests.get(url, headers=H, timeout=25).text
        found = []
        for m in re.finditer(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', t, re.S):
            href, text = m.group(1), re.sub(r"<[^>]+>|\s+", " ", m.group(2)).strip()
            full = urllib.parse.urljoin(url, href)
            if pat in full and full.rstrip("/") != url.rstrip("/") and 25 <= len(text) <= 220:
                found.append((text[:90], full))
        print(f"{name:10} {len(found)} links")
        for x in found[:6]:
            print("     ", x[0], "|", x[1])
    except Exception as e:
        print(name, "ERR", type(e).__name__)
