<?php

namespace IndieWebTestData;

function use_bundled_media( $response, array $args, string $url ) {
	$prefix = 'https://example.test/wp-content/uploads/indieweb-fixtures/';
	if ( ! str_starts_with( $url, $prefix ) || empty( $args['filename'] ) ) {
		return $response;
	}

	$name = substr( $url, strlen( $prefix ) );
	if ( ! in_array( $name, [ 'indieweb-night-signal.png', 'indieweb-tomato-soup.png' ], true ) ) {
		return new \WP_Error( 'indieweb_fixture_missing_media', 'This fixture has no bundled image.' );
	}

	$source = dirname( __DIR__ ) . '/media/' . $name;
	if ( ! is_readable( $source ) || ! copy( $source, $args['filename'] ) ) {
		return new \WP_Error( 'indieweb_fixture_copy_failed', 'Could not copy the bundled image.' );
	}

	return [
		'headers'  => [ 'content-length' => filesize( $source ), 'content-type' => 'image/png' ],
		'body'     => '',
		'response' => [ 'code' => 200, 'message' => 'OK' ],
		'cookies'  => [],
	];
}

\WP_CLI::add_wp_hook( 'pre_http_request', __NAMESPACE__ . '\\use_bundled_media', 10, 3 );
