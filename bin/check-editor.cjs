const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '../cases/post-formats');
const origin = 'http://127.0.0.1:9400';

async function checkFormats() {
	const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
	try {
		for (const username of ['admin', 'fixture-author']) {
			await checkEditor(browser, username);
		}
	} finally {
		await browser.close();
	}
}

async function checkEditor(browser, username) {
	const page = await browser.newPage();
	await page.goto(origin + '/wp-login.php');
	await page.locator('#user_login').fill(username);
	await page.locator('#user_pass').fill(process.env.FIXTURE_PASSWORD);
	await page.locator('#wp-submit').click();
	await page.waitForURL('**/wp-admin/**');

	for (const format of fs.readdirSync(root).sort()) {
		const folder = path.join(root, format);
		const file = fs.readdirSync(folder).find((name) => name.endsWith('.json') && !name.endsWith('.expected.json'));
		assert.ok(file, `Missing manifest for ${format}`);
		const fixture = JSON.parse(fs.readFileSync(path.join(folder, file), 'utf8'));
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
		assert.equal(reloaded.content, saved.original, `Edited content changed: ${fixture.id}`);
		assert.equal(reloaded.format || 'standard', format, fixture.id);

		const [publicPost] = await (await page.request.get(origin + '/?rest_route=/wp/v2/posts&' + query)).json();
		assert.equal(publicPost.title.rendered, saved.title, fixture.id);
		assert.equal(publicPost.content.rendered, post.content.rendered, fixture.id);
		if (format === 'audio' || format === 'video') {
			await page.goto(publicPost.link);
			const player = page.locator(`article ${format}`);
			await player.evaluate(async (media) => { await media.play(); });
			await page.waitForFunction((selector) => document.querySelector(selector)?.currentTime > 0.15, `article ${format}`);
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
