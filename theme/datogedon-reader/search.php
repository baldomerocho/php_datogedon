<?php
/**
 * The template for displaying search results pages
 */

get_header();
?>

<main id="primary" class="site-main container">
    <header data-search-results="<?php global $wp_query; echo (int)$wp_query->found_posts; ?>" class="page-header search-header" style="margin-bottom: 2.5rem; padding-bottom: 2rem; border-bottom: 1px solid var(--border);">
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
                <?php set_query_var('datogedon_featured',false); get_template_part('template-parts/card'); ?>
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
