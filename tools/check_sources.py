"""Checks which official press-release feeds and pages answer from GitHub (run by the check-sources workflow)."""
import re
import sys
import requests

CANDIDATES = [
    # --- 2026-11-27: embassies, high commissions and foreign ministries relevant to Jamaica ---
    ("US Emb Jamaica", ["https://jm.usembassy.gov/feed/", "https://jm.usembassy.gov/category/news-events/feed/", "https://jm.usembassy.gov/news-events/"]),
    ("US State press", ["https://www.state.gov/rss-feed/press-releases/feed/", "https://www.state.gov/rss-feed/western-hemisphere-affairs/feed/"]),
    ("BHC Kingston", ["https://www.gov.uk/government/world/organisations/british-high-commission-kingston.atom",
                      "https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=british-high-commission-kingston"]),
    ("Canada IRCC", ["https://api.io.canada.ca/io-server/gc/news/en/v2?dept=immigrationrefugeescitizenshipcanada&type=newsreleases&sort=publishedDate&orderBy=desc&pick=50&format=atom&atomtitle=IRCC"]),
    ("China Emb JM", ["http://jm.china-embassy.gov.cn/eng/", "http://jm.china-embassy.gov.cn/eng/sgxw/"]),
    ("China MFA", ["https://www.fmprc.gov.cn/eng/xw/rss.xml", "https://www.mfa.gov.cn/eng/rss.xml"]),
    ("Cuba Emb JM", ["https://misiones.cubaminrex.cu/en/jamaica", "https://misiones.cubaminrex.cu/en/rss.xml", "https://cubaminrex.cu/en/rss.xml"]),
    ("India HC JM", ["https://www.hcikingston.gov.in/", "https://www.hcikingston.gov.in/news.php"]),
    ("India MEA", ["https://www.mea.gov.in/rss/press-releases.xml"]),
    ("Nigeria MFA", ["https://foreignaffairs.gov.ng/feed/", "https://foreignaffairs.gov.ng/news/"]),
    ("Venezuela MPPRE", ["https://mppre.gob.ve/feed/", "https://mppre.gob.ve/category/comunicados/feed/"]),
    ("Japan Emb JM", ["https://www.jamaica.emb-japan.go.jp/itpr_en/index.html"]),
    ("Japan MOFA", ["https://www.mofa.go.jp/rss/press_e.xml", "https://www.mofa.go.jp/rss/index_e.xml"]),
    ("EU Delegation JM", ["https://www.eeas.europa.eu/delegations/jamaica/news_en", "https://www.eeas.europa.eu/rss.xml"]),
    ("Mexico SRE", ["https://www.gob.mx/sre/archivo/prensa?format=rss", "https://www.gob.mx/sre/prensa"]),
    ("Germany AA", ["https://www.auswaertiges-amt.de/blueprint/servlet/aa/rss/en/newsfeed"]),
    ("France Diplo", ["https://www.diplomatie.gouv.fr/spip.php?page=backend-fd&lang=en"]),
    ("Spain Exteriores", ["https://www.exteriores.gob.es/es/Comunicacion/Noticias/rss.xml"]),
    ("Dom Rep MIREX", ["https://mirex.gob.do/feed/"]),
    ("Haiti MAE", ["https://www.mae.gouv.ht/feed/"]),
    ("T&T MFCA", ["https://foreign.gov.tt/feed/", "https://foreign.gov.tt/news/"]),
    ("Jamaica MFAFT", ["https://mfaft.gov.jm/feed/", "https://mfaft.gov.jm/jm/feed/", "https://mfaft.gov.jm/jm/category/news/feed/", "https://mfaft.gov.jm/jm/news/"]),
    ("JA Emb USA", ["https://www.embassyofjamaica.org/feed/", "https://www.embassyofjamaica.org/"]),
    ("JA HC London", ["https://www.jhcuk.com/feed/", "https://www.jhcuk.com/news"]),
    ("JA CG New York", ["https://jamaicacgny.org/feed/"]),
    ("JA CG Miami", ["https://jamaicacgmiami.org/feed/"]),
    ("JA CG Toronto", ["https://www.jcgtoronto.ca/feed/", "https://jcgtoronto.ca/feed/"]),
    ("JA HC Ottawa", ["https://www.jhcottawa.ca/feed/", "https://jhcottawa.ca/feed/"]),
    ("CARICOM", ["https://caricom.org/feed/"]),
]
PAGES = [
    ("US Emb Jamaica", "https://jm.usembassy.gov/news-events/", "jm.usembassy.gov/"),
    ("EU Delegation JM", "https://www.eeas.europa.eu/delegations/jamaica/news_en", "/delegations/jamaica/"),
    ("China Emb JM", "http://jm.china-embassy.gov.cn/eng/", "/eng/"),
    ("India HC JM", "https://www.hcikingston.gov.in/", "hcikingston"),
    ("Jamaica MFAFT", "https://mfaft.gov.jm/jm/news/", "/news/"),
]
# Google News searches limited to one mission website (site:) and by mission name
GN = ["site:jm.usembassy.gov", "site:mfaft.gov.jm", "site:gov.uk Jamaica", "site:jm.china-embassy.gov.cn", "site:hcikingston.gov.in",
      "site:eeas.europa.eu Jamaica", "site:international.gc.ca Jamaica",
      '"U.S. Embassy Kingston" OR "US Embassy in Jamaica"', '"British High Commission" Jamaica', '"Canadian High Commission" Jamaica',
      '"Chinese Embassy" Jamaica', '"Cuban Embassy" Jamaica', '"Indian High Commission" Jamaica', '"Nigerian High Commission" Jamaica',
      '"Venezuelan Embassy" Jamaica', '"Japanese Embassy" Jamaica', '"EU Delegation" Jamaica',
      '"Jamaican Embassy" OR "Jamaican High Commission" OR "Jamaican Consulate"', '"Ministry of Foreign Affairs and Foreign Trade" Jamaica']
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


print("\n--- Google News (last 30 days): headlines and publisher names ---")
import time, collections
for q in GN:
    try:
        u = "https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:30d") + "&hl=en-US&gl=US&ceid=US:en"
        t = requests.get(u, headers=H, timeout=25).text
        srcs = collections.Counter(re.findall(r"<source[^>]*>(.*?)</source>", t))
        print(f"{q[:60]:60} items={len(re.findall(r'<item>', t)):3} sources={srcs.most_common(6)}")
    except Exception as e:
        print(q, "ERR", type(e).__name__)
    time.sleep(2)
