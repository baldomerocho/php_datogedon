<?php
/**
 * Datogedon Reader functions and definitions
 */

require_once get_template_directory().'/inc/contents.php';

if ( ! function_exists( 'datogedon_reader_setup' ) ) :
    function datogedon_reader_setup() {
        // Let WordPress manage the document title
        add_theme_support( 'title-tag' );

        // Enable post thumbnails / featured images
        add_theme_support( 'post-thumbnails' );

        // Add support for custom logo
        add_theme_support( 'custom-logo', array(
            'height'      => 60,
            'width'       => 200,
            'flex-width'  => true,
            'flex-height' => true,
        ) );

        // Enable clean HTML5 markup
        add_theme_support( 'html5', array(
            'search-form',
            'comment-form',
            'comment-list',
            'gallery',
            'caption',
            'style',
            'script',
        ) );

        // Add automatic feed links
        add_theme_support( 'automatic-feed-links' );

        // Register navigation menus
        register_nav_menus( array(
            'primary' => __( 'Primary Menu', 'datogedon-reader' ),
        ) );
    }
endif;
add_action( 'after_setup_theme', 'datogedon_reader_setup' );

/**
 * Enqueue scripts and styles.
 */
function datogedon_reader_scripts() {
    // Enqueue Google Fonts
    wp_enqueue_style( 'datogedon-reader-fonts', 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Merriweather:ital,wght@0,300;0,400;0,700;1,300;1,400&display=swap', array(), null );

    // Avoid caching issues using file modification time as version (Cache Busting)
    $css_path = get_stylesheet_directory() . '/style.css';
    $js_path = get_stylesheet_directory() . '/js/theme.js';
    
    $css_version = file_exists( $css_path ) ? filemtime( $css_path ) : '1.0.1';
    $js_version = file_exists( $js_path ) ? filemtime( $js_path ) : '1.0.1';

    // Stylesheet
    wp_enqueue_style( 'datogedon-reader-style', get_stylesheet_uri(), array(), $css_version );

    if (is_singular() && comments_open() && get_option('thread_comments')) wp_enqueue_script('comment-reply');

    // JavaScript
    wp_enqueue_script( 'datogedon-reader-js', get_template_directory_uri() . '/js/theme.js', array(), $js_version, true );
    wp_enqueue_script( 'datogedon-analytics', get_template_directory_uri() . '/js/analytics.js', array('datogedon-reader-js'), filemtime(get_template_directory() . '/js/analytics.js'), true );
}
add_action( 'wp_enqueue_scripts', 'datogedon_reader_scripts' );

/**
 * Remove unused code and bloat (WPO & Security)
 */
function datogedon_reader_cleanup() {
    // Emojis
    remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
    remove_action( 'wp_print_styles', 'print_emoji_styles' );
    remove_action( 'admin_print_scripts', 'print_emoji_detection_script' );
    remove_action( 'admin_print_styles', 'print_emoji_styles' );

    // Meta links
    remove_action( 'wp_head', 'rsd_link' );
    remove_action( 'wp_head', 'wlwmanifest_link' );
    remove_action( 'wp_head', 'wp_generator' );
    remove_action( 'wp_head', 'wp_shortlink_wp_head' );
    remove_action( 'wp_head', 'rest_output_link_wp_head', 10 );
    remove_action( 'wp_head', 'wp_oembed_add_discovery_links', 10 );
}
add_action( 'init', 'datogedon_reader_cleanup' );

/**
 * Render JSON-LD Structured Data (Only if no SEO plugin is active to avoid duplicates)
 */
function datogedon_reader_structured_data() {
    // If Rank Math or Yoast is active, they handle JSON-LD. Let's exit.
    if ( class_exists( 'RankMath' ) || defined( 'WPSEO_VERSION' ) ) {
        return;
    }

    $schema = array();

    if ( is_front_page() || is_home() ) {
        $schema[] = array(
            '@context' => 'https://schema.org',
            '@type' => 'WebSite',
            'name' => get_bloginfo( 'name' ),
            'url' => home_url(),
            'potentialAction' => array(
                '@type' => 'SearchAction',
                'target' => home_url( '/?s={search_term_string}' ),
                'query-input' => 'required name=search_term_string'
            )
        );
    }

    if ( is_single() ) {
        global $post;
        $schema[] = array(
            '@context' => 'https://schema.org',
            '@type' => 'BlogPosting',
            'headline' => get_the_title(),
            'image' => get_the_post_thumbnail_url( $post->ID, 'full' ),
            'datePublished' => get_the_date( 'c' ),
            'dateModified' => get_the_modified_date( 'c' ),
            'author' => array(
                '@type' => 'Person',
                'name' => get_the_author(),
                'url' => get_author_posts_url( get_the_author_meta( 'ID' ) )
            ),
            'publisher' => array(
                '@type' => 'Organization',
                'name' => get_bloginfo( 'name' ),
                'logo' => array(
                    '@type' => 'ImageObject',
                    'url' => get_site_icon_url()
                )
            ),
            'description' => wp_strip_all_tags( get_the_excerpt() )
        );
    }

    if ( ! empty( $schema ) ) {
        foreach ( $schema as $data ) {
            echo '<script type="application/ld+json">' . json_encode( $data ) . '</script>' . "\n";
        }
    }
}
add_action( 'wp_head', 'datogedon_reader_structured_data' );

/**
 * Estimate reading time of content
 */
function datogedon_reader_reading_time( $content ) {
    $word_count = str_word_count( strip_tags( $content ) );
    $reading_time = ceil( $word_count / 200 ); // Average speed: 200 words per minute
    return $reading_time;
}

/**
 * Filter site title tags for proper SEO hierarchy (Only 1 H1 per page)
 */
function datogedon_reader_get_site_title_html() {
    $title = get_bloginfo( 'name' );
    $url = esc_url( home_url( '/' ) );
    
    if ( ( is_front_page() || is_home() ) && is_paged() ) {
        return sprintf( '<h1 class="site-title"><a href="%s" class="logo-link">%s</a></h1>', $url, $title );
    } else {
        return sprintf( '<div class="site-title"><a href="%s" class="logo-link">%s</a></div>', $url, $title );
    }
}

/**
 * Fallback menu that displays top categories and home page link
 */
function datogedon_reader_menu_fallback() {
    $categories = get_categories( array(
        'number'  => 5,
        'orderby' => 'count',
        'order'   => 'DESC',
    ) );
    echo '<ul id="primary-menu" class="menu">';
    echo '<li><a href="' . esc_url( home_url( '/' ) ) . '">' . __( 'Inicio', 'datogedon-reader' ) . '</a></li>';
    if ( ! empty( $categories ) && ! is_wp_error( $categories ) ) {
        foreach ( $categories as $category ) {
            echo '<li><a href="' . esc_url( get_category_link( $category->term_id ) ) . '">' . esc_html( $category->name ) . '</a></li>';
        }
    }
    echo '</ul>';
}

/**
 * Render Breadcrumbs (Supports Rank Math and custom fallback)
 */
function datogedon_reader_breadcrumbs() {
    if(is_front_page()||is_home()) return;
    echo '<nav class="breadcrumbs" aria-label="Ruta de navegación"><a href="'.esc_url(home_url('/')).'">Inicio</a>';
    if(is_single() && function_exists('datogedon_primary_category')) {
        $category=datogedon_primary_category(get_queried_object_id());
        if($category) echo '<span aria-hidden="true"> / </span><a href="'.esc_url(get_category_link($category->term_id)).'">'.esc_html($category->name).'</a>';
    } elseif(is_category()) echo '<span aria-hidden="true"> / </span><span>'.esc_html(single_cat_title('',false)).'</span>';
    echo '</nav>';
}

function datogedon_reader_related_posts() {
    $category=function_exists('datogedon_primary_category')?datogedon_primary_category(get_the_ID()):null;
    $args=array('post_type'=>'post','post_status'=>'publish','posts_per_page'=>3,'post__not_in'=>array(get_the_ID()),'ignore_sticky_posts'=>true);
    if($category) $args['category__in']=array($category->term_id);
    $related=new WP_Query($args);
    if($related->have_posts()) {
        echo '<aside class="related-posts" aria-label="Artículos relacionados"><h2>Seguir leyendo</h2><ul>';
        while($related->have_posts()) {$related->the_post();echo '<li data-post-id="'.(int)get_the_ID().'"><a href="'.esc_url(get_permalink()).'">'.esc_html(get_the_title()).'</a></li>';}
        echo '</ul></aside>';wp_reset_postdata();
    }
}

/**
 * Add aria-haspopup and aria-expanded to menu items that have children
 */
function datogedon_reader_menu_link_attributes( $atts, $item, $args, $depth ) {
    if ( in_array( 'menu-item-has-children', $item->classes ) || in_array( 'page_item_has_children', $item->classes ) ) {
        $atts['aria-haspopup'] = 'true';
        $atts['aria-expanded'] = 'false';
    }
    return $atts;
}
add_filter( 'nav_menu_link_attributes', 'datogedon_reader_menu_link_attributes', 10, 4 );

/**
 * Dynamically inject alt tags to content images if they are missing or empty
 */
function datogedon_reader_fallback_image_alt( $content ) {
    if ( ! is_single() && ! is_page() ) {
        return $content;
    }

    $title = get_the_title();

    // Scan for img tags and insert/replace empty alt text
    return preg_replace_callback( '/<img\s+([^>]*)\/?>/i', function( $matches ) use ( $title ) {
        $img_attributes = $matches[1];

        // Check if alt attribute exists
        if ( preg_match( '/\balt\s*=\s*(["\'])(.*?)\1/i', $img_attributes, $alt_match ) ) {
            $alt_value = trim( $alt_match[2] );
            if ( empty( $alt_value ) ) {
                // If alt is empty, replace it with post title
                $img_attributes = preg_replace( '/\balt\s*=\s*(["\'])(.*?)\1/i', 'alt="' . esc_attr( $title ) . '"', $img_attributes );
            }
        } else {
            // If alt doesn't exist, append it
            $img_attributes .= ' alt="' . esc_attr( $title ) . '"';
        }

        return '<img ' . $img_attributes . '>';
    }, $content );
}
// Preserve intentional empty alt attributes on decorative images.

/**
 * Basic SEO meta description fallback when no major SEO plugin is active
 */
function datogedon_reader_meta_description() {
    if ( class_exists( 'RankMath' ) || defined( 'WPSEO_VERSION' ) ) {
        return;
    }
    if ( is_single() || is_page() ) {
        global $post;
        $excerpt = wp_strip_all_tags( get_the_excerpt( $post ) );
        if ( ! empty( $excerpt ) ) {
            echo '<meta name="description" content="' . esc_attr( wp_trim_words( $excerpt, 30, '' ) ) . '">' . "\n";
        }
    } elseif ( is_front_page() || is_home() ) {
        $description = get_bloginfo( 'description' );
        if ( ! empty( $description ) ) {
            echo '<meta name="description" content="' . esc_attr( $description ) . '">' . "\n";
        }
    }
}
add_action( 'wp_head', 'datogedon_reader_meta_description', 1 );

/**
 * Get attachment alt text or fallback to post title
 */
function datogedon_reader_get_post_thumbnail_alt( $post_id = null ) {
    $post_id = $post_id ? $post_id : get_the_ID();
    $thumbnail_id = get_post_thumbnail_id( $post_id );
    if ( $thumbnail_id ) {
        $alt = get_post_meta( $thumbnail_id, '_wp_attachment_image_alt', true );
        if ( ! empty( trim( $alt ) ) ) {
            return $alt;
        }
    }
    return the_title_attribute( array( 'echo' => false, 'post' => $post_id ) );
}

/**
 * Register search REST API route
 */
function datogedon_reader_register_search_route() {
    register_rest_route( 'datogedon-reader/v1', '/search', array(
        'methods'             => WP_REST_Server::READABLE,
        'callback'            => 'datogedon_reader_ajax_search_handler',
        'permission_callback' => '__return_true',
    ) );
}
add_action( 'rest_api_init', 'datogedon_reader_register_search_route' );

/**
 * Handle AJAX search with Redis caching
 */
function datogedon_reader_ajax_search_handler( $request ) {
    $query = sanitize_text_field( $request->get_param( 'q' ) );
    if ( empty( trim( $query ) ) ) {
        return new WP_REST_Response( array(), 200 );
    }

    $cache_key = 'datogedon_search_' . md5( strtolower( trim( $query ) ) );
    $cached_results = wp_cache_get( $cache_key, 'datogedon_search' );

    if ( false !== $cached_results ) {
        $response = new WP_REST_Response( $cached_results, 200 );
        $response->header( 'X-Datogedon-Cache', 'HIT' );
        return $response;
    }

    $search_query = new WP_Query( array(
        's'                   => $query,
        'posts_per_page'      => 8,
        'post_status'         => 'publish',
        'post_type'           => 'post',
        'ignore_sticky_posts' => true,
    ) );

    $results = array();

    if ( $search_query->have_posts() ) {
        while ( $search_query->have_posts() ) {
            $search_query->the_post();
            $post_id = get_the_ID();
            
            $thumb_url = get_the_post_thumbnail_url( $post_id, 'thumbnail' );
            
            $results[] = array(
                'id'        => $post_id,
                'title'     => get_the_title(),
                'permalink' => get_permalink(),
                'date'      => get_the_date(),
                'thumbnail' => $thumb_url ? $thumb_url : '',
            );
        }
        wp_reset_postdata();
    }

    wp_cache_set( $cache_key, $results, 'datogedon_search', HOUR_IN_SECONDS );

    $response = new WP_REST_Response( $results, 200 );
    $response->header( 'X-Datogedon-Cache', 'MISS' );
    return $response;
}

/**
 * Exclude main theme stylesheet from LiteSpeed Cache optimization (minify/combine)
 */
function datogedon_reader_exclude_style_from_litespeed( $tag, $handle, $src, $media ) {
    if ( 'datogedon-reader-style' === $handle ) {
        $tag = str_replace( '<link ', '<link data-no-optimize="1" ', $tag );
    }
    return $tag;
}
add_filter( 'style_loader_tag', 'datogedon_reader_exclude_style_from_litespeed', 10, 4 );

/**
 * Exclude main theme script from LiteSpeed Cache optimization (minify/combine/defer)
 */
function datogedon_reader_exclude_script_from_litespeed( $tag, $handle, $src ) {
    if ( in_array($handle, array('datogedon-reader-js','datogedon-analytics'), true) ) {
        $tag = str_replace( '<script ', '<script data-no-optimize="1" ', $tag );
    }
    return $tag;
}
add_filter( 'script_loader_tag', 'datogedon_reader_exclude_script_from_litespeed', 10, 3 );

/** Keep native comment IDs, permalinks, threading and moderation behavior. */
function datogedon_reader_comment($comment, $args, $depth) {
    $GLOBALS['comment']=$comment;
    require get_template_directory().'/template-parts/comment.php';
}
