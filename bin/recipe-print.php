<?php

if ( ! class_exists( 'WPRM_Recipe_Saver' ) ) {
	WP_CLI::error( 'Activate WP Recipe Maker before seeding the print cases.' );
}

foreach ( [ 'edge-recipe-public', 'edge-recipe-locked' ] as $slug ) {
	$parent = get_page_by_path( $slug, OBJECT, 'post' );
	if ( ! $parent ) {
		WP_CLI::error( "Import the WXR first. Missing post: $slug." );
	}

	$recipe_slug = 'wprm-' . $slug;
	$recipe      = get_page_by_path( $recipe_slug, OBJECT, 'wprm_recipe' );
	$recipe_id   = $recipe ? $recipe->ID : WPRM_Recipe_Saver::create_recipe(
		[
			'name'        => 'Fixture tomato soup',
			'summary'     => 'Synthetic recipe for testing the print route.',
			'post_status' => 'publish',
			'image_id'    => get_post_thumbnail_id( $parent ),
		]
	);
	if ( ! $recipe_id || is_wp_error( $recipe_id ) ) {
		WP_CLI::error( "Could not create recipe for $slug." );
	}

	wp_update_post( [ 'ID' => $recipe_id, 'post_name' => $recipe_slug ] );
	$shortcode = '[wprm-recipe id="' . $recipe_id . '"]';
	if ( ! str_contains( $parent->post_content, $shortcode ) ) {
		wp_update_post( [ 'ID' => $parent->ID, 'post_content' => $parent->post_content . "\n\n" . $shortcode ] );
	}
	update_post_meta( $recipe_id, 'wprm_parent_post_id', $parent->ID );
	WP_CLI::log( $slug . ': /' . WPRM_Print::slug() . '/' . $recipe_id . '/' );
}
