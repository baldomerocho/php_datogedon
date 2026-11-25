<?php
/** Synthetic articles, never installed in production. */
$text='<p>'.str_repeat('Este párrafo permite revisar la lectura y navegar por las secciones con claridad. ',12).'</p>';
$content='<p>Introducción antes del índice.</p><h3>Antes de empezar</h3>'.$text.'<h2 id="manual">Cómo empezar</h2>'.$text.'<h3>Qué medir</h3>'.$text.'<h2>Resultados</h2>'.$text.'<h2>Resultados</h2>'.$text.'<h2><span id="historical">Final</span></h2>'.$text;
foreach(array('toc-fixture'=>$content,'toc-short-fixture'=>'<h2>Uno</h2><p>Una noticia breve.</p><h2>Dos</h2><p>Sin índice innecesario.</p><h2>Tres</h2>','toc-disabled-fixture'=>'[no_toc]'.$content,'toc-forced-fixture'=>'<p>Inicio.</p>[toc label="Secciones" start="2"]<h2>Uno</h2><p>Contenido.</p><h2>Dos</h2>') as $slug=>$body) {
    $existing=get_page_by_path($slug,OBJECT,'post');
    wp_insert_post(array('ID'=>$existing?$existing->ID:0,'post_type'=>'post','post_name'=>$slug,'post_title'=>'Prueba de navegación '.$slug,'post_status'=>'publish','post_content'=>$body,'post_author'=>1,'post_category'=>array(get_category_by_slug('web')->term_id)));
}
WP_CLI::success('Article navigation fixtures prepared.');
