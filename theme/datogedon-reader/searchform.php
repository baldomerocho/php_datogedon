<?php
/**
 * The template for displaying search forms
 */
?>
<form role="search" method="get" class="search-form" action="<?php echo esc_url( home_url( '/' ) ); ?>">
    <label style="width: 100%;">
        <span class="screen-reader-text"><?php echo _x( 'Buscar:', 'label', 'datogedon-reader' ); ?></span>
        <input type="search" class="search-field" placeholder="<?php echo esc_attr_x( 'Buscar artículo...', 'placeholder', 'datogedon-reader' ); ?>" value="<?php echo get_search_query(); ?>" name="s" />
    </label>
    <button type="submit" class="search-submit" aria-label="<?php echo esc_attr__( 'Buscar', 'datogedon-reader' ); ?>">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
    </button>
</form>
