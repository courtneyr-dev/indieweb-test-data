#!/usr/bin/env python3
"""Generate WordPress WXR test data for post formats, IndieWeb post kinds, and XFN.

Two layers:

  generic   post formats, the `kind` taxonomy, XFN rel values, and edge cases.
            Nothing plugin-specific — works with any plugin that uses the `kind`
            taxonomy, and with core post formats alone.

  extended  everything in generic, plus the post meta that specific plugins read.
            Opt in with --layer extended.

The vocabularies live in data/*.csv so adding a kind is a one-line change and
shows up in a diff.

Usage
    bin/generate.py                                  > indieweb-test-data.xml
    bin/generate.py --layer extended                 > indieweb-test-data-extended.xml
    bin/generate.py --no-matrix                      > indieweb-test-data-small.xml
    bin/generate.py --layer extended --no-matrix     > small extended
"""

import argparse
import csv
import json
import sys
from calendar import monthrange
from datetime import date, datetime, time, timedelta, timezone
from itertools import count
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASE = datetime(2026, 1, 1, 9, tzinfo=timezone.utc)
FIXTURE_ZONE = timezone(timedelta(hours=-5))
UPLOADS = "https://example.test/wp-content/uploads/indieweb-fixtures"
COVER_ID = 3001
MEDIA = (
    (COVER_ID, "indieweb-night-signal.png", "Night Signal cover",
     "A yellow moon above a navy skyline", "Cover art for the fictional Night Signal episode."),
    (3002, "indieweb-tomato-soup.png", "Tomato soup",
     "A red bowl of tomato soup on a pale table", "Tomato soup for the fictional recipe."),
)


def load(name):
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


FORMATS = [r["slug"] for r in load("formats.csv")]
KIND_ROWS = load("kinds.csv")
KINDS = [r["slug"] for r in KIND_ROWS]
KIND_LABEL = {r["slug"]: r["label"] for r in KIND_ROWS}
RESPONSE_KINDS = {r["slug"] for r in KIND_ROWS if r["response"] == "yes"}
XFN_ROWS = load("xfn.csv")
XFN = [r["value"] for r in XFN_ROWS]
XFN_GROUP = {r["value"]: r["group"] for r in XFN_ROWS}


def cd(s):
    return f"<![CDATA[{s}]]>"


def meta_xml(key, value):
    return (f"\t\t<wp:postmeta>\n\t\t\t<wp:meta_key>{cd(key)}</wp:meta_key>\n"
            f"\t\t\t<wp:meta_value>{cd(value)}</wp:meta_value>\n\t\t</wp:postmeta>\n")


def render_item(title, content, *, pid, slug, fmt=None, kind=None, metas=None,
                excerpt="", offset_days=0, status="publish", password="",
                local_date=None, attachment_url=None):
    posted = local_date or BASE + timedelta(days=offset_days, minutes=pid % 600)
    utc = posted.astimezone(timezone.utc)
    ds = posted.strftime("%Y-%m-%d %H:%M:%S")
    gmt = utc.strftime("%Y-%m-%d %H:%M:%S")
    pub = utc.strftime("%a, %d %b %Y %H:%M:%S +0000")
    lines = [
        "\t<item>",
        f"\t\t<title>{cd(title)}</title>",
        f"\t\t<link>http://example.test/{slug}/</link>",
        f"\t\t<pubDate>{pub}</pubDate>",
        f"\t\t<dc:creator>{cd('testbot')}</dc:creator>",
        f'\t\t<guid isPermaLink="false">http://example.test/?p={pid}</guid>',
        "\t\t<description></description>",
        f"\t\t<content:encoded>{cd(content)}</content:encoded>",
        f"\t\t<excerpt:encoded>{cd(excerpt)}</excerpt:encoded>",
        f"\t\t<wp:post_id>{pid}</wp:post_id>",
        f"\t\t<wp:post_date>{cd(ds)}</wp:post_date>",
        f"\t\t<wp:post_date_gmt>{cd(gmt)}</wp:post_date_gmt>",
        f"\t\t<wp:comment_status>{cd('open')}</wp:comment_status>",
        f"\t\t<wp:ping_status>{cd('open')}</wp:ping_status>",
        f"\t\t<wp:post_name>{cd(slug)}</wp:post_name>",
        f"\t\t<wp:status>{cd(status)}</wp:status>",
        "\t\t<wp:post_parent>0</wp:post_parent>",
        "\t\t<wp:menu_order>0</wp:menu_order>",
        f"\t\t<wp:post_type>{cd('attachment' if attachment_url else 'post')}</wp:post_type>",
        (f"\t\t<wp:post_password>{cd(password)}</wp:post_password>" if password
         else "\t\t<wp:post_password></wp:post_password>"),
        "\t\t<wp:is_sticky>0</wp:is_sticky>",
    ]
    if attachment_url:
        lines.append(f"\t\t<wp:attachment_url>{cd(attachment_url)}</wp:attachment_url>")
    if fmt and fmt != "standard":
        lines.append(f'\t\t<category domain="post_format" nicename="post-format-{fmt}">'
                     f'{cd("Post format " + fmt)}</category>')
    if kind:
        lines.append(f'\t\t<category domain="kind" nicename="{kind}">'
                     f'{cd(KIND_LABEL.get(kind, kind.title()))}</category>')
    body = "\n".join(lines) + "\n"
    for k, v in (metas or {}).items():
        body += meta_xml(k, v)
    return body + "\t</item>\n"


