<?php
/**
 * Plugin Name: Datogedon Editorial MCP
 * Description: Capacidades MCP para borradores, programación y miniaturas del diario de desarrollo.
 * Version: 0.1.0
 * Requires at least: 6.9
 * Requires PHP: 7.4
 * Requires Plugins: mcp-adapter
 */
defined('ABSPATH') || exit;

add_action('wp_abilities_api_categories_init', function () {
    wp_register_ability_category('datogedon-editorial', ['label' => 'Editorial Datogedon', 'description' => 'Entradas y miniaturas del diario.']);
});

add_action('wp_abilities_api_init', function () {
    wp_register_ability('datogedon/save-post', [
        'label' => 'Guardar o programar entrada editorial',
        'description' => 'Crea o actualiza por editorial_id un borrador o una entrada futura. Reutiliza IDs al reintentar. Fechas en zona local de WordPress.',
        'category' => 'datogedon-editorial',
        'input_schema' => ['type' => 'object', 'additionalProperties' => false, 'required' => ['editorial_id','title','content','status'], 'properties' => [
            'editorial_id' => ['type' => 'string', 'minLength' => 1, 'maxLength' => 100],
            'title' => ['type' => 'string', 'minLength' => 1], 'content' => ['type' => 'string'],
            'excerpt' => ['type' => 'string'], 'slug' => ['type' => 'string'],
            'status' => ['type' => 'string', 'enum' => ['draft','future']],
            'date' => ['type' => 'string', 'description' => 'YYYY-MM-DD HH:MM:SS, zona del sitio.'],
            'featured_media' => ['type' => 'integer', 'minimum' => 1],
            'categories' => ['type' => 'array', 'items' => ['type' => 'integer', 'minimum' => 1]],
            'tags' => ['type' => 'array', 'items' => ['type' => 'integer', 'minimum' => 1]],
            'seo_title' => ['type' => 'string'], 'seo_description' => ['type' => 'string'], 'focus_keyword' => ['type' => 'string'],
        ]],
        'permission_callback' => function () { return current_user_can('edit_posts'); },
        'execute_callback' => function ($p) {
            $key = sanitize_text_field($p['editorial_id']);
            $existing = get_posts(['post_type' => 'post', 'post_status' => ['draft','pending','future','publish','private'], 'meta_key' => '_datogedon_editorial_id', 'meta_value' => $key, 'posts_per_page' => 2, 'fields' => 'ids']);
            if (count($existing) > 1) return new WP_Error('duplicate_key', 'Hay entradas duplicadas para esta clave.');
            $id = $existing ? $existing[0] : 0;
            if ($id && (!current_user_can('edit_post', $id) || get_post_status($id) === 'publish')) return new WP_Error('locked_post', 'Entrada publicada o sin permiso de edición.');
            $post = ['post_type' => 'post', 'post_title' => sanitize_text_field($p['title']), 'post_content' => wp_kses_post($p['content']), 'post_status' => $p['status']];
            if ($id) $post['ID'] = $id;
            if (isset($p['excerpt'])) $post['post_excerpt'] = sanitize_textarea_field($p['excerpt']);
            if (isset($p['slug'])) $post['post_name'] = sanitize_title($p['slug']);
            if ($p['status'] === 'future') {
                if (!current_user_can('publish_posts')) return new WP_Error('forbidden', 'Sin permiso para programar.');
                $date = isset($p['date']) ? DateTimeImmutable::createFromFormat('!Y-m-d H:i:s', $p['date'], wp_timezone()) : false;
                if (!$date || $date->format('Y-m-d H:i:s') !== $p['date'] || $date->getTimestamp() <= time()+60) return new WP_Error('invalid_date', 'Fecha futura válida requerida, con zona horaria de WordPress.');
                if (empty($p['featured_media'])) return new WP_Error('missing_image', 'Una entrada programada necesita miniatura.');
                $post['post_date'] = $date->format('Y-m-d H:i:s');
                $post['post_date_gmt'] = $date->setTimezone(new DateTimeZone('UTC'))->format('Y-m-d H:i:s');
            }
            if (isset($p['featured_media'])) {
                if (!current_user_can('edit_post', $p['featured_media']) || !wp_attachment_is_image($p['featured_media'])) return new WP_Error('invalid_image', 'Imagen no válida o sin permiso.');
            }
            foreach (['categories' => 'category','tags' => 'post_tag'] as $field => $taxonomy) {
                if (!isset($p[$field])) continue;
                $tax = get_taxonomy($taxonomy);
                if (!current_user_can($tax->cap->assign_terms)) return new WP_Error('forbidden_terms', 'Sin permiso para asignar términos.');
                foreach ($p[$field] as $term) if (!term_exists((int)$term, $taxonomy)) return new WP_Error('invalid_term', 'Término inexistente.');
            }
            $id = wp_insert_post(wp_slash($post), true);
            if (is_wp_error($id)) return $id;
            update_post_meta($id, '_datogedon_editorial_id', $key);
            if (isset($p['featured_media'])) set_post_thumbnail($id, $p['featured_media']);
            foreach (['categories' => 'category','tags' => 'post_tag'] as $field => $taxonomy) if (isset($p[$field])) wp_set_post_terms($id, array_map('intval',$p[$field]),$taxonomy);
            foreach (['seo_title' => 'rank_math_title','seo_description' => 'rank_math_description','focus_keyword' => 'rank_math_focus_keyword'] as $field => $meta) if (isset($p[$field])) update_post_meta($id,$meta,sanitize_text_field($p[$field]));
            return ['id' => $id, 'status' => get_post_status($id), 'date' => get_post_field('post_date',$id), 'url' => get_permalink($id), 'timezone' => wp_timezone_string()];
        },
        'meta' => ['mcp' => ['public' => true], 'public' => true],
    ]);

    wp_register_ability('datogedon/upload-thumbnail', [
        'label' => 'Subir miniatura editorial', 'description' => 'Sube una imagen de hasta 2 MB y guarda título y texto alternativo. Reutiliza editorial_id al reintentar.',
        'category' => 'datogedon-editorial',
        'input_schema' => ['type' => 'object', 'additionalProperties' => false, 'required' => ['editorial_id','filename','base64','title','alt'], 'properties' => [
            'editorial_id' => ['type' => 'string', 'minLength' => 1, 'maxLength' => 100],
            'filename' => ['type' => 'string'], 'base64' => ['type' => 'string', 'maxLength' => 2800000], 'title' => ['type' => 'string'], 'alt' => ['type' => 'string'],
        ]],
        'permission_callback' => function () { return current_user_can('upload_files'); },
        'execute_callback' => function ($p) {
            $key = sanitize_text_field($p['editorial_id']);
            $found = get_posts(['post_type'=>'attachment','post_status'=>'inherit','meta_key'=>'_datogedon_thumbnail_id','meta_value'=>$key,'fields'=>'ids','posts_per_page'=>1]);
            if ($found) {
                if (!current_user_can('edit_post',$found[0])) return new WP_Error('forbidden','Sin permiso sobre la imagen existente.');
                return ['id'=>$found[0],'url'=>wp_get_attachment_url($found[0])];
            }
            $bytes = base64_decode($p['base64'],true);
            if (!$bytes || strlen($bytes)>2097152) return new WP_Error('invalid_image','Imagen inválida o demasiado grande.');
            $info = @getimagesizefromstring($bytes);
            if (!$info || !in_array($info['mime'],['image/webp','image/jpeg','image/png'],true)) return new WP_Error('invalid_format','Solo WebP, JPEG o PNG.');
            $filename = sanitize_file_name($p['filename']);
            $type = wp_check_filetype($filename);
            if (empty($type['type']) || $type['type'] !== $info['mime']) return new WP_Error('invalid_extension','Extensión incompatible con la imagen.');
            $upload = wp_upload_bits($filename,null,$bytes);
            if (!empty($upload['error'])) return new WP_Error('upload_failed',$upload['error']);
            $id = wp_insert_attachment(['post_title'=>sanitize_text_field($p['title']),'post_mime_type'=>$info['mime'],'post_status'=>'inherit'],$upload['file'],0,true);
            if (is_wp_error($id)) { wp_delete_file($upload['file']); return $id; }
            require_once ABSPATH.'wp-admin/includes/image.php';
            wp_update_attachment_metadata($id,wp_generate_attachment_metadata($id,$upload['file']));
            update_post_meta($id,'_wp_attachment_image_alt',sanitize_text_field($p['alt']));
            update_post_meta($id,'_datogedon_thumbnail_id',$key);
            return ['id'=>$id,'url'=>wp_get_attachment_url($id)];
        },
        'meta' => ['mcp' => ['public' => true], 'public' => true],
    ]);
});
