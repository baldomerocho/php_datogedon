<?php get_header(); ?><main id="primary" class="site-main container"><div class="feed-layout">
<header class="archive-header"><?php datogedon_reader_breadcrumbs(); the_archive_title('<h1 class="archive-title">','</h1>'); the_archive_description('<div class="archive-description">','</div>'); ?></header>
<?php if(have_posts()): while(have_posts()):the_post();set_query_var('datogedon_featured',false);get_template_part('template-parts/card');endwhile; ?>
<nav class="pagination" aria-label="Paginación de entradas"><?php the_posts_pagination(array('prev_text'=>'← Anteriores','next_text'=>'Siguientes →')); ?></nav>
<?php else: ?><p>Aún no hay artículos en este tema.</p><?php endif; ?></div></main><?php get_footer(); ?>
