<?php
/**
 * Article navigation. Render-time only: stored content and permalinks stay intact.
 * Legacy fragment normalization adapted from TOC+ (GPL-2.0+), Michael Tran/AIOSEO.
 */
defined('ABSPATH') || exit;

/** Preserve TOC+ fragment conventions, including legacy capitalization and suffixes. */
function datogedon_reader_toc_fragment($heading, $options, &$collisions) {
    $id=trim(wp_strip_all_tags($heading));
    $id=remove_accents($id);
    $id=str_replace(array("\r","\n","\n\r","\r\n"),' ',$id);
    $id=str_replace('&amp;','',$id);
    $id=preg_replace('/[^a-zA-Z0-9 \-_]*/','',$id);
    $id=rtrim(str_replace(array('  ',' '),'_',$id),'-_');
    if($options['lowercase'])$id=strtolower($id);
    if($id==='')$id=$options['fragment_prefix']?:'_';
    if($options['hyphenate'])$id=str_replace('--','-',str_replace('_','-',$id));
    if(isset($collisions[$id])){ $collisions[$id]++;return $id.'-'.$collisions[$id]; }
    $collisions[$id]=1;return $id;
}

function datogedon_reader_toc_list($items) {
    $html='<ol>';$child=false;$parent=false;$parent_level=null;
    foreach($items as $item) {
        if($item['level']===3 && $parent && $parent_level===2) {
            if(!$child){$html.='<ol>';$child=true;}else $html.='</li>';
        } else {
            if($child){$html.='</li></ol>';$child=false;}
            if($parent)$html.='</li>';
            $parent=true;$parent_level=$item['level'];
        }
        $html.='<li><a href="#'.esc_attr(rawurlencode($item['id'])).'">'.esc_html($item['text']).'</a>';
    }
    if($child)$html.='</li></ol>';
    if($parent)$html.='</li>';
    return $html.'</ol>';
}

/** Pure rendering entry point, also used for compatibility tests. */
function datogedon_reader_toc_build($content) {
    if(preg_match('/<details\b[^>]*\bdata-datogedon-toc(?:[\s=>])/',$content))return $content;
    $disabled=strpos($content,'<!--datogedon-no-toc-->')!==false;
    $content=str_replace('<!--datogedon-no-toc-->','',$content);
    $forced=preg_match('/<!--datogedon-toc:([A-Za-z0-9+\/=]+)-->/',$content,$marker);
    $attributes=$forced?json_decode(base64_decode($marker[1]),true):array();
    if(!is_array($attributes))$attributes=array();
    // Hide literal examples, scripts and comments while locating actual headings.
    $protected=array();$prefix='DATOGEDON_TOC_'.substr(hash('sha256',$content),0,16).'_';
    $content=preg_replace_callback('~<(pre|code|script|style|textarea|svg|template)\b[^>]*>.*?</\1\s*>|<!--(?!datogedon-toc:).*?-->~is',function($match)use(&$protected,$prefix){
        $key=$prefix.count($protected).'_END';$protected[$key]=$match[0];return $key;
    },$content);
    // Reserve existing IDs across the entire article, including manually authored spans.
    $ids=array_fill_keys(array('primary','masthead','colophon','comments','respond','commentform','main-nav'),true);$tokens=new WP_HTML_Tag_Processor(strtr($content,$protected));
    while($tokens->next_tag())if(is_string($id=$tokens->get_attribute('id'))&&$id!=='')$ids[$id]=true;
    $options=wp_parse_args((array)get_option('toc-options',array()),array('lowercase'=>false,'hyphenate'=>false,'fragment_prefix'=>'i'));
    $items=array();$collisions=array();
    $content=preg_replace_callback('~<h([1-6])\b[^>]*>.*?</h\1\s*>~is',function($match)use(&$items,&$collisions,&$ids,$options,$protected){
        $html=strtr($match[0],$protected);
        if(!preg_match('~^(<h([1-6])\b[^>]*>)(.*)(</h\2\s*>)$~is',$html,$parts))return $html;
        $text=trim(html_entity_decode(wp_strip_all_tags($parts[3]),ENT_QUOTES|ENT_HTML5,'UTF-8'));
        $text=preg_replace('/\s+/u',' ',$text);if($text==='')return $html;
        $legacy=datogedon_reader_toc_fragment($html,$options,$collisions);
        $tag=new WP_HTML_Tag_Processor($parts[1]);$tag->next_tag();$id=$tag->get_attribute('id');$alias='';
        // An existing heading ID takes precedence; old generated fragments remain aliases.
        if(!is_string($id)||$id==='') {
            $inside=new WP_HTML_Tag_Processor($parts[3]);$has_legacy=false;
            while($inside->next_tag())if($inside->get_attribute('id')===$legacy)$has_legacy=true;
            $id=$legacy;
            if(!$has_legacy){
                $suffix=2;while(isset($ids[$id]))$id=$legacy.'-'.$suffix++;
                $tag->set_attribute('id',$id);$ids[$id]=true;
            }
        } elseif($id!==$legacy&&!isset($ids[$legacy])) {
            $alias='<span class="article-anchor" id="'.esc_attr($legacy).'" aria-hidden="true"></span>';$ids[$legacy]=true;
        }
        $tag->set_attribute('data-article-heading','');
        if($tag->get_attribute('tabindex')===null)$tag->set_attribute('tabindex','-1');
        if(in_array((int)$parts[2],array(2,3),true)) {
            $items[]=array('id'=>$id,'text'=>$text,'level'=>(int)$parts[2]);
        }
        $result=$tag->get_updated_html().$alias.$parts[3].$parts[4];
        return count($items)===1&&in_array((int)$parts[2],array(2,3),true)?'<!--datogedon-toc-first-heading-->'.$result:$result;
    },$content);
    $content=strtr($content,$protected);
    $words=preg_match_all('/[\p{L}\p{N}]+/u',wp_strip_all_tags($content));
    $threshold=max(2,min(20,(int)($attributes['start']??3)));
    $show=!$disabled&&count($items)>=$threshold&&($forced||$words>=500);
    $show=(bool)apply_filters('datogedon_reader_show_toc',$show,count($items),$words);
    $toc='';
    if($show && $items) {
        $label=trim(wp_strip_all_tags((string)($attributes['label']??'En este artículo')))?:'En este artículo';
        $toc='<details class="article-toc" data-datogedon-toc data-nosnippet><summary><span>'.esc_html($label).'</span><span class="article-toc-count">'.count($items).' secciones</span></summary><nav aria-label="Secciones del artículo">'.datogedon_reader_toc_list($items).'</nav></details>';
    }
    if($forced){
        $inserted=false;
        $content=preg_replace_callback('/<!--datogedon-toc:[A-Za-z0-9+\/=]+-->/',function()use(&$inserted,$toc){if($inserted)return '';$inserted=true;return $toc;},$content);
    }
    return str_replace('<!--datogedon-toc-first-heading-->',$forced?'':$toc,$content);
}

