<?php
/**
 * Plugin Name: Datogedon Site
 * Description: Identidad, navegación y estructura editorial independientes del tema.
 * Version: 1.1.0
 * License: GPL-2.0-or-later
 */
defined('ABSPATH') || exit;

function datogedon_category_url($term) {
    if (is_numeric($term)) $term = get_term((int) $term, 'category');
    if (!$term || is_wp_error($term)) return home_url('/');
    $slugs = array();
    foreach (array_reverse(get_ancestors($term->term_id, 'category', 'taxonomy')) as $id) {
        $parent = get_term($id, 'category');
        if ($parent && !is_wp_error($parent)) $slugs[] = $parent->slug;
    }
    $slugs[] = $term->slug;
    return home_url('/category/' . implode('/', $slugs) . '/');
}
add_filter('category_link', function ($url, $id) { return datogedon_category_url($id); }, 100, 2);

add_action('template_redirect', function () {
    if (is_admin() || is_feed() || is_preview()) return;
    $path = rawurldecode(parse_url(isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '/', PHP_URL_PATH));
    if (is_category()) {
        $url = datogedon_category_url(get_queried_object());
        if (is_paged()) $url .= user_trailingslashit('page/' . (int)get_query_var('paged'), 'paged');
        if (untrailingslashit($path) !== untrailingslashit(parse_url($url, PHP_URL_PATH))) {
            wp_safe_redirect($url, 301, 'Datogedon'); exit;
        }
    }
    if (is_404()) {
        $redirects = get_option('datogedon_category_redirects', array());
        $key = '/' . trim($path, '/') . '/';
        if (isset($redirects[$key])) { wp_safe_redirect(home_url($redirects[$key]), 301, 'Datogedon'); exit; }
        if (preg_match('~^(.*?/)((?:page/[1-9][0-9]*|feed(?:/(?:rss2|rss|atom|rdf))?)/)$~', $key, $match) && isset($redirects[$match[1]])) {
            wp_safe_redirect(home_url($redirects[$match[1]] . $match[2]), 301, 'Datogedon'); exit;
        }
    }
});
add_filter('rank_math/frontend/canonical', function ($url) {
    return is_category() && !is_paged() ? datogedon_category_url(get_queried_object()) : $url;
});

// This plugin echoes sitemap directives after core has filtered robots.txt.
// Keep the XML generator; let our single robots filter own its declaration.
add_action('init', function () {
    remove_action('do_robots', array('GoogleSitemapGeneratorLoader', 'call_do_robots'), 100);
}, 100);
add_filter('robots_txt', function ($text, $public) {
    if (!$public) return $text;
    $text = preg_replace('/^\s*Sitemap:[^\r\n]*(?:\r?\n|$)/mi', '', $text);
    return rtrim($text) . "\n\nSitemap: " . home_url('/sitemap.xml') . "\n";
}, 100, 2);

function datogedon_primary_category($post_id) {
    $primary = (int) get_post_meta($post_id, 'rank_math_primary_category', true);
    if ($primary && has_term($primary, 'category', $post_id)) return get_term($primary, 'category');
    $categories = get_the_category($post_id);
    if (!$categories) return null;
    // WordPress's existing permalink is authoritative; match its category path.
    $path = parse_url(get_permalink($post_id), PHP_URL_PATH);
    foreach ($categories as $category) {
        if (strpos($path, '/' . $category->slug . '/') !== false) return $category;
    }
    return $categories[0];
}

