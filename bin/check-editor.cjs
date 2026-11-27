const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '../cases/post-formats');
const origin = 'http://127.0.0.1:9400';
const normalizeVoidTags = (html) => html.replace(/(<(?:img|source|track|br|hr)\b[^>]*?)\s*\/>/gi, '$1/>');

async function checkFormats() {
	const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
	try {
		if (process.argv[2] === 'pkiw') {
			await checkKindPanel(browser);
			return;
		}
		if (process.argv[2] === 'settings') {
			await checkSettings(browser);
			return;
		}
		for (const username of ['fixture-author', 'admin']) {
			await checkEditor(browser, username);
		}
	} finally {
		await browser.close();
	}
}

async function signIn(browser, username) {
	const page = await browser.newPage();
	await page.goto(origin + '/wp-login.php');
	await page.locator('#user_login').fill(username);
	await page.locator('#user_pass').fill(process.env.FIXTURE_PASSWORD);
	await page.locator('#wp-submit').click();
	await page.waitForURL('**/wp-admin/**');
	return page;
}

async function checkSettings(browser) {
	const page = await signIn(browser, 'admin');
	for (const [settings, name, category] of [
		['xfn-link-extension', 'XFN relationship test cases', 'xfn'],
		['pfbt-settings', 'WordPress post format test cases', 'post-formats'],
	]) {
		const response = await page.goto(`${origin}/wp-admin/options-general.php?page=${settings}`);
		assert.equal(response.status(), 200, settings);
		const link = page.getByRole('link', { name, exact: true });
		await link.waitFor({ state: 'visible' });
		assert.equal(await link.getAttribute('href'), `https://github.com/courtneyr-dev/indieweb-test-data/tree/main/cases/${category}`);
		console.log(`Verified settings link for ${settings}`);
	}
	await page.close();
}

async function checkKindPanel(browser) {
	const page = await signIn(browser, 'admin');
	await page.goto(origin + '/wp-admin/post-new.php');
	await page.waitForFunction(() => window.wp?.plugins?.getPlugin('post-kinds-indieweb-kind-selector'));
	await page.evaluate(() => {
		wp.data.dispatch('core/edit-post').openGeneralSidebar('edit-post/document');
		const panelName = 'post-kinds-indieweb-kind-selector/post-kinds-indieweb-kind-selector';
		if (!wp.data.select('core/editor').isEditorPanelOpened(panelName)) {
			wp.data.dispatch('core/editor').toggleEditorPanelOpened(panelName);
		}
	});
	const grid = page.getByRole('radiogroup', { name: 'Select post kind' });
	await grid.waitFor({ state: 'visible' });
	const reply = grid.getByRole('button', { name: 'Reply', exact: true });
	await reply.evaluate((button) => button.click());
	assert.equal(await reply.getAttribute('aria-pressed'), 'true');
	await page.waitForFunction(() => wp.data.select('core/block-editor').getBlocks()
		.some((block) => block.name === 'post-kinds-indieweb/reply-card'));
	console.log('Verified Post Kind editor panel, Reply selection, and card insertion');
	await page.close();
}

function loadCases() {
	const folders = fs.readdirSync(root).sort().map((name) => path.join(root, name));
	folders.push(path.resolve(root, '../xfn'));
	return folders.flatMap((folder) =>
		fs.readdirSync(folder).sort()
			.filter((name) => name.endsWith('.json') && !name.endsWith('.expected.json'))
			.map((name) => JSON.parse(fs.readFileSync(path.join(folder, name), 'utf8')))
	);
}

async function checkEditor(browser, username) {
	const page = await signIn(browser, username);

	for (const fixture of loadCases()) {
		const format = fixture.format || 'standard';
		const query = new URLSearchParams({ slug: fixture.id, _fields: 'id,format,title,content,link' });
		const response = await page.request.get(origin + '/?rest_route=/wp/v2/posts&' + query);
		assert.equal(response.status(), 200, fixture.id);
		const [post] = await response.json();
		assert.ok(post, `Missing imported post ${fixture.id}`);
		assert.equal(post.format, format, fixture.id);

		await page.goto(`${origin}/wp-admin/post.php?post=${post.id}&action=edit`);
		await page.waitForFunction((id) => window.wp?.data?.select('core/editor')?.getCurrentPostId?.() === id, post.id);

		const saved = await page.evaluate(async (id) => {
			const select = () => wp.data.select('core/editor');
			const original = select().getEditedPostContent();
			const title = `${select().getEditedPostAttribute('title')} (verified)`;
			const editor = wp.data.dispatch('core/editor');
			editor.editPost({ title });
			await editor.savePost();
			if (!select().didPostSaveRequestSucceed()) {
				throw new Error(`Editor save failed for post ${id}`);
			}
			return { original, title };
		}, post.id);

		await page.reload();
		await page.waitForFunction((title) => window.wp?.data?.select('core/editor')?.getEditedPostAttribute?.('title') === title, saved.title);
		const reloaded = await page.evaluate(() => ({
			content: wp.data.select('core/editor').getEditedPostContent(),
			format: wp.data.select('core/editor').getEditedPostAttribute('format'),
		}));
		assert.equal(normalizeVoidTags(reloaded.content), normalizeVoidTags(saved.original), `Edited content changed: ${fixture.id}`);
		assert.equal(reloaded.format || 'standard', format, fixture.id);

		const [publicPost] = await (await page.request.get(origin + '/?rest_route=/wp/v2/posts&' + query)).json();
		assert.equal(publicPost.title.rendered, saved.title, fixture.id);
		assert.equal(normalizeVoidTags(publicPost.content.rendered), normalizeVoidTags(post.content.rendered), fixture.id);
		if (username === 'admin' && (format === 'audio' || format === 'video')) {
			await page.goto(publicPost.link);
			const player = page.locator(format);
			await player.evaluate(async (media) => { await media.play(); });
			await page.waitForFunction((selector) => document.querySelector(selector)?.currentTime > 0.15, format);
			console.log(`${username} played ${fixture.id}`);
		}
		console.log(`${username} saved and reopened ${fixture.id}`);
	}
	await page.close();
}

checkFormats().catch((error) => {
	console.error(error);
	process.exitCode = 1;
});
