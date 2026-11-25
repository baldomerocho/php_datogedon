<?php
/** Main-query composition and template state; only synthetic local fixtures. */
if(wp_parse_url(home_url(),PHP_URL_HOST)!=='127.0.0.1')WP_CLI::error('Isolated CI only.');
$ids=array();
try {
    for($i=0;$i<12;$i++)$ids[]=wp_insert_post(array('post_title'=>'Synthetic home '.$i,'post_status'=>'publish','post_content'=>'A concise synthetic excerpt.'));
    $posts=array_map('get_post',$ids);
    $news_tag=term_exists('noticias','post_tag');if(!$news_tag)$news_tag=wp_insert_term('Noticias','post_tag',array('slug'=>'noticias'));
    wp_set_post_terms($ids[0],array((int)$news_tag['term_id']),'post_tag');
    update_post_meta($ids[1],'_datogedon_kind','news');
    for($i=2;$i<=6;$i++)update_post_meta($ids[$i],'_datogedon_editorial_id','synthetic-'.$i);
    $groups=datogedon_reader_home_sections($posts);
    if(!$groups['news'] || array_map(fn($post)=>$post->ID,$groups['cover'])!==array_slice($ids,0,2))throw new RuntimeException('News was not promoted by tag and kind');
    if(count($groups['experiences'])!==3)throw new RuntimeException('Experience selection missing');
    $shown=array_merge($groups['cover'],$groups['experiences'],$groups['more']);
    $seen=array_map(fn($post)=>(int)$post->ID,$shown);sort($seen);$expected=$ids;sort($expected);
    if($seen!==$expected || count(array_unique($seen))!==12)throw new RuntimeException('Homepage lost or repeated a main-query post');
    foreach($ids as $id){wp_set_post_terms($id,array(),'post_tag');delete_post_meta($id,'_datogedon_kind');delete_post_meta($id,'_datogedon_editorial_id');}
    $fallback=datogedon_reader_home_sections($posts);
    if($fallback['news'] || count($fallback['cover'])!==4 || count($fallback['more'])!==8)throw new RuntimeException('No-news fallback failed');
    foreach($ids as $id)update_post_meta($id,'_datogedon_kind','news');
    $all_news=datogedon_reader_home_sections($posts);
    if(count($all_news['cover'])!==4 || count($all_news['more'])!==8 || $all_news['experiences'])throw new RuntimeException('News-only page lost overflow');
    if(datogedon_reader_home_sections(array())['cover'])throw new RuntimeException('Empty page failed');
    $original=$GLOBALS['post']??null;
    ob_start();get_template_part('template-parts/home-story',null,array('post'=>$posts[0],'variant'=>'lead'));$html=ob_get_clean();
    if(($GLOBALS['post']??null)!==$original)throw new RuntimeException('Card changed the global post');
    if(!str_contains($html,'data-post-id="'.$ids[0].'"') || !str_contains($html,'<h3'))throw new RuntimeException('Card semantics missing');
    WP_CLI::success('Home classification, no-news/empty/news-only states, complete main page and global template state verified.');
}finally{foreach($ids as $id)wp_delete_post($id,true);}
