<?php
/** Synthetic content for CI. No production database or user credentials. */
$parent=wp_insert_term('Web','category',array('slug'=>'web'));
$web=is_wp_error($parent)?get_category_by_slug('web')->term_id:$parent['term_id'];
$ia=wp_insert_term('Inteligencia Artificial','category',array('slug'=>'inteligencia-artificial'));
$ai=is_wp_error($ia)?get_category_by_slug('inteligencia-artificial')->term_id:$ia['term_id'];
wp_update_user(array('ID'=>1,'display_name'=>'Baldomero Cho','description'=>'Desarrollo aplicaciones y comparto experiencias trabajando con asistentes de inteligencia artificial.'));
$about=wp_insert_post(array('post_type'=>'page','post_name'=>'acerca-de','post_title'=>'Acerca de','post_status'=>'publish','post_content'=>'Desarrollo de aplicaciones.','post_author'=>1));
wp_insert_post(array('post_type'=>'page','post_name'=>'contacto','post_title'=>'Contacto','post_status'=>'publish','post_content'=>'Comparte tu propuesta de artículo.','post_author'=>1));
for($i=1;$i<=15;$i++) {
    $id=wp_insert_post(array('post_title'=>'Revisar una integración con IA '.$i,'post_name'=>'integracion-ia-'.$i,'post_content'=>'<p>Definí las condiciones de una integración y revisé con el asistente cómo comprobar el resultado.</p><h2>La decisión técnica</h2><p>Contrasté la propuesta con los datos disponibles antes de aplicarla.</p>','post_status'=>'publish','post_author'=>1,'post_category'=>array($web,$ai)));
    update_post_meta($id,'rank_math_primary_category',$web);
}
update_option('permalink_structure','/%category%/%postname%/');
wp_insert_post(array('post_title'=>'Una entrada futura','post_name'=>'entrada-futura','post_status'=>'future','post_date'=>wp_date('Y-m-d H:i:s',time()+86400),'post_content'=>'Publicación programada.','post_author'=>1));
$contributor=wp_insert_user(array('user_login'=>'colaborador','user_pass'=>wp_generate_password(32),'user_email'=>'contributor@example.invalid','role'=>'contributor'));
if(is_wp_error($contributor)||user_can($contributor,'publish_posts')) throw new Exception('El colaborador no debe publicar directamente.');
WP_CLI::success('Contenido y permisos de revisión preparados.');
