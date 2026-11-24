<?php
/**
 * The template for displaying all pages
 */

get_header();
?>

<main id="primary" class="site-main content-container">
    <div class="single-layout">
        <?php while ( have_posts() ) : the_post(); ?>
            <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                <header class="single-header">
                    <?php datogedon_reader_breadcrumbs(); ?>
                    <h1 class="entry-title"><?php the_title(); ?></h1>
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
            </article>

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
