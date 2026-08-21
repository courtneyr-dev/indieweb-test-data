# IndieWeb test data

Importable WordPress test content for **post formats**, the **`kind` taxonomy**, and **XFN**
relationship values — the combinations that existing test corpora don't cover.

[`WordPress/theme-test-data`](https://github.com/WordPress/theme-test-data) covers core markup edge
cases. [`wpaccessibility/a11y-theme-unit-test`](https://github.com/wpaccessibility/a11y-theme-unit-test)
covers accessibility. Neither covers post formats crossed with post kinds, and nothing covers XFN.
This fills that gap.

## Quick start

```bash
wp plugin install wordpress-importer --activate
curl -sLO https://raw.githubusercontent.com/courtneyr-dev/indieweb-test-data/main/indieweb-test-data.xml
wp import indieweb-test-data.xml --authors=create
```

| File | Items | Contents |
|---|---:|---|
| [`indieweb-test-data.xml`](indieweb-test-data.xml) | 489 | **Start here.** Formats, kinds, XFN, edge cases — no plugin-specific meta |
| [`indieweb-test-data-small.xml`](indieweb-test-data-small.xml) | 89 | Same, without the 400-post matrix |
| [`indieweb-test-data-extended.xml`](indieweb-test-data-extended.xml) | 489 | Adds post meta specific plugins read — see [Extended layer](#extended-layer) |

## What's covered

**10 post formats** — standard, aside, chat, gallery, link, image, quote, status, video, audio.
Content is shaped so format-dependent logic has something real to work on: the quote post has a
`<cite>`, the image post has a caption and alt text, the link post points somewhere.

**40 post kinds** on the `kind` taxonomy — acquisition, article, audio, bookmark, checkin,
chicken, collection, comics, craft, drink, eat, event, exercise, favorite, follow, issue,
itinerary, jam, like, listen, mood, note, photo, play, presentation, question, quote, read,
recipe, reply, repost, review, rsvp, sleep, tag, trip, video, watch, weather, wish.

> The `kind` taxonomy slug is shared by more than one plugin, so this data imports for any of them.

**The full 10 × 40 matrix** — 400 posts covering every format/kind pair. Verbose on purpose: when two
plugins both render a post, their interaction lives in the cross-product, and a bug that only appears
for `quote` + `like` is invisible to testing either dimension alone.

**18 XFN values** across all seven groups, each on its own, plus seven multi-group combinations
(`friend met`, `spouse met sweetheart`, `colleague co-resident met`). Values from different groups
combine; values within a group are mutually exclusive.

**16 edge cases** — the section worth reading before you use this:

| Case | Why |
|---|---|
| Format with no kind, kind with no format, neither | Each is a different code path |
| Empty content | Character counts and excerpt logic |
| Response kind with **no** citation data | The absence is the test |
| Link format with **no** target URL | Same |
| Unicode, emoji, and RTL Arabic | Round-tripping through any transform |
| 9,000-character post | Truncation and counting |
| HTML entities inside a `<cite>` | Escaping |
| Draft with format and kind | Must not appear on the front end |
| XFN with an unknown `rel` token | Graceful handling of invalid input |
| `rel="me"` on external profiles | Identity consolidation |

## Extended layer

The generic files carry no plugin-specific post meta, so they work anywhere. The **extended** file
adds meta that named plugins read:

| Prefix | Plugin | Adds |
|---|---|---|
| `_pfbt_*` | [post-formats-for-block-themes](https://github.com/courtneyr-dev/post-formats-for-block-themes) | manual format assignment, link target URL |
| `_pkiw_*` | [post-kinds-for-indieweb](https://github.com/courtneyr-dev/post-kinds-for-indieweb) | citation URL/name/author/photo, checkin venue and geo |

Adding another plugin means one block in `extended_meta()` — nothing else changes.

## Regenerating

The vocabularies live in [`data/`](data/) as CSV, so adding a kind is a one-line change that shows
up in a diff.

```bash
bin/generate.py                              > indieweb-test-data.xml
bin/generate.py --layer extended             > indieweb-test-data-extended.xml
bin/generate.py --no-matrix                  > indieweb-test-data-small.xml
```

| File | Holds |
|---|---|
| [`data/formats.csv`](data/formats.csv) | The 10 core post formats |
| [`data/kinds.csv`](data/kinds.csv) | Kind slugs, labels, and whether each is a *response* kind needing citation data |
| [`data/xfn.csv`](data/xfn.csv) | XFN values and their groups |

Python 3, no dependencies.

## Pairing it with the other corpora

These complement rather than replace each other. For a full test site, import all three:

```bash
wp plugin install wordpress-importer --activate

curl -sLO https://raw.githubusercontent.com/WordPress/theme-test-data/master/themeunittestdata.wordpress.xml
wp import themeunittestdata.wordpress.xml --authors=create

curl -sLO https://raw.githubusercontent.com/wpaccessibility/a11y-theme-unit-test/master/a11y-theme-unit-test-data.xml
wp import a11y-theme-unit-test-data.xml --authors=create

curl -sLO https://raw.githubusercontent.com/courtneyr-dev/indieweb-test-data/main/indieweb-test-data.xml
wp import indieweb-test-data.xml --authors=create
```

| Corpus | Covers |
|---|---|
| theme-test-data | Core markup, nested menus, embeds, alignments, sticky/password/scheduled posts |
| a11y-theme-unit-test | Accessibility-focused content |
| **this** | Post formats × kinds × XFN, and their edge cases |

## Notes

Every URL is `example.test` — reserved by [RFC 6761](https://www.rfc-editor.org/rfc/rfc6761) and
guaranteed not to resolve. Nothing here reaches the network on import.

Import into a **disposable site**. This is test content, not a starter kit.

## Contributing

New kinds, XFN cases, and edge cases are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). The most
useful contribution is an edge case that broke something real.

## License

GPLv2 or later — see [LICENSE](LICENSE). Same as WordPress.
