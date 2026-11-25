<?php
/**
 * Plugin Name: Datogedon Editorial MCP
 * Description: Capacidades MCP para borradores, programación y miniaturas del diario de desarrollo.
 * Version: 0.2.0
 * Requires at least: 6.9
 * Requires PHP: 8.0
 * Requires Plugins: mcp-adapter
 */
defined('ABSPATH') || exit;

add_action('wp_abilities_api_categories_init', function () {
    wp_register_ability_category('datogedon-editorial', ['label' => 'Editorial Datogedon', 'description' => 'Entradas y miniaturas del diario.']);
});

add_action('wp_abilities_api_init', function () {
    wp_register_ability('datogedon/save-post', [
        'label' => 'Guardar o programar entrada editorial',
        'description' => 'Crea o actualiza por editorial_id un borrador, una entrada futura o publica un borrador verificado. Reutiliza IDs al reintentar. Fechas en zona local de WordPress.',
        'category' => 'datogedon-editorial',
        'input_schema' => ['type' => 'object', 'additionalProperties' => false, 'required' => ['editorial_id','title','content','status'], 'properties' => [
            'editorial_id' => ['type' => 'string', 'minLength' => 1, 'maxLength' => 100],
            'title' => ['type' => 'string', 'minLength' => 1], 'content' => ['type' => 'string'],
            'author' => ['type'=>'integer','minimum'=>1],
            'kind' => ['type'=>'string','enum'=>['experience','news']],
            'source_urls' => ['type'=>'array','maxItems'=>12,'items'=>['type'=>'string','format'=>'uri']],
            'excerpt' => ['type' => 'string'], 'slug' => ['type' => 'string'],
            'status' => ['type' => 'string', 'enum' => ['draft','future','publish']],
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
            if ($id && get_post_status($id)==='publish' && $p['status']==='publish' && current_user_can('edit_post',$id)) return ['id'=>$id,'status'=>'publish','date'=>get_post_field('post_date',$id),'url'=>get_permalink($id),'timezone'=>wp_timezone_string(),'immutable'=>true];
            if ($id && (!current_user_can('edit_post', $id) || get_post_status($id) === 'publish')) return new WP_Error('locked_post', 'Entrada publicada o sin permiso de edición.');
            $post = ['post_type' => 'post', 'post_title' => sanitize_text_field($p['title']), 'post_content' => wp_kses_post($p['content']), 'post_status' => $p['status']];
            // Partial wp_insert_post updates default omitted comment_status to closed.
            // Preserve the post's explicit policy; apply the site default only on creation.
            $post['comment_status'] = $id ? get_post_field('comment_status', $id) : get_default_comment_status('post');
            if ($id) $post['ID'] = $id;
            $post['post_author']=$id?(int)get_post_field('post_author',$id):get_current_user_id();
            $kind=$p['kind']??($id?get_post_meta($id,'_datogedon_kind',true):'experience');
            if (isset($p['author'])) {
                if (!get_user_by('id',$p['author']) || ((int)$p['author']!==get_current_user_id() && !current_user_can('edit_others_posts'))) return new WP_Error('invalid_author','Autor inexistente o sin permiso de atribución.');
                $post['post_author']=(int)$p['author'];
            }
            if ($kind==='news' && (int)$post['post_author']!==135) return new WP_Error('news_author','Las noticias deben atribuirse al autor editorial 135.');
            if ($kind!=='news' && (int)$post['post_author']===135)return new WP_Error('reserved_author','El autor 135 se reserva para noticias.');
            if ($p['status']==='publish') {
                if (!current_user_can('publish_posts')) return new WP_Error('forbidden','Sin permiso para publicar.');
                if (!$id || get_post_status($id)!=='draft') return new WP_Error('draft_required','Revisar primero un borrador antes de publicar.');
                if (empty($p['featured_media']) || empty($p['categories']) || empty($p['excerpt'])) return new WP_Error('incomplete_post','Se requieren miniatura, categoría y extracto.');
                if ($kind==='news') {
                    $hosts=[];
                    foreach(($p['source_urls']??[]) as $url) {
                        if(wp_parse_url($url,PHP_URL_SCHEME)!=='https')return new WP_Error('invalid_source','Las fuentes deben usar HTTPS.');
                        $hosts[]=preg_replace('/^www\./','',strtolower((string)wp_parse_url($url,PHP_URL_HOST)));
                    }
                    if(count(array_unique(array_filter($hosts)))<2)return new WP_Error('missing_sources','Una noticia necesita al menos dos dominios fuente; el redactor debe comprobar su independencia.');
                }
                $image_id=(int)$p['featured_media'];$image=wp_get_attachment_metadata($image_id);$file=get_attached_file($image_id);
                if(get_post_mime_type($image_id)!=='image/webp' || ($image['width']??0)!==1200 || ($image['height']??0)!==630 || !get_post_meta($image_id,'_wp_attachment_image_alt',true) || !$file || !is_file($file) || filesize($file)>180*1024)return new WP_Error('incomplete_thumbnail','Miniatura WebP 1200x630, alt y hasta 180 KB requeridos.');
                $links=new WP_HTML_Tag_Processor($post['post_content']);$internal=[];$external=[];
                while($links->next_tag('a')) {
                    $href=$links->get_attribute('href');if(!is_string($href))continue;
                    $host=wp_parse_url($href,PHP_URL_HOST);$path=wp_parse_url($href,PHP_URL_PATH);
                    if($host && !in_array(strtolower($host),[strtolower(wp_parse_url(home_url(),PHP_URL_HOST)),'www.datogedon.com'],true)){$external[]=untrailingslashit($href);continue;}
                    if(!$path || str_starts_with($path,'/wp-content/'))continue;
                    $target=url_to_postid($host?$href:home_url($href));
                    if(!$target || $target===$id || !datogedon_linkable_post($target) || in_array($target,$internal,true))return new WP_Error('invalid_internal_link','Enlace interno no publicado, repetido, al propio post o no indexable.');
                    $internal[]=$target;
                }
                if(count($internal)>3)return new WP_Error('excess_internal_links','Revisar: más de tres enlaces internos.');
                if($kind==='news')foreach($p['source_urls'] as $url)if(!in_array(untrailingslashit($url),$external,true))return new WP_Error('uncited_source','Cada fuente declarada debe estar enlazada en el artículo.');
                $post['post_date']=current_time('mysql');$post['post_date_gmt']=current_time('mysql',true);
            }
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
            if(isset($p['kind']))update_post_meta($id,'_datogedon_kind',$p['kind']);
            if(isset($p['source_urls']))update_post_meta($id,'_datogedon_source_urls',array_map('esc_url_raw',$p['source_urls']));
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

/** Discover candidates; matching is a shortlist, never an instruction to force links. */
function datogedon_linkable_post($id) {
    $post=get_post($id);
    if(!$post || $post->post_type!=='post' || $post->post_status!=='publish' || $post->post_password)return false;
    $robots=(array)get_post_meta($id,'rank_math_robots',true);
    $canonical=get_post_meta($id,'rank_math_canonical_url',true);
    return !in_array('noindex',$robots,true) && (!$canonical || untrailingslashit($canonical)===untrailingslashit(get_permalink($id)));
}
add_action('wp_abilities_api_init',function(){
    wp_register_ability('datogedon/find-related-posts',[
        'label'=>'Buscar contexto para enlaces internos',
        'description'=>'Busca artículos publicados e indexables por conceptos del borrador. Devuelve candidatos con extractos; el redactor debe leerlos y decidir su relevancia, sin forzar enlaces.',
        'category'=>'datogedon-editorial',
        'input_schema'=>['type'=>'object','additionalProperties'=>false,'required'=>['query'],'properties'=>[
            'query'=>['type'=>'string','minLength'=>2,'maxLength'=>180],
            'exclude_id'=>['type'=>'integer','minimum'=>1],
            'limit'=>['type'=>'integer','minimum'=>1,'maximum'=>10],
        ]],
        'permission_callback'=>function(){return current_user_can('edit_posts');},
        'execute_callback'=>function($p){
            $text=remove_accents(mb_strtolower(wp_strip_all_tags($p['query'])));
            preg_match_all('/[\p{L}\p{N}+#.\-]{2,}/u',$text,$matches);
            $stop=['para','como','con','una','uno','los','las','del','por','que','sobre','desde','este','esta','tecnologia','noticias','the','and','with'];
            $terms=array_slice(array_values(array_diff(array_unique($matches[0]),$stop)),0,6);$pool=[];
            foreach($terms as $term){
                foreach(get_posts(['post_type'=>'post','post_status'=>'publish','s'=>$term,'posts_per_page'=>30,'orderby'=>'date','order'=>'DESC','post__not_in'=>[(int)($p['exclude_id']??0)]]) as $post)$pool[$post->ID]=$post;
            }
            $items=[];
            foreach($pool as $post){
                if(!datogedon_linkable_post($post->ID))continue;
                $title=remove_accents(mb_strtolower($post->post_title));
                $body=remove_accents(mb_strtolower(wp_strip_all_tags($post->post_content)));$score=0;$matched=[];
                foreach($terms as $term){
                    $pattern='/(?<![\p{L}\p{N}])'.preg_quote($term,'/').'(?![\p{L}\p{N}])/u';
                    if(preg_match($pattern,$title)){$score+=5;$matched[]=$term;}
                    elseif(preg_match($pattern,$body)){$score++;$matched[]=$term;}
                }
                if(!$score)continue;
                $items[]=['id'=>$post->ID,'title'=>$post->post_title,'url'=>get_permalink($post),'date'=>get_post_time('c',false,$post),'excerpt'=>wp_trim_words(wp_strip_all_tags($post->post_excerpt?:$post->post_content),100,'…'),'matched_terms'=>$matched,'score'=>$score];
            }
            usort($items,function($a,$b){return $b['score']<=>$a['score'];});
            return ['candidates'=>array_slice($items,0,$p['limit']??6),'policy'=>'Leer el destino antes de enlazar. Cero enlaces es válido. Preferir entre uno y tres solo si amplían el contexto. No enlazar por mera coincidencia de palabras.'];
        },
        'meta'=>['mcp'=>['public'=>true],'public'=>true],
    ]);
});
