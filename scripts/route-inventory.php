<?php
/** Run with wp eval-file; contains public route metadata only. */
$result=array('posts'=>array(),'categories'=>array());
foreach(get_posts(array('post_type'=>array('post','page'),'post_status'=>array('publish','future'),'numberposts'=>-1)) as $post) {
    $result['posts'][]=array('id'=>$post->ID,'status'=>$post->post_status,'url'=>get_permalink($post));
}
foreach(get_categories(array('hide_empty'=>false)) as $term) $result['categories'][]=array('id'=>$term->term_id,'url'=>get_category_link($term));
echo wp_json_encode($result,JSON_UNESCAPED_SLASHES);
