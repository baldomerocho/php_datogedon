<?php get_header();$edition=is_home() && !is_paged(); ?>
<main id="primary" class="site-main container<?php echo $edition?' home-edition':''; ?>">
<?php if($edition):get_template_part('template-parts/home');else: ?>
<div class="feed-layout">
<?php if(have_posts()):while(have_posts()):the_post();set_query_var('datogedon_featured',false);get_template_part('template-parts/card');endwhile; ?>
<nav class="pagination" aria-label="Paginación de entradas"><?php the_posts_pagination(array('mid_size'=>1,'prev_text'=>'← Anteriores','next_text'=>'Siguientes →')); ?></nav>
<?php else: ?><h1>No hay artículos disponibles</h1><?php endif; ?>
</div>
<?php endif; ?></main><?php get_footer(); ?>