# --- Content -----------------------------------------------------------------

FORMAT_CONTENT = {
    "quote": ('<!-- wp:quote --><blockquote class="wp-block-quote"><p>The build describes reality; '
              "the announcement describes intent.</p><cite>Ada Lovelace</cite></blockquote><!-- /wp:quote -->"),
    "link": ('<!-- wp:paragraph --><p>Worth reading: <a href="https://indieweb.org/">the IndieWeb wiki</a>'
             "</p><!-- /wp:paragraph -->"),
    "image": ('<!-- wp:image --><figure class="wp-block-image">'
              '<img src="https://example.test/wp-content/uploads/photo.jpg" alt="A ridgeline at dusk"/>'
              "<figcaption>A ridgeline at dusk</figcaption></figure><!-- /wp:image -->"),
    "gallery": ('<!-- wp:gallery --><figure class="wp-block-gallery">'
                '<img src="https://example.test/wp-content/uploads/one.jpg" alt="One"/>'
                '<img src="https://example.test/wp-content/uploads/two.jpg" alt="Two"/>'
                "</figure><!-- /wp:gallery -->"),
    "video": ('<!-- wp:video --><figure class="wp-block-video">'
              '<video controls src="https://example.test/wp-content/uploads/clip.mp4"></video>'
              "</figure><!-- /wp:video -->"),
    "audio": ('<!-- wp:audio --><figure class="wp-block-audio">'
              '<audio controls src="https://example.test/wp-content/uploads/track.mp3"></audio>'
              "</figure><!-- /wp:audio -->"),
    "chat": ("<!-- wp:paragraph --><p>Ada: is the RC out?<br/>Grace: not yet<br/>"
             "Ada: then we are testing the beta<br/>Grace: and labelling it the beta</p><!-- /wp:paragraph -->"),
    "status": "<!-- wp:paragraph --><p>Fixtures built. Controls calibrated.</p><!-- /wp:paragraph -->",
    "aside": "<!-- wp:paragraph --><p>A short remark with no title of its own.</p><!-- /wp:paragraph -->",
    "standard": ("<!-- wp:paragraph --><p>A standard post with ordinary prose, long enough that a "
                 "character count resolves to something meaningful. It carries a "
                 '<a href="https://wordpress.org/">plain link</a> too.</p><!-- /wp:paragraph -->'),
}


def kind_content(kind):
    if kind == "checkin":
        return "<!-- wp:paragraph --><p>Checked in at the trailhead.</p><!-- /wp:paragraph -->"
    if kind in RESPONSE_KINDS:
        return (f'<!-- wp:paragraph --><p>A {kind} of '
                f'<a href="https://indieweb.org/{kind}">something on the IndieWeb</a>.</p><!-- /wp:paragraph -->')
    return f"<!-- wp:paragraph --><p>A {kind} post with ordinary content.</p><!-- /wp:paragraph -->"


def xfn_link(values, label):
    return (f'<!-- wp:paragraph --><p>Someone I know: '
            f'<a href="https://example.test/people/{label}/" rel="{" ".join(values)}">{label}</a>'
            "</p><!-- /wp:paragraph -->")


# --- Extended layer: plugin-specific meta ------------------------------------
# Each block is namespaced by the plugin that reads it. Adding support for
# another plugin means adding a block here, not changing anything above.

