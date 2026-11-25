<?php
global $wp_query;
$sections=datogedon_reader_home_sections($wp_query->posts);
$news_term=get_term_by('slug','noticias','post_tag');
$news_url=$news_term?get_term_link($news_term):false;
if(is_wp_error($news_url))$news_url=false;
?>
<header class="home-hero edition-intro">
<div><p class="edition-kicker">Software, inteligencia artificial y desarrollo</p><h1>Actualidad tecnológica.<br>Desarrollo en la práctica.</h1></div>
<div class="edition-intro-side"><p>Noticias para entender qué cambia. Experiencias para ver cómo lo resolvemos creando aplicaciones con IA.</p><div class="edition-search"><?php get_search_form(); ?></div></div>
</header>
<nav class="edition-channels hero-links" aria-label="Explorar Datogedon">
<?php if($news_url): ?><a href="<?php echo esc_url($news_url); ?>">Noticias <span aria-hidden="true">↗</span></a><?php endif; ?>
<a href="<?php echo esc_url(home_url('/experiencias-con-ia/')); ?>">Experiencias con IA <span aria-hidden="true">↗</span></a>
<a href="<?php echo esc_url(home_url('/temas/')); ?>">Todos los temas <span aria-hidden="true">↗</span></a>
<span class="edition-channel-note">El problema. Las decisiones. Lo aprendido.</span>
</nav>
<?php if($sections['cover']): ?>
<section class="edition-section edition-top" aria-labelledby="home-news-title">
<div class="edition-section-head"><h2 id="home-news-title"><?php echo $sections['news']?'Noticias':'En portada'; ?></h2><?php if($sections['news'] && $news_url): ?><a class="edition-section-link" href="<?php echo esc_url($news_url); ?>">Todas las noticias <span aria-hidden="true">→</span></a><?php endif; ?></div>
<div class="edition-top-grid<?php echo count($sections['cover'])===1?' edition-top-grid--solo':''; ?>">
<?php get_template_part('template-parts/home-story',null,array('post'=>$sections['cover'][0],'variant'=>'lead')); ?>
<?php if(count($sections['cover'])>1): ?><div class="edition-headlines"><p class="edition-rail-label">También en portada</p><?php foreach(array_slice($sections['cover'],1) as $story):get_template_part('template-parts/home-story',null,array('post'=>$story,'variant'=>'rail'));endforeach; ?></div><?php endif; ?>
</div>
</section>
<?php endif; ?>
<?php if($sections['experiences']): ?>
<section class="edition-section edition-experiences" aria-labelledby="home-experiences-title">
<div class="edition-section-head"><div><p class="edition-kicker">El diario de desarrollo</p><h2 id="home-experiences-title">Experiencias con IA</h2></div><a class="edition-section-link" href="<?php echo esc_url(home_url('/experiencias-con-ia/')); ?>">Explorar experiencias <span aria-hidden="true">→</span></a></div>
<p class="edition-section-description">Problemas reales, decisiones humanas y soluciones construidas con asistentes de IA.</p>
<div class="edition-story-grid"><?php foreach($sections['experiences'] as $story):get_template_part('template-parts/home-story',null,array('post'=>$story,'variant'=>'grid'));endforeach; ?></div>
</section>
<?php endif; ?>
<?php
$topics=get_terms(array('taxonomy'=>'category','hide_empty'=>true,'slug'=>array('flutter','inteligencia-artificial','web','wordpress','entornos-de-desarrollo','herramientas'),'orderby'=>'count','order'=>'DESC','number'=>6));
if(!is_wp_error($topics) && $topics): ?>
<section class="edition-topics" aria-labelledby="home-topics-title"><div><p class="edition-kicker">Encuentra tu próxima lectura</p><h2 id="home-topics-title">Explora por tema</h2></div><ul><?php foreach($topics as $topic): ?><li><a href="<?php echo esc_url(get_category_link($topic)); ?>"><?php echo esc_html($topic->name); ?><span aria-hidden="true">↗</span></a></li><?php endforeach; ?></ul></section>
<?php endif; ?>
<?php if($sections['more']): ?>
<section class="edition-section" aria-labelledby="home-more-title"><div class="edition-section-head"><h2 id="home-more-title">Más para leer</h2><span class="edition-section-note">Del archivo de Datogedon</span></div><div class="edition-more-grid"><?php foreach($sections['more'] as $story):get_template_part('template-parts/home-story',null,array('post'=>$story,'variant'=>'list'));endforeach; ?></div></section>
<?php endif; ?>
<?php if(!$sections['cover']): ?><p>Aún no hay artículos disponibles.</p><?php endif; ?>
<div class="edition-pagination"><?php the_posts_pagination(array('mid_size'=>1,'prev_text'=>'← Anteriores','next_text'=>'Más artículos →','screen_reader_text'=>'Paginación de artículos')); ?></div>
<aside class="edition-about"><p class="edition-kicker">Detrás de Datogedon</p><h2>Cómo trabajamos con IA</h2><p>Documentamos el problema, las decisiones del asistente y las intervenciones humanas, con resultados y límites claros.</p><a href="<?php echo esc_url(home_url('/acerca-de/')); ?>">Conoce el blog <span aria-hidden="true">→</span></a><a href="<?php echo esc_url(home_url('/colabora/')); ?>">Escribe en Datogedon <span aria-hidden="true">→</span></a></aside>
