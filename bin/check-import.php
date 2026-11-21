<?php

require_once '/wordpress/wp-load.php';
require_once ABSPATH . 'wp-admin/includes/plugin.php';

function fixture_assert( $condition, $message ) {
	if ( ! $condition ) {
		throw new RuntimeException( $message );
	}
}

function fixture_block_names( $blocks ) {
	$names = [];
	foreach ( $blocks as $block ) {
		if ( $block['blockName'] ) {
			$names[] = $block['blockName'];
			array_push( $names, ...fixture_block_names( $block['innerBlocks'] ) );
		}
	}
	return $names;
}

$manifests = array_merge(
	glob( '/fixtures/cases/xfn/*.json' ),
	glob( '/fixtures/cases/post-formats/*/*.json' )
);
$count = 0;
foreach ( $manifests as $path ) {
	if ( str_ends_with( $path, '.expected.json' ) ) {
		continue;
	}

	$case     = json_decode( file_get_contents( $path ), true, 512, JSON_THROW_ON_ERROR );
	$stem     = substr( $path, 0, -5 );
	$expected = json_decode( file_get_contents( $stem . '.expected.json' ), true, 512, JSON_THROW_ON_ERROR );
	$id       = $case['id'];
	$target   = $expected['prerequisites'];
	fixture_assert( get_bloginfo( 'version' ) === $target['wordpress'], 'Wrong WordPress version.' );
	$theme = wp_get_theme();
	fixture_assert( $theme->get_stylesheet() === $target['theme'] &&
		$theme->get( 'Version' ) === $target['themeVersion'], 'Wrong theme or theme version.' );
	foreach ( $target['plugins'] as $slug => $version ) {
		$plugin = "$slug/$slug.php";
		fixture_assert( is_plugin_active( $plugin ), "Inactive plugin $slug." );
		$data = get_plugin_data( WP_PLUGIN_DIR . '/' . $plugin );
		fixture_assert( $data['Version'] === $version, "Wrong version for $slug." );
	}

	$post = get_page_by_path( $id, OBJECT, 'post' );
	fixture_assert( $post instanceof WP_Post, "Missing post $id." );
	$input = file_get_contents( $stem . '.html' );
	foreach ( $case['attachments'] ?? [] as $media ) {
		$attachment = get_page_by_path( pathinfo( $media['file'], PATHINFO_FILENAME ), OBJECT, 'attachment' );
		fixture_assert( $attachment instanceof WP_Post, "Missing attachment {$media['file']}." );
		$file = get_attached_file( $attachment->ID );
		$url  = wp_get_attachment_url( $attachment->ID );
		fixture_assert( is_readable( $file ), "Unreadable attachment {$media['file']}." );
		fixture_assert( $attachment->post_mime_type === $media['mime'], "Wrong MIME type for {$media['file']}." );
		fixture_assert( $attachment->post_excerpt === ( $media['caption'] ?? '' ), "Wrong caption for {$media['file']}." );
		if ( isset( $media['alt'] ) ) {
			fixture_assert( get_post_meta( $attachment->ID, '_wp_attachment_image_alt', true ) === $media['alt'],
				"Wrong alt text for {$media['file']}." );
		}
		$input = str_replace( 'https://example.test/wp-content/uploads/indieweb-fixtures/' . $media['file'], $url, $input );
	}
	fixture_assert( trim( $post->post_content ) === trim( $input ), "Unexpected stored content for $id." );
	fixture_assert( get_post_format( $post ) === ( $case['format'] ?? false ), "Wrong post format for $id." );
	if ( isset( $expected['assertions']['afterImport']['blocks'] ) ) {
		$names = fixture_block_names( parse_blocks( $post->post_content ) );
		fixture_assert( $names === $expected['assertions']['afterImport']['blocks'], "Wrong parsed blocks for $id." );
	}
	echo "Imported $id\n";
	++$count;
}
fixture_assert( $count === 10, "Expected 10 first-batch cases, imported $count." );
