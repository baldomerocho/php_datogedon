<?php
/**
 * The template for displaying 404 pages (not found)
 */

get_header();
?>

<main id="primary" class="site-main content-container">
    <div class="single-layout text-center" style="padding: 5rem 0;">
        <section class="error-404 not-found">
            <header class="page-header mb-4">
                <h1 class="page-title" style="font-size: clamp(4rem, 10vw, 7rem); line-height: 1; font-weight: 800; color: var(--accent); margin-bottom: 1.5rem;">404</h1>
                <h2 style="font-size: 1.75rem; font-weight: 700; margin-bottom: 1rem;"><?php esc_html_e( 'Página no encontrada', 'datogedon-reader' ); ?></h2>
            </header>

            <div class="page-content">
                <p><?php esc_html_e( 'Lo sentimos, la página que buscas no existe o ha sido movida.', 'datogedon-reader' ); ?></p>
                <p class="mt-4">
                    <a href="<?php echo esc_url( home_url( '/' ) ); ?>" style="display: inline-block; background-color: var(--accent); color: #ffffff; padding: 0.75rem 1.5rem; border-radius: 6px; font-weight: 600; text-decoration: none; transition: background-color 0.2s;">
                        <?php esc_html_e( 'Volver al Inicio', 'datogedon-reader' ); ?>
                    </a>
                </p>
            </div>
        </section>
    </div>
</main>

<?php
get_footer();
