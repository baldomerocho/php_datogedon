<?php get_header(); ?>
<main id="primary" class="site-main container">
<?php if (is_home() && !is_paged()) : ?>
<header class="home-hero">
<p class="eyebrow">DATOGEDON · Diario de desarrollo</p>
<h1 class="home-hero-title">Programar con IA, en la práctica</h1>
<p class="home-hero-description">Problemas reales, decisiones técnicas y lo que aprendemos creando aplicaciones con asistentes de IA.</p>
<div class="home-hero-search"><?php get_search_form(); ?></div>
<p class="hero-links"><a href="<?php echo esc_url(home_url('/experiencias-con-ia/')); ?>">Explorar experiencias</a><a href="<?php echo esc_url(home_url('/temas/')); ?>">Ver temas</a></p>
</header>
<?php endif; ?>
<div class="feed-layout">
<?php if (have_posts()) : $position=0; while (have_posts()) : the_post();
set_query_var('datogedon_featured', is_home() && !is_paged() && $position===0);
get_template_part('template-parts/card'); $position++; endwhile; ?>
<nav class="pagination" aria-label="Paginación de entradas"><?php the_posts_pagination(array('mid_size'=>1,'prev_text'=>'← Anteriores','next_text'=>'Siguientes →')); ?></nav>
<?php else : ?><h1>No hay artículos disponibles</h1><?php endif; ?>
</div></main><?php get_footer(); ?>
