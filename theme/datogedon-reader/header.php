<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    
    <!-- Inline script to prevent FOUC (Flash of Unstyled Content) in Dark Mode -->
    <script>
        (function() {
            var savedTheme = localStorage.getItem('theme');
            var systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
                document.documentElement.setAttribute('data-theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
            }
        })();
    </script>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div id="page" class="site">
    <a class="skip-link screen-reader-text" href="#primary"><?php esc_html_e( 'Saltar al contenido', 'datogedon-reader' ); ?></a>
    <header id="masthead" class="site-header">
        <div class="container">
            <div class="site-branding">
                <?php
                if ( has_custom_logo() ) {
                    the_custom_logo();
                } else {
                    echo datogedon_reader_get_site_title_html();
                }
                ?>
            </div>

            <nav id="site-navigation" class="main-navigation nav-container">
                <div id="main-nav" class="main-nav">
                    <?php
                    wp_nav_menu( array(
                        'theme_location' => 'primary',
                        'menu_id'        => 'primary-menu',
                        'container'      => false,
                        'fallback_cb'    => 'datogedon_reader_menu_fallback',
                    ) );
                    ?>
                </div>

                <div class="header-controls">
                    <!-- Search Toggle Button -->
                    <button id="search-toggle" class="search-toggle control-btn" aria-expanded="false" aria-controls="header-search-container" aria-label="Abrir búsqueda">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    </button>

                    <!-- Dark Mode Toggle Button -->
                    <button id="theme-toggle" class="theme-toggle control-btn" aria-label="Cambiar tema claro u oscuro">
                        <!-- Sun Icon for Dark Mode -->
                        <svg class="sun-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                        <!-- Moon Icon for Light Mode -->
                        <svg class="moon-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
                    </button>
                    
                    <!-- Mobile Hamburger Menu Button -->
                    <button id="menu-toggle" class="menu-toggle control-btn" aria-expanded="false" aria-controls="main-nav" aria-label="Abrir menú">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
                    </button>
                </div>
            </nav>
        </div>

        <!-- Search Overlay Container -->
        <div id="header-search-container" class="header-search-container">
            <?php get_search_form(); ?>
        </div>
    </header>

    <!-- Reading Progress Bar (Only visible on single posts/pages) -->
    <?php if ( is_single() || is_page() ) : ?>
        <div class="progress-container">
            <div id="reading-progress" class="progress-bar"></div>
        </div>
    <?php endif; ?>
