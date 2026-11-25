<?php
$story=$args['post'];$id=(int)$story->ID;$variant=$args['variant']??'grid';$kind=datogedon_reader_home_kind($story);
$category=function_exists('datogedon_primary_category')?datogedon_primary_category($id):null;
$labels=array('news'=>'Noticia','experience'=>'Experiencia con IA','article'=>'Artículo');
?>
<article class="home-story home-story--<?php echo esc_attr($variant); ?>" data-post-id="<?php echo $id; ?>" id="post-<?php echo $id; ?>">
<?php if(in_array($variant,array('lead','grid'),true)): ?>
<a class="home-story-image<?php echo has_post_thumbnail($id)?'':' home-story-image--empty'; ?>" href="<?php echo esc_url(get_permalink($id)); ?>" tabindex="-1" aria-hidden="true">
<?php if(has_post_thumbnail($id)): echo get_the_post_thumbnail($id,$variant==='lead'?'large':'medium_large',array('alt'=>'','loading'=>$variant==='lead'?'eager':'lazy','fetchpriority'=>$variant==='lead'?'high':'auto','sizes'=>$variant==='lead'?'(max-width: 700px) 100vw, (max-width: 1100px) 60vw, 650px':'(max-width: 700px) 100vw, (max-width: 960px) 50vw, 350px')); ?>
<?php else: ?><span aria-hidden="true" class="home-image-mark">{ / }</span><span><?php echo esc_html($category?$category->name:'Desarrollo'); ?></span><?php endif; ?>
</a>
<?php endif; ?>
<div class="home-story-body">
<div class="home-story-meta"><span class="home-kind"><?php echo esc_html($labels[$kind]); ?></span><?php if($category): ?><span><?php echo esc_html($category->name); ?></span><?php endif; ?></div>
<h3 class="home-story-title"><a href="<?php echo esc_url(get_permalink($id)); ?>"><?php echo esc_html(get_the_title($id)); ?></a></h3>
<?php if($variant!=='rail'): ?><p class="home-story-excerpt"><?php echo esc_html(wp_trim_words(get_the_excerpt($story),$variant==='lead'?30:23)); ?></p><?php endif; ?>
<div class="home-story-foot"><time datetime="<?php echo esc_attr(get_the_date('c',$id)); ?>"><?php echo esc_html(get_the_date('j M Y',$id)); ?></time><span aria-hidden="true">·</span><span><?php echo max(1,(int)datogedon_reader_reading_time($story->post_content)); ?> min</span><?php if(get_comments_number($id)): ?><a class="home-story-comments" href="<?php echo esc_url(get_comments_link($id)); ?>"><?php echo esc_html(number_format_i18n(get_comments_number($id))); ?> <span class="screen-reader-text">comentarios en <?php echo esc_html(get_the_title($id)); ?></span><svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2V11.5a8.5 8.5 0 1 1 19 0Z"/></svg></a><?php endif; ?></div>
</div>
</article>
