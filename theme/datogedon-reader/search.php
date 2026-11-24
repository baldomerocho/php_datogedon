<?php
/**
 * The template for displaying search results pages
 */

get_header();
?>

<main id="primary" class="site-main container">
    <header class="page-header search-header" style="margin-bottom: 2.5rem; padding-bottom: 2rem; border-bottom: 1px solid var(--border);">
        <?php datogedon_reader_breadcrumbs(); ?>
        
        <h1 class="page-title search-title" style="font-size: 2rem; font-weight: 700; margin-top: 1rem; margin-bottom: 1.5rem; color: var(--text-headings);">
            <?php
            printf(
                /* translators: %s: search query. */
                esc_html__( 'Resultados de búsqueda para: %s', 'datogedon-reader' ),
                '<span style="font-style: italic;">&ldquo;' . get_search_query() . '&rdquo;</span>'
            );
            ?>
        </h1>
        
        <div class="search-page-form" style="max-width: 500px;">
            <?php get_search_form(); ?>
        </div>
    </header>

    <div class="feed-layout">
        <?php if ( have_posts() ) : ?>

            <?php
            while ( have_posts() ) :
                the_post();
                ?>
                <!-- Standard Post Cards -->
                <article id="post-<?php the_ID(); ?>" <?php post_class( 'post-card' ); ?>>
                    <div class="post-meta">
                        <span class="post-date"><?php echo get_the_date(); ?></span>
                        <span class="meta-separator">&bull;</span>
                        <span class="post-category"><?php the_category( ', ' ); ?></span>
                        <span class="meta-separator">&bull;</span>
                        <span class="post-read-time">
                            <?php 
                            $reading_time = datogedon_reader_reading_time( get_the_content() );
                            printf( __( '%d min de lectura', 'datogedon-reader' ), $reading_time );
                            ?>
                        </span>
                    </div>

                    <h2 class="post-card-title">
                        <a href="<?php the_permalink(); ?>" rel="bookmark"><?php the_title(); ?></a>
                    </h2>

                    <div class="post-excerpt">
                        <?php the_excerpt(); ?>
                    </div>

                    <a href="<?php the_permalink(); ?>" class="read-more-link"><?php _e( 'Leer artículo completo &rarr;', 'datogedon-reader' ); ?></a>
                </article>
            <?php
            endwhile;
            ?>

            <nav class="pagination" aria-label="<?php esc_attr_e( 'Paginación de resultados', 'datogedon-reader' ); ?>">
                <div class="nav-previous"><?php next_posts_link( __( '&larr; Resultados anteriores', 'datogedon-reader' ) ); ?></div>
                <div class="nav-next"><?php previous_posts_link( __( 'Resultados siguientes &rarr;', 'datogedon-reader' ) ); ?></div>
            </nav>

        <?php else : ?>
            <div class="no-results-content" style="padding: 3rem 0; text-align: center;">
                <p style="font-size: 1.125rem; color: var(--text-muted); margin-bottom: 2rem;">
                    <?php _e( 'Lo sentimos, no encontramos resultados que coincidan con tu búsqueda. Intenta con otras palabras clave.', 'datogedon-reader' ); ?>
                </p>
            </div>
        <?php endif; ?>
    </div>
</main>

<?php
get_footer();
