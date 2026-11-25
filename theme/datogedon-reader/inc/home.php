<?php
/** Partition the main page without losing or repeating its posts. */
function datogedon_reader_home_kind($post) {
    if (has_term('noticias','post_tag',$post) || get_post_meta($post->ID,'_datogedon_kind',true)==='news') return 'news';
    if (get_post_meta($post->ID,'_datogedon_kind',true)==='experience' || get_post_meta($post->ID,'_datogedon_editorial_id',true)) return 'experience';
    return 'article';
}
function datogedon_reader_home_sections($posts) {
    $news=array();$experiences=array();
    foreach($posts as $post) {
        $kind=datogedon_reader_home_kind($post);
        if($kind==='news')$news[]=$post;
        elseif($kind==='experience')$experiences[]=$post;
    }
    $cover=$news?array_slice($news,0,4):array_slice($posts,0,4);
    $shown=array_map(fn($post)=>(int)$post->ID,$cover);
    $experiences=array_slice(array_values(array_filter($experiences,fn($post)=>!in_array((int)$post->ID,$shown,true))),0,3);
    $shown=array_merge($shown,array_map(fn($post)=>(int)$post->ID,$experiences));
    return array('cover'=>$cover,'news'=>(bool)$news,'experiences'=>$experiences,'more'=>array_values(array_filter($posts,fn($post)=>!in_array((int)$post->ID,$shown,true))));
}
