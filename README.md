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
| [`indieweb-test-data.xml`](indieweb-test-data.xml) | 497 | Formats, kinds, XFN, and edge cases |
| [`indieweb-test-data-small.xml`](indieweb-test-data-small.xml) | 97 | Same, without the 400-post matrix |
| [`indieweb-test-data-extended.xml`](indieweb-test-data-extended.xml) | 501 | Adds plugin metadata, PKIW cards, and two media attachments |

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

**Edge cases** cover the following:

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
| `_pkiw_*` | [post-kinds-for-indieweb](https://github.com/courtneyr-dev/post-kinds-for-indieweb) | citation, check-in, geo, and Listen card facts |

Adding another plugin means one block in `extended_meta()` — nothing else changes.

### Import the bundled images

On a disposable WordPress install, activate Post Kinds for IndieWeb before
importing. From this checkout, use WP-CLI to load the two PNGs from `media/`.
The files import as attachments with captions and alt text. WordPress remaps
the featured images to those attachments.

```bash
wp --path=/path/to/disposable-wordpress plugin install wordpress-importer --activate
wp --path=/path/to/disposable-wordpress import indieweb-test-data-extended.xml \
  --authors=create --require="$PWD/bin/local-media.php"
```

The generic exports import through **Tools → Import → WordPress**. For a
content-only import of the extended export through wp-admin, leave attachment
downloads off.

### Check visibility and card rendering

| Find the posts by slug | Check |
|---|---|
| `edge-listen-public`, `edge-listen-locked` | Both have the same episode facts in the extended export. Signed out, the locked post keeps its title and hides the cover, listen link, and rating on surfaces that enforce PKIW privacy. Use the fixture password `fixture-unlock` on the single post. |
| `edge-listen-native-card`, `edge-listen-public` | In the extended export, the native block and the metadata-only fixture describe the same episode. Compare them on render paths that support both inputs. |
| `edge-listen-missing-cover` | The episode still has its title and facts when the cover URL has no file. |
| `edge-recipe-public`, `edge-recipe-locked` | On a theme with the recipe privacy rules, compare the public card and the locked post in the archive, embed, and single views. |

To exercise the recipe print routes, activate WP Recipe Maker after import and run
`wp --path=/path/to/disposable-wordpress eval-file bin/recipe-print.php`. The command prints a URL path for each
fixture. On the courtneyr.dev child theme, signed-out requests to the public
recipe print, locked recipe print, and a nonexistent recipe print should
return 200, 404, and 404 respectively.

### Check dates across midnight

`--as-of` anchors four cases to a date you choose. Use a disposable install
set to **UTC−05:00** to compare its local dates with the stored UTC dates.

```bash
bin/generate.py --no-matrix --as-of 2027-01-01 > indie-web-year-boundary.xml
```

| Slug | Expected date or status |
|---|---|
| `edge-date-anniversary` | Same month and day in the previous year, or February 28 for a leap-day anchor. |
| `edge-date-before-midnight` | December 31 at 23:30 local. WordPress stores January 1 at 04:30 UTC. |
| `edge-date-after-midnight` | January 1 at 00:30 local. WordPress stores January 1 at 05:30 UTC. |
| `edge-date-scheduled` | January 2 at 09:00 local. Generate with today's date to verify it remains scheduled after import. |

The checked-in exports use January 1, 2026 as their fixed anchor. Importer
status depends on when you run it because WordPress compares publish dates to
its clock.

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

Synthetic media uses `example.test`, a reserved domain. The extended import
command above loads its bundled images from disk. Some content deliberately
references unavailable media to exercise fallback behavior.

Import into a **disposable site**. This is test content, not a starter kit.

## Contributing

New kinds, XFN cases, and edge cases are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). The most
useful contribution is an edge case that broke something real.

## License

GPLv2 or later — see [LICENSE](LICENSE). Same as WordPress.