add_filter('rank_math/json_ld', function ($data) {
    foreach ($data as &$node) {
        if (!is_array($node)) continue;
        $types = isset($node['@type']) ? (array) $node['@type'] : array();
        if (in_array('WebSite', $types, true)) $node['name'] = get_bloginfo('name');
        if (is_author() && in_array('CollectionPage', $types, true)) {
            $node['@type'] = 'ProfilePage';
            $node['mainEntity'] = array('@id'=>get_author_posts_url(get_queried_object_id()).'#person');
        }
        if (isset($node['@id']) && $node['@id'] === home_url('/#person')) {
            $owner = get_user_by('id', (int) get_option('datogedon_owner_user_id', 0));
            if ($owner) {
                $node['@type'] = 'Person';
                $node['name'] = $owner->display_name;
                $node['url'] = get_author_posts_url($owner->ID);
            }
        }
        if (is_single() && in_array('Person', $types, true) && isset($node['@id']) && strpos($node['@id'], '#author') !== false) {
            $node['url'] = get_author_posts_url((int) get_post_field('post_author', get_queried_object_id()));
        }
        if (is_page('acerca-de') && (in_array('Article', $types, true) || in_array('BlogPosting', $types, true))) {
            unset($node['@type']);
        }
        if (is_page('acerca-de') && in_array('WebPage', $types, true)) $node['@type'] = 'AboutPage';
    }
    unset($node);
    if (is_author()) {
        $author = get_queried_object();
        $data['datogedon_author'] = array('@type'=>'Person','@id'=>get_author_posts_url($author->ID).'#person','name'=>$author->display_name,'url'=>get_author_posts_url($author->ID),'description'=>get_the_author_meta('description',$author->ID));
    }
    if (is_single() || is_page() || is_category()) {
        $items = array(array('@type'=>'ListItem','position'=>1,'name'=>'Inicio','item'=>home_url('/')));
        if (is_single()) {
            $category = datogedon_primary_category(get_queried_object_id());
            if ($category) $items[] = array('@type'=>'ListItem','position'=>count($items)+1,'name'=>$category->name,'item'=>datogedon_category_url($category));
        }
        $label = is_category() ? single_cat_title('',false) : get_the_title(get_queried_object_id());
        $url = is_category() ? datogedon_category_url(get_queried_object()) : get_permalink(get_queried_object_id());
        $items[] = array('@type'=>'ListItem','position'=>count($items)+1,'name'=>$label,'item'=>$url);
        $id = $url . '#breadcrumb';
        foreach ($data as $key => &$node) {
            if (!is_array($node)) continue;
            $types = isset($node['@type']) ? (array)$node['@type'] : array();
            if (in_array('BreadcrumbList',$types,true)) unset($data[$key]);
            if (in_array('WebPage',$types,true) || in_array('AboutPage',$types,true)) $node['breadcrumb'] = array('@id'=>$id);
        }
        unset($node);
        $data['datogedon_breadcrumb'] = array('@type'=>'BreadcrumbList','@id'=>$id,'itemListElement'=>$items);
    }
    // Remove the redundant Article node on About; keep its WebPage and identity.
    foreach ($data as $key => $node) {
        if (is_array($node) && !isset($node['@type']) && isset($node['headline'])) unset($data[$key]);
    }
    return $data;
}, 99);

function datogedon_home_social_image($url) {
    return (is_front_page() || is_home()) ? get_template_directory_uri().'/assets/social.png' : $url;
}
add_filter('rank_math/opengraph/facebook/image','datogedon_home_social_image');
add_filter('rank_math/opengraph/twitter/image','datogedon_home_social_image');

add_action('pre_get_posts', function ($query) {
    if (!is_admin() && $query->is_main_query() && ($query->is_home() || $query->is_archive())) $query->set('posts_per_page', 12);
});

add_shortcode('datogedon_topics', function () {
    $terms = get_terms(array('taxonomy' => 'category', 'hide_empty' => true, 'orderby' => 'count', 'order' => 'DESC'));
    if (is_wp_error($terms)) return '';
    $html = '<ul class="topic-directory">';
    foreach ($terms as $term) {
        if ($term->slug === 'sin-categoria' || $term->slug === 'uncategorized') continue;
        $html .= '<li><a href="' . esc_url(datogedon_category_url($term)) . '">' . esc_html($term->name) . '</a><span>' . (int) $term->count . ' artículos</span></li>';
    }
    return $html . '</ul>';
});
add_shortcode('datogedon_experiences', function () {
    $query = new WP_Query(array('post_type' => 'post', 'post_status' => 'publish', 'category_name' => 'inteligencia-artificial', 'posts_per_page' => 12));
    ob_start();
    while ($query->have_posts()) { $query->the_post();
        echo '<article class="post-card"><h2><a href="' . esc_url(get_permalink()) . '">' . esc_html(get_the_title()) . '</a></h2><p>' . esc_html(wp_trim_words(get_the_excerpt(), 32)) . '</p></article>';
    }
    wp_reset_postdata();
    $term = get_category_by_slug('inteligencia-artificial');
    if ($term) echo '<p><a href="' . esc_url(datogedon_category_url($term)) . '">Ver todas las experiencias y artículos sobre IA →</a></p>';
    return ob_get_clean();
});

