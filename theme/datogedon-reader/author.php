<?php get_header(); $author=get_queried_object(); ?>
<main id="primary" class="site-main container"><header class="author-profile">
<?php echo get_avatar($author->ID,80,'',esc_attr($author->display_name)); ?>
<div><p class="eyebrow">Autor</p><h1><?php echo esc_html($author->display_name); ?></h1><p><?php echo esc_html(get_the_author_meta('description',$author->ID)); ?></p><a href="<?php echo esc_url(home_url('/politica-editorial/')); ?>">Cómo publicamos</a></div></header>
<h2>Artículos</h2><?php while(have_posts()):the_post();set_query_var('datogedon_featured',false);get_template_part('template-parts/card');endwhile; ?>
<nav class="pagination" aria-label="Paginación de artículos del autor"><?php the_posts_pagination(array('prev_text'=>'← Anteriores','next_text'=>'Siguientes →')); ?></nav></main><?php get_footer(); ?>
