<?php
/**
 * The template for displaying all single posts
 */

get_header();
?>

<main id="primary" class="site-main content-container">
    <div class="single-layout">
        <?php while ( have_posts() ) : the_post(); ?>
            <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                <header class="single-header">
                    <?php datogedon_reader_breadcrumbs(); ?>
                    <div class="post-meta">
                        <span class="post-date"><time datetime="<?php echo esc_attr(get_the_date('c')); ?>"><?php echo esc_html(get_the_date()); ?></time></span>
                        <span class="meta-separator">&bull;</span>
                        <span class="post-category"><?php $category=function_exists('datogedon_primary_category')?datogedon_primary_category(get_the_ID()):null;if($category)echo '<a href="'.esc_url(get_category_link($category->term_id)).'">'.esc_html($category->name).'</a>'; ?></span>
                        <span class="meta-separator">&bull;</span>
                        <span class="post-read-time">
                            <?php 
                            $reading_time = datogedon_reader_reading_time( get_the_content() );
                            printf( __( '%d min de lectura', 'datogedon-reader' ), $reading_time );
                            ?>
                        </span>
                    </div>

                    <h1 class="entry-title"><?php the_title(); ?></h1>
                    
                    <div class="post-author-meta">
                        <span class="author-name"><?php _e( 'Por', 'datogedon-reader' ); ?> <?php the_author_posts_link(); ?></span>
                    </div>
                </header>

                <?php if ( has_post_thumbnail() ) : ?>
                    <div class="post-thumbnail mb-4">
                        <?php the_post_thumbnail( 'large', array( 'alt' => datogedon_reader_get_post_thumbnail_alt() ) ); ?>
                    </div>
                <?php endif; ?>

                <div class="post-content">
                    <?php
                    the_content();

                    wp_link_pages( array(
                        'before' => '<div class="page-links">' . esc_html__( 'Páginas:', 'datogedon-reader' ),
                        'after'  => '</div>',
                    ) );
                    ?>
                </div>

                <footer class="entry-footer">
                    <?php
                    $tags_list = get_the_tag_list( '', esc_html_x( ', ', 'list item separator', 'datogedon-reader' ) );
                    if ( $tags_list ) {
                        printf( '<span class="tags-links">' . esc_html__( 'Etiquetas: %1$s', 'datogedon-reader' ) . '</span>', $tags_list );
                    }
                    ?>
                </footer>
            </article>

            <?php datogedon_reader_related_posts(); ?>
            <?php
            if ( comments_open() || get_comments_number() ) :
                comments_template();
            endif;
            ?>

        <?php endwhile; ?>
    </div>
</main>

<?php
get_footer();
