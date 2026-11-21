<?php

namespace IndieWebTestData;

function use_bundled_media( $response, array $args, string $url ) {
	$prefix = 'https://example.test/wp-content/uploads/indieweb-fixtures/';
	if ( ! str_starts_with( $url, $prefix ) || empty( $args['filename'] ) ) {
		return $response;
	}

	$name = substr( $url, strlen( $prefix ) );
	$types = [
		'indieweb-night-signal.png' => 'image/png',
		'indieweb-tomato-soup.png'   => 'image/png',
		'fixture-yellow-square.png' => 'image/png',
		'fixture-cyan-stripes.png'  => 'image/png',
		'fixture-440hz.mp3'         => 'audio/mpeg',
		'fixture-color-bars.mp4'    => 'video/mp4',
		'fixture-color-bars-en.vtt' => 'text/vtt',
	];
	if ( ! isset( $types[ $name ] ) ) {
		return new \WP_Error( 'indieweb_fixture_missing_media', 'This fixture has no bundled file.' );
	}

	$source = dirname( __DIR__ ) . '/media/' . $name;
	if ( ! is_readable( $source ) || ! copy( $source, $args['filename'] ) ) {
		return new \WP_Error( 'indieweb_fixture_copy_failed', 'Could not copy the bundled file.' );
	}

	return [
		'headers'  => [ 'content-length' => filesize( $source ), 'content-type' => $types[ $name ] ],
		'body'     => '',
		'response' => [ 'code' => 200, 'message' => 'OK' ],
		'cookies'  => [],
	];
}

if ( defined( 'WP_CLI' ) && WP_CLI ) {
	\WP_CLI::add_wp_hook( 'pre_http_request', __NAMESPACE__ . '\\use_bundled_media', 10, 3 );
} else {
	add_filter( 'pre_http_request', __NAMESPACE__ . '\\use_bundled_media', 10, 3 );
}