if (defined('WP_CLI') && WP_CLI) {
    WP_CLI::add_command('datogedon configure', function ($args, $assoc) {
        $owner_id = isset($assoc['owner']) ? (int) $assoc['owner'] : 0;
        $owner = get_user_by('id', $owner_id);
        if (!$owner) WP_CLI::error('Indica un autor existente mediante --owner=ID.');
        update_option('datogedon_owner_user_id', $owner_id);
        // Native free-mode option: no account or API key is required.
        update_option('rank_math_registration_skip', true);
        $titles = get_option('rank-math-options-titles', array());
        $titles['knowledgegraph_name'] = $owner->display_name;
        $titles['website_name'] = get_bloginfo('name');
        $titles['knowledgegraph_type'] = 'person';
        $titles['disable_author_archives'] = 'off';
        $titles['author_custom_robots'] = 'on';
        $titles['author_robots'] = array('index');
        $titles['homepage_title'] = 'DATOGEDON | Desarrollo de software con IA';
        $titles['homepage_description'] = 'Experiencias reales programando aplicaciones con inteligencia artificial: problemas, decisiones técnicas y colaboración entre personas y asistentes de IA.';
        $titles['open_graph_image'] = get_template_directory_uri().'/assets/social.png';
        update_option('rank-math-options-titles', $titles);
        $general = get_option('rank-math-options-general', array());
        $general['breadcrumbs'] = 'on';
        $general['strip_category_base'] = 'off';
        update_option('rank-math-options-general', $general);
        $redirects = array();
        foreach (get_categories(array('hide_empty' => false)) as $term) {
            $target = parse_url(datogedon_category_url($term), PHP_URL_PATH);
            $redirects[str_replace('/category/', '/', $target)] = $target;
        }
        update_option('datogedon_category_redirects', $redirects);
        $pages = array(
            'experiencias-con-ia' => array('Experiencias con IA', '<p>Problemas reales de desarrollo, decisiones técnicas y lo que aprendemos al trabajar con asistentes de inteligencia artificial.</p>[datogedon_experiences]'),
            'temas' => array('Temas de desarrollo', '<p>Explora experiencias, soluciones y apuntes por tecnología.</p>[datogedon_topics]'),
            'politica-editorial' => array('Política editorial', '<p>Publicamos experiencias reales de desarrollo. Cada relato distingue las condiciones y decisiones humanas de las propuestas y acciones de la IA.</p><h2>Evidencia y privacidad</h2><p>Los resultados se describen según lo que se pudo verificar. No publicamos credenciales, conversaciones originales ni datos privados de clientes. Identificamos herramientas y modelos cuando existe un registro suficiente.</p><h2>Autoría e imágenes</h2><p>El autor humano responde por la revisión del artículo. La asistencia de IA se reconoce cuando corresponde. Usamos imágenes propias o recursos con licencia comprobada y los créditos adecuados.</p><h2>Correcciones y colaboraciones</h2><p>Las propuestas se revisan antes de publicarse. Puedes solicitar una corrección o proponer una experiencia desde <a href="/contacto/">Contacto</a>.</p>'),
            'colabora' => array('Colabora con Datogedon', '<p>Comparte una experiencia real creando o manteniendo software con ayuda de IA.</p><h2>Qué contar</h2><p>Describe el problema, las condiciones que definiste, las decisiones del asistente, tus intervenciones y el resultado comprobado. Preferimos relatos breves y concretos.</p><h2>Cómo proponer un artículo</h2><p>Envía el tema y un resumen desde <a href="/contacto/">Contacto</a>. Revisaremos contigo el borrador antes de programarlo. No necesitas compartir código privado ni conversaciones completas.</p><p>Consulta nuestra <a href="/politica-editorial/">política editorial</a>.</p>')
        );
        $about = get_page_by_path('acerca-de');
        if ($about) wp_update_post(array('ID'=>$about->ID,'post_content'=>'<p>Datogedon es el blog de ' . esc_html($owner->display_name) . ' sobre desarrollo de software y trabajo con inteligencia artificial.</p><p>Comparto experiencias creando y manteniendo aplicaciones: el problema, las condiciones que definí, las decisiones del asistente y el resultado que pudimos comprobar.</p><p>El archivo también conserva tutoriales y apuntes sobre desarrollo móvil, web, bases de datos e infraestructura.</p><p><a href="/experiencias-con-ia/">Explora las experiencias con IA</a> o consulta nuestra <a href="/politica-editorial/">política editorial</a>.</p>'));
        $ids = array();
        foreach ($pages as $slug => $page) {
            $existing = get_page_by_path($slug);
            $post = array('post_type' => 'page', 'post_name' => $slug, 'post_title' => $page[0], 'post_content' => $page[1], 'post_status' => 'publish', 'post_author' => $owner_id);
            if ($existing) $post['ID'] = $existing->ID;
            $id = wp_insert_post($post, true);
            if (is_wp_error($id)) WP_CLI::error($id->get_error_message());
            $ids[$slug] = $id;
        }
        $menu = wp_get_nav_menu_object('Datogedon editorial');
        $menu_id = $menu ? $menu->term_id : wp_create_nav_menu('Datogedon editorial');
        foreach ((array) wp_get_nav_menu_items($menu_id) as $item) wp_delete_post($item->ID, true);
        $items = array('Inicio' => home_url('/'), 'Experiencias con IA' => get_permalink($ids['experiencias-con-ia']), 'Temas' => get_permalink($ids['temas']), 'Acerca de' => home_url('/acerca-de/'), 'Colabora' => get_permalink($ids['colabora']));
        foreach ($items as $label => $url) wp_update_nav_menu_item($menu_id, 0, array('menu-item-title' => $label, 'menu-item-url' => $url, 'menu-item-status' => 'publish', 'menu-item-type' => 'custom'));
        $locations = get_theme_mod('nav_menu_locations', array()); $locations['primary'] = $menu_id; set_theme_mod('nav_menu_locations', $locations);
        flush_rewrite_rules(false);
        WP_CLI::success('Estructura editorial configurada sin cambiar categorías ni permalinks de artículos.');
    });
}
