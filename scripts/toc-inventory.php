<?php
/** Read-only fragment/shortcode inventory; run through wp eval-file. */
$result=array('posts'=>array(),'shortcodes'=>array(),'widgets'=>array());
$original_query=$GLOBALS['wp_query'];$original_main=$GLOBALS['wp_the_query'];$original_uri=$_SERVER['REQUEST_URI']??'';
foreach(get_posts(array('post_type'=>array('post','page'),'post_status'=>array('publish','future'),'numberposts'=>-1)) as $entry) {
    $GLOBALS['wp_query']=new WP_Query(array('p'=>$entry->ID,'post_type'=>$entry->post_type,'post_status'=>$entry->post_status));
    $GLOBALS['wp_the_query']=$GLOBALS['wp_query'];$GLOBALS['wp_query']->the_post();$_SERVER['REQUEST_URI']=wp_parse_url(get_permalink($entry),PHP_URL_PATH);
    // TOC+ keeps no_toc state on its object; emulate one fresh request per article.
    foreach(($GLOBALS['wp_filter']['the_content']->callbacks??array()) as $callbacks)foreach($callbacks as $filter) {
        $fn=$filter['function'];if(is_array($fn)&&is_object($fn[0])&&method_exists($fn[0],'extract_headings')&&method_exists($fn[0],'enable'))$fn[0]->enable();
    }
    $html=apply_filters('the_content',$entry->post_content);
    $document=new DOMDocument();$before=libxml_use_internal_errors(true);
    $document->loadHTML('<?xml encoding="UTF-8">'.$html,LIBXML_NONET|LIBXML_NOERROR|LIBXML_NOWARNING);libxml_clear_errors();libxml_use_internal_errors($before);
    $xpath=new DOMXPath($document);$ids=array();
    foreach($xpath->query('//*[@id][self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6 or ancestor::h1 or ancestor::h2 or ancestor::h3 or ancestor::h4 or ancestor::h5 or ancestor::h6]') as $node)$ids[]=$node->getAttribute('id');
    $result['posts'][]=array('id'=>$entry->ID,'url'=>get_permalink($entry),'has_toc'=>strpos($html,'data-datogedon-toc')!==false||strpos($html,'id="toc_container"')!==false,'fragments'=>array_values(array_unique($ids)));
    if(preg_match_all('/\[(toc|no_toc|sitemap(?:_pages|_categories|_posts)?)(?=[\s\]\/])[^\]]*\]/i',$entry->post_content,$matches))$result['shortcodes'][]=array('id'=>$entry->ID,'codes'=>$matches[0]);
}
foreach((array)get_option('sidebars_widgets',array()) as $sidebar=>$widgets)foreach((array)$widgets as $widget)if(is_string($widget)&&strpos($widget,'toc')!==false)$result['widgets'][]=array('sidebar'=>$sidebar,'widget'=>$widget);
$GLOBALS['wp_query']=$original_query;$GLOBALS['wp_the_query']=$original_main;$_SERVER['REQUEST_URI']=$original_uri;wp_reset_postdata();
echo wp_json_encode($result,JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE);
