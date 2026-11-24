<?php $featured=(bool)get_query_var('datogedon_featured',false); $category=function_exists('datogedon_primary_category')?datogedon_primary_category(get_the_ID()):null; ?>
<article id="post-<?php the_ID(); ?>" <?php post_class($featured?'featured-post-card':'post-card compact-card'); ?>>
<?php if(has_post_thumbnail()): ?><a class="<?php echo $featured?'featured-post-image':'card-thumbnail'; ?>" href="<?php the_permalink(); ?>" tabindex="-1" aria-hidden="true"><?php the_post_thumbnail($featured?'large':'medium',array('alt'=>'','loading'=>$featured?'eager':'lazy')); ?></a><?php endif; ?>
<div class="card-details">
<div class="post-meta"><time datetime="<?php echo esc_attr(get_the_date('c')); ?>"><?php echo esc_html(get_the_date()); ?></time><?php if($category): ?><a href="<?php echo esc_url(get_category_link($category->term_id)); ?>"><?php echo esc_html($category->name); ?></a><?php endif; ?><span><?php echo (int)datogedon_reader_reading_time(get_the_content()); ?> min de lectura</span></div>
<?php if($featured): ?><span class="featured-badge">Más reciente</span><?php endif; ?>
<h2 class="<?php echo $featured?'featured-post-title':'post-card-title'; ?>"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
<p class="post-excerpt"><?php echo esc_html(wp_trim_words(get_the_excerpt(),32)); ?></p>
<a class="read-more-link" href="<?php the_permalink(); ?>">Leer artículo <span class="screen-reader-text"><?php the_title(); ?></span>→</a>
</div></article>