add_action('init',function(){
    // Allow the old plugin to own its shortcodes until the deployment disables it.
    if(shortcode_exists('toc'))return;
    add_shortcode('toc',function($attributes){if(is_feed()||doing_filter('get_the_excerpt')||defined('REST_REQUEST')&&REST_REQUEST)return '';return '<!--datogedon-toc:'.base64_encode(wp_json_encode((array)$attributes)).'-->';});
    add_shortcode('no_toc',function(){if(is_feed()||doing_filter('get_the_excerpt')||defined('REST_REQUEST')&&REST_REQUEST)return '';return '<!--datogedon-no-toc-->';});
});
add_filter('the_content',function($content){
    if(is_admin()||is_feed()||!is_singular(array('post','page'))||!in_the_loop()||!is_main_query()||doing_filter('get_the_excerpt')||defined('REST_REQUEST')&&REST_REQUEST)return $content;
    if(in_array('table-of-contents-plus/toc.php',(array)get_option('active_plugins',array()),true))return $content;
    return datogedon_reader_toc_build($content);
},100);

/** Invoked only by the deployment CLI, with the previous plugin state journaled. */
function datogedon_reader_toc_migrate() {
    $plugin='table-of-contents-plus/toc.php';
    require_once ABSPATH.'wp-admin/includes/plugin.php';
    if(is_plugin_active_for_network($plugin))return new WP_Error('toc_network','La tabla anterior está activa para la red; requiere una migración de red.');
    if(!is_plugin_active($plugin))return true;
    foreach((array)get_option('sidebars_widgets',array()) as $sidebar=>$widgets) {
        if($sidebar==='wp_inactive_widgets')continue;
        foreach((array)$widgets as $widget)if(is_string($widget)&&strpos($widget,'toc-widget-')===0)return new WP_Error('toc_widget','Hay un widget de TOC+ en uso; migrarlo antes de desactivar el plugin.');
    }
    global $wpdb;
    $entries=$wpdb->get_results("SELECT ID, post_content FROM {$wpdb->posts} WHERE post_type IN ('post','page') AND post_status NOT IN ('trash','auto-draft')");
    foreach($entries as $entry)if(preg_match('/\[sitemap(?:_pages|_categories|_posts)?(?=[\s\]\/])/i',$entry->post_content))return new WP_Error('toc_sitemap','Hay shortcodes de sitemap en uso; migrarlos antes de desactivar TOC+.');
    deactivate_plugins($plugin,true);
    return true;
}
