<?php
/** Synthetic discussion for isolated CI/local WordPress, never run against production. */
$post=isset($args[0])?get_post((int)$args[0]):get_page_by_path('integracion-ia-1',OBJECT,'post');
if(!$post)WP_CLI::error('Synthetic article not found.');
update_option('thread_comments',1);update_option('thread_comments_depth',5);update_option('page_comments',0);
wp_update_post(array('ID'=>$post->ID,'comment_status'=>'open'));
$parent=0;
for($depth=1;$depth<=5;$depth++){
    $parent=wp_insert_comment(array('comment_post_ID'=>$post->ID,'comment_parent'=>$parent,'comment_author'=>$depth===3?'Autor de la entrada':'Lector '.$depth,'comment_author_email'=>'fixture@example.invalid','user_id'=>$depth===3?(int)$post->post_author:0,'comment_content'=>$depth===4?'<p>Un enlace largo debe mantenerse dentro de la tarjeta: https://example.invalid/'.str_repeat('example',60).'</p>':'<p>Una experiencia de desarrollo y una pregunta para continuar la conversación.</p>','comment_approved'=>1,'comment_date'=>sprintf('2026-11-24 10:%02d:00',$depth),'comment_date_gmt'=>sprintf('2026-11-24 16:%02d:00',$depth)));
}
wp_insert_comment(array('comment_post_ID'=>$post->ID,'comment_author'=>'Otra conversación','comment_author_email'=>'fixture@example.invalid','comment_content'=>'<p>Un comentario independiente.</p><ol><li>Primer punto.</li><li>Segundo punto.</li></ol>','comment_approved'=>1));
wp_insert_comment(array('comment_post_ID'=>$post->ID,'comment_author'=>'Pendiente no público','comment_author_email'=>'pending@example.invalid','comment_content'=>'Texto pendiente que no debe mostrarse al visitante.','comment_approved'=>0));
WP_CLI::success('Synthetic five-level discussion ready.');
