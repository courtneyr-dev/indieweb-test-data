const fs = require('node:fs/promises');
const path = require('node:path');

const corpusPlugin = 'post-kinds-for-indieweb-in-block-themes';
const specs = [
	{
		name: 'pkiw-directory',
		plugin: corpusPlugin,
		condition: "count(get_terms(['taxonomy' => 'kind', 'hide_empty' => false])) >= 40",
	},
	{
		name: 'pkiw-standalone',
		plugin: corpusPlugin,
		url: 'https://raw.githubusercontent.com/courtneyr-dev/post-kinds-for-indieweb/main/blueprints/blueprint.json',
		condition: "count(get_terms(['taxonomy' => 'kind', 'hide_empty' => false])) >= 40",
	},
	{
		name: 'xfn-directory',
		plugin: 'link-extension-for-xfn',
		condition: "get_page_by_path('xfn-demo') instanceof WP_Post",
	},
	{
		name: 'post-formats-directory',
		plugin: 'post-formats-for-block-themes',
		condition: "count(get_terms(['taxonomy' => 'post_format', 'hide_empty' => true])) >= 9",
	},
];

async function prepare() {
	for (const spec of specs) {
		const source = spec.url || `https://wordpress.org/plugins/wp-json/plugins/v1/plugin/${spec.plugin}/blueprint.json`;
		const response = await fetch(source, { signal: AbortSignal.timeout(20000) });
		if (!response.ok) throw new Error(`${source} returned ${response.status}`);
		const blueprint = await response.json();
		blueprint.steps.push({
			step: 'runPHP',
			code: `<?php
require '/wordpress/wp-load.php';
require_once ABSPATH . 'wp-admin/includes/plugin.php';
if (!is_plugin_active('${spec.plugin}/${spec.plugin}.php') || !(${spec.condition})) {
	throw new RuntimeException('${spec.name} content or activation check failed');
}
file_put_contents('/proof/${spec.name}.ok', "${spec.name} passed\n");`,
		});
		await fs.writeFile(path.join(process.env.PREVIEW_RECEIPTS, `${spec.name}.json`), JSON.stringify(blueprint));
	}
}

prepare().catch((error) => {
	console.error(error);
	process.exitCode = 1;
});