def extended_meta(fmt=None, kind=None):
    m = {}
    if fmt:
        # post-formats-for-block-themes
        m["_pfbt_format_manual"] = fmt
        if fmt == "link":
            m["_pfbt_link_url"] = "https://indieweb.org/"
    if kind:
        # post-kinds-for-indieweb
        if kind in RESPONSE_KINDS:
            m.update({
                "_pkiw_cite_url": f"https://indieweb.org/{kind}",
                "_pkiw_cite_name": f"The thing being responded to ({kind})",
                "_pkiw_cite_author": "A. Author",
                "_pkiw_cite_photo": "https://example.test/wp-content/uploads/avatar.jpg",
            })
        if kind == "checkin":
            m.update({
                "_pkiw_checkin_name": "Ridge Trailhead",
                "_pkiw_checkin_venue": "Ridge Trailhead",
                "_pkiw_checkin_locality": "High Country",
                "_pkiw_checkin_region": "CO",
                "_pkiw_checkin_country": "US",
                "_pkiw_checkin_latitude": "39.7392",
                "_pkiw_checkin_longitude": "-104.9903",
                "_pkiw_checkin_shout": "Forty minutes past the last cell signal.",
                "_pkiw_geo_latitude": "39.7392",
                "_pkiw_geo_longitude": "-104.9903",
            })
    return m


# --- Build -------------------------------------------------------------------

