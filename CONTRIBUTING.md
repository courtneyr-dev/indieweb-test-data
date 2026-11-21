# Contributing

## Adding a kind, format, or XFN value

Edit the CSV in `data/`, regenerate, commit both the data change and the regenerated XML:

```bash
bin/generate.py > indieweb-test-data.xml
bin/generate.py --layer extended > indieweb-test-data-extended.xml
bin/generate.py --no-matrix > indieweb-test-data-small.xml
```

For a kind, `response=yes` means it responds to something else and needs citation data. That flag is
what drives cite meta in the extended layer.

## Adding an edge case

The most valuable contribution here. Add it to the `E` list in `bin/generate.py` with a slug
starting `edge-`, and say in the PR **what broke** — an edge case with a real failure behind it is
worth ten hypothetical ones.

Cases that test an *absence* (missing meta, empty content) must not receive that meta in the
extended layer. See how `edge-reply-no-cite` and `edge-link-no-url` are handled.

## Adding an XFN or post-format round trip

Put same-stem `<id>.json`, `<id>.expected.json`, and HTML files under
`cases/xfn/` or `cases/post-formats/<format>/`. Use a lower-kebab-case ID and
unique WXR post and attachment IDs. Use fictional names and identify which
assertions apply at import, save, reload, or render. For generated assets, add a
[provenance and license entry](media/README.md) and register the filename and
MIME type in [the local import hook](bin/local-media.php). Regenerate all three
exports.

## Adding support for another plugin

One block in `extended_meta()`, namespaced by that plugin's meta prefix, with a comment naming the
plugin. Don't touch the generic layer — it must stay plugin-agnostic.

## Rules

- **Never hand-edit the XML.** It's generated; your change will be overwritten.
- **`example.test` for every URL.** Reserved by RFC 6761, guaranteed not to resolve.
- Keep it importable on the oldest WordPress the consuming plugins support.
- Run the validator before opening a PR: `python3 -c "import xml.etree.ElementTree as ET; [ET.parse(f) for f in __import__('glob').glob('*.xml')]"`
