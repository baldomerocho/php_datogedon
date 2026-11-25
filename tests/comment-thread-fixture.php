<?php
/** Synthetic discussion for isolated CI/local WordPress, never run against production. */
$post=isset($args[0])?get_post((int)$args[0]):get_page_by_path('integracion-ia-1',OBJECT,'post');
if(!$post)WP_CLI::error('Synthetic article not found.');
update_option('thread_comments',1);update_option('thread_comments_depth',5);update_option('page_comments',0);
wp_update_post(array('ID'=>$post->ID,'comment_status'=>'open'));
$parent=0;$first=0;
for($depth=1;$depth<=5;$depth++){
    $parent=wp_insert_comment(array('comment_post_ID'=>$post->ID,'comment_parent'=>$parent,'comment_author'=>$depth===3?'Autor de la entrada':'Lector '.$depth,'comment_author_email'=>'fixture@example.invalid','user_id'=>$depth===3?(int)$post->post_author:0,'comment_content'=>$depth===4?'<p>Un enlace largo debe mantenerse dentro de la tarjeta: https://example.invalid/'.str_repeat('example',60).'</p>':'<p>Una experiencia de desarrollo y una pregunta para continuar la conversación.</p>','comment_approved'=>1,'comment_date'=>sprintf('2026-11-24 10:%02d:00',$depth),'comment_date_gmt'=>sprintf('2026-11-24 16:%02d:00',$depth)));
    if($depth===1)$first=$parent;
}
wp_insert_comment(array('comment_post_ID'=>$post->ID,'comment_author'=>'Otra conversación','comment_author_email'=>'fixture@example.invalid','comment_content'=>'<p>Un comentario independiente.</p><ol><li>Primer punto.</li><li>Segundo punto.</li></ol>','comment_approved'=>1));
$pending=wp_insert_comment(array('comment_post_ID'=>$post->ID,'comment_author'=>'Pendiente no público','comment_author_email'=>'pending@example.invalid','comment_content'=>'Texto pendiente que no debe mostrarse al visitante.','comment_approved'=>0));
update_post_meta($post->ID,'_datogedon_featured_comment',$pending);
if(datogedon_featured_comment($post->ID)!==null)WP_CLI::error('Pending comment leaked into featured selection.');
update_post_meta($post->ID,'_datogedon_featured_comment',$first);
if(!datogedon_featured_comment($post->ID))WP_CLI::error('Approved featured comment missing.');
$other=get_posts(array('post_type'=>'post','post__not_in'=>array($post->ID),'numberposts'=>1));
if($other){
    $other_id=$other[0]->ID;$had=metadata_exists('post',$other_id,'_datogedon_featured_comment');$old=get_post_meta($other_id,'_datogedon_featured_comment',true);
    update_post_meta($other_id,'_datogedon_featured_comment',$first);
    $leaked=datogedon_featured_comment($other_id)!==null;
    if($had)update_post_meta($other_id,'_datogedon_featured_comment',$old);else delete_post_meta($other_id,'_datogedon_featured_comment');
    if($leaked)WP_CLI::error('Featured comment crossed article boundaries.');
}
update_post_meta($post->ID,'_datogedon_discussion_question','¿Qué decisión le dejarías a la IA y cuál revisarías tú?');
if(datogedon_discussion_question($post->ID)!=='¿Qué decisión le dejarías a la IA y cuál revisarías tú?')WP_CLI::error('Custom question missing.');
WP_CLI::success('Synthetic five-level discussion ready.');