def build(layer="generic", matrix=True, as_of=BASE.date()):
    ext = layer == "extended"
    ids = count(1001)

    def item(title, content, **fields):
        return render_item(title, content, pid=next(ids), **fields)
    def M(fmt=None, kind=None):
        return extended_meta(fmt, kind) if ext else {}

    items = []

    for i, f in enumerate(FORMATS):
        items.append(item(f"Format: {f}", FORMAT_CONTENT[f], slug=f"format-{f}", fmt=f,
                          metas=M(fmt=f), offset_days=i,
                          excerpt=f"A post using the {f} post format."))

    for i, k in enumerate(KINDS):
        items.append(item(f"Kind: {k}", kind_content(k), slug=f"kind-{k}", kind=k,
                          metas=M(kind=k), offset_days=20 + i,
                          excerpt=f"A post of kind {k}."))

    if matrix:
        n = 0
        for f in FORMATS:
            for k in KINDS:
                m = M(fmt=f); m.update(M(kind=k))
                items.append(item(
                    f"Matrix: {f} x {k}",
                    f"<!-- wp:paragraph --><p>Post format <strong>{f}</strong> combined with kind "
                    f"<strong>{k}</strong>.</p><!-- /wp:paragraph -->",
                    slug=f"matrix-{f}-{k}", fmt=f, kind=k, metas=m, offset_days=50 + n // 24))
                n += 1

    for v in XFN:
        items.append(item(f"XFN: {v}", xfn_link([v], v), slug=f"xfn-{v}", offset_days=120,
                          excerpt=f"Single XFN value ({XFN_GROUP[v]} group): {v}"))

    for vals, label in [
        (["friend", "met"], "friend-met"),
        (["friend", "met", "co-worker"], "friend-met-coworker"),
        (["acquaintance", "neighbor"], "acquaintance-neighbor"),
        (["spouse", "met", "sweetheart"], "spouse-met-sweetheart"),
        (["parent", "met"], "parent-met"),
        (["colleague", "co-resident", "met"], "colleague-coresident-met"),
        (["me"], "me-identity"),
    ]:
        items.append(item(f"XFN combo: {' '.join(vals)}", xfn_link(vals, label),
                          slug=f"xfn-combo-{label}", offset_days=125,
                          excerpt="Values from different XFN groups combine; within a group they do not."))

    items.append(item("XFN: many links in one post",
                      "\n".join(xfn_link([v], v) for v in XFN[:8]),
                      slug="xfn-many-in-one", offset_days=126))

    # Edge cases — where the interesting failures live.
    E = [
        ("Edge: format with no kind", FORMAT_CONTENT["quote"], "edge-format-no-kind", "quote", None),
        ("Edge: kind with no format", kind_content("reply"), "edge-kind-no-format", None, "reply"),
        ("Edge: neither format nor kind",
         "<!-- wp:paragraph --><p>A plain post. Both should leave it alone.</p><!-- /wp:paragraph -->",
         "edge-neither", None, None),
        ("Edge: empty content", "", "edge-empty-content", "status", "note"),
        ("Edge: response kind with no cite data",
         "<!-- wp:paragraph --><p>A reply whose citation was never recorded.</p><!-- /wp:paragraph -->",
         "edge-reply-no-cite", None, "reply"),
        ("Edge: link format with no target URL",
         "<!-- wp:paragraph --><p>A link post missing its URL.</p><!-- /wp:paragraph -->",
         "edge-link-no-url", "link", None),
        ("Edge: unicode and emoji — 日本語 · Ελληνικά · 🌲🏔️",
         "<!-- wp:paragraph --><p>Multibyte: 日本語テキスト, Ελληνικά, Русский, and emoji 🌲🏔️🔭."
         "</p><!-- /wp:paragraph -->", "edge-unicode", "status", "note"),
        ("Edge: RTL content — العربية",
         '<!-- wp:paragraph --><p dir="rtl" lang="ar">هذا نص عربي لاختبار الاتجاه من اليمين إلى اليسار.'
         "</p><!-- /wp:paragraph -->", "edge-rtl", "aside", "note"),
        ("Edge: very long content",
         "<!-- wp:paragraph --><p>" + ("The quick brown fox jumps over the lazy dog. " * 200) +
         "</p><!-- /wp:paragraph -->", "edge-long", "standard", "article"),
        ("Edge: HTML entities in a citation",
         '<!-- wp:quote --><blockquote class="wp-block-quote"><p>&laquo;Ampersands &amp; '
         "&lt;angle brackets&gt;&raquo;.</p><cite>O&#8217;Brien &amp; Co.</cite></blockquote>"
         "<!-- /wp:quote -->", "edge-entities", "quote", None),
    ]
    for title, content, slug, f, k in E:
        m = M(fmt=f); m.update(M(kind=k))
        # Deliberately withhold the meta these two cases exist to test the absence of.
        if slug in ("edge-reply-no-cite", "edge-link-no-url"):
            m = {}
        items.append(item(title, content, slug=slug, fmt=f, kind=k, metas=m, offset_days=130))

    items.append(item("Edge: draft with format and kind",
                      "<!-- wp:paragraph --><p>Unpublished.</p><!-- /wp:paragraph -->",
                      slug="edge-draft", fmt="image", kind="photo", status="draft", offset_days=134))
    items.append(item("Edge: XFN with an unknown rel token",
                      '<!-- wp:paragraph --><p><a href="https://example.test/people/nobody/" '
                      'rel="friend notarealvalue met">nobody</a></p><!-- /wp:paragraph -->',
                      slug="edge-xfn-invalid", offset_days=134))
    items.append(item("Edge: rel=me on external profiles",
                      '<!-- wp:paragraph --><p>Also me: '
                      '<a href="https://github.com/example" rel="me">GitHub</a>, '
                      '<a href="https://example.test/" rel="me">home</a></p><!-- /wp:paragraph -->',
                      slug="edge-xfn-me-rel", offset_days=134))

    if ext:
        for media_id, filename, title, alt, caption in MEDIA:
            items.append(render_item(
                title, "", pid=media_id, slug=Path(filename).stem, status="inherit",
                attachment_url=f"{UPLOADS}/{filename}", excerpt=caption,
                metas={"_wp_attachment_image_alt": alt}))

    listen_meta = {
        "_pkiw_listen_track": "Night Signal",
        "_pkiw_listen_artist": "Lakeside Radio",
        "_pkiw_listen_album": "Lakeside Radio",
        "_pkiw_listen_media_type": "podcast",
        "_pkiw_listen_url": "https://example.test/listen/night-signal/",
        "_pkiw_listen_rating": "4",
        "_thumbnail_id": str(COVER_ID),
    }
    notes = "<!-- wp:paragraph --><p>Fixture notes for Night Signal.</p><!-- /wp:paragraph -->"
    for kind, title, content, meta in (
        ("listen", "Night Signal", notes, listen_meta),
        ("recipe", "Tomato soup", "<!-- wp:paragraph --><p>Fixture recipe notes for tomato soup.</p><!-- /wp:paragraph -->",
         {"_thumbnail_id": str(MEDIA[1][0])}),
    ):
        for visibility, password in (("public", ""), ("locked", "fixture-unlock")):
            items.append(item(
                f"{title} ({visibility})", content, slug=f"edge-{kind}-{visibility}",
                kind=kind, metas=meta if ext else None, password=password, offset_days=135))

    if ext:
        attrs = {
            "trackTitle": "Night Signal",
            "artistName": "Lakeside Radio",
            "albumTitle": "Lakeside Radio",
            "mediaType": "podcast",
            "listenUrl": listen_meta["_pkiw_listen_url"],
            "rating": 4,
        }
        card = f"<!-- wp:post-kinds-indieweb/listen-card {json.dumps(attrs)} /-->"
        items.append(item(
            "Night Signal (native card)", card + notes, kind="listen", slug="edge-listen-native-card",
            metas={"_thumbnail_id": str(COVER_ID)}, offset_days=136))
        missing = dict(attrs, coverImage=f"{UPLOADS}/missing-cover.png")
        items.append(item(
            "Night Signal (missing cover)", f"<!-- wp:post-kinds-indieweb/listen-card {json.dumps(missing)} /-->" + notes,
            kind="listen", slug="edge-listen-missing-cover", offset_days=136))

    previous_year = as_of.year - 1
    anniversary = as_of.replace(
        year=previous_year, day=min(as_of.day, monthrange(previous_year, as_of.month)[1]))
    for slug, title, day, at, status in (
        ("edge-date-anniversary", "Date: previous-year anniversary", anniversary, time(12), "publish"),
        ("edge-date-before-midnight", "Date: before local midnight", as_of - timedelta(days=1), time(23, 30), "publish"),
        ("edge-date-after-midnight", "Date: after local midnight", as_of, time(0, 30), "publish"),
        ("edge-date-scheduled", "Date: scheduled for tomorrow", as_of + timedelta(days=1), time(9), "future"),
    ):
        items.append(item(
            title, notes, slug=slug, kind="listen", status=status,
            local_date=datetime.combine(day, at, tzinfo=FIXTURE_ZONE)))

    terms = "".join(
        f"\t<wp:term><wp:term_id>{2000+i}</wp:term_id>"
        f"<wp:term_taxonomy>{cd('kind')}</wp:term_taxonomy>"
        f"<wp:term_slug>{cd(k)}</wp:term_slug>"
        f"<wp:term_name>{cd(KIND_LABEL[k])}</wp:term_name></wp:term>\n"
        for i, k in enumerate(KINDS))

    head = f"""<?xml version="1.0" encoding="UTF-8" ?>
<!--
  IndieWeb test data — {layer} layer{"" if matrix else ", no format x kind matrix"}
  {len(FORMATS)} post formats · {len(KINDS)} kinds · {len(XFN)} XFN values · {len(items)} items
  Generated by bin/generate.py — regenerate rather than editing.
  https://github.com/courtneyr-dev/indieweb-test-data
-->
<rss version="2.0"
\txmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
\txmlns:content="http://purl.org/rss/1.0/modules/content/"
\txmlns:wfw="http://wellformedweb.org/CommentAPI/"
\txmlns:dc="http://purl.org/dc/elements/1.1/"
\txmlns:wp="http://wordpress.org/export/1.2/">
<channel>
\t<title>IndieWeb Test Data</title>
\t<link>http://example.test</link>
\t<description>Post formats, IndieWeb post kinds, and XFN</description>
\t<pubDate>{BASE.strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
\t<language>en-US</language>
\t<wp:wxr_version>1.2</wp:wxr_version>
\t<wp:base_site_url>http://example.test</wp:base_site_url>
\t<wp:base_blog_url>http://example.test</wp:base_blog_url>
\t<wp:author><wp:author_id>1</wp:author_id><wp:author_login>{cd('testbot')}</wp:author_login>
\t\t<wp:author_email>{cd('testbot@example.test')}</wp:author_email>
\t\t<wp:author_display_name>{cd('Test Bot')}</wp:author_display_name>
\t\t<wp:author_first_name>{cd('Test')}</wp:author_first_name>
\t\t<wp:author_last_name>{cd('Bot')}</wp:author_last_name></wp:author>
{terms}"""
    return head + "".join(items) + "</channel>\n</rss>\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer", choices=("generic", "extended"), default="generic")
    ap.add_argument("--no-matrix", action="store_true",
                    help="skip the format x kind cross-product")
    ap.add_argument("--as-of", type=date.fromisoformat, default=BASE.date(), metavar="YYYY-MM-DD",
                    help="anchor the four date fixtures (default: %(default)s)")
    a = ap.parse_args()
    if not 2 <= a.as_of.year <= 9998:
        ap.error("--as-of must allow dates in the previous year and the following day")
    sys.stdout.write(build(layer=a.layer, matrix=not a.no_matrix, as_of=a.as_of))
