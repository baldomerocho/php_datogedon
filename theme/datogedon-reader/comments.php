<?php
/**
 * The template for displaying comments
 */

if ( post_password_required() ) {
    return;
}
?>

<div id="comments" class="comments-area">

    <?php if ( have_comments() ) : ?>
        <h2 class="comments-title">
            <?php
            $comment_count = get_comments_number();
            if ( 1 === $comment_count ) {
                printf(
                    esc_html__( 'Un comentario en &ldquo;%1$s&rdquo;', 'datogedon-reader' ),
                    '<span>' . wp_kses_post( get_the_title() ) . '</span>'
                );
            } else {
                printf(
                    esc_html( _n( '%1$s comentario en &ldquo;%2$s&rdquo;', '%1$s comentarios en &ldquo;%2$s&rdquo;', $comment_count, 'datogedon-reader' ) ),
                    number_format_i18n( $comment_count ),
                    '<span>' . wp_kses_post( get_the_title() ) . '</span>'
                );
            }
            ?>
        </h2>

        <ol class="comment-list">
            <?php
            wp_list_comments( array(
                'style'      => 'ol',
                'short_ping' => true,
                'avatar_size'=> 48,
            ) );
            ?>
        </ol>

        <?php
        the_comments_navigation( array(
            'prev_text' => __( '&larr; Comentarios anteriores', 'datogedon-reader' ),
            'next_text' => __( 'Comentarios siguientes &rarr;', 'datogedon-reader' ),
        ) );
        ?>

        <?php if ( ! comments_open() ) : ?>
            <p class="no-comments"><?php esc_html_e( 'Los comentarios están cerrados.', 'datogedon-reader' ); ?></p>
        <?php endif; ?>

    <?php endif; ?>

    <?php
    $commenter = wp_get_current_commenter();
    $req = get_option( 'require_name_email' );
    $aria_req = ( $req ? " aria-required='true'" : '' );

    $fields = array(
        'author' => '<div class="comment-form-author"><input id="author" name="author" type="text" placeholder="' . esc_attr__( 'Nombre *', 'datogedon-reader' ) . '" value="' . esc_attr( $commenter['comment_author'] ) . '" size="30"' . $aria_req . ' /></div>',
        'email'  => '<div class="comment-form-email"><input id="email" name="email" type="email" placeholder="' . esc_attr__( 'Correo electrónico *', 'datogedon-reader' ) . '" value="' . esc_attr( $commenter['comment_author_email'] ) . '" size="30"' . $aria_req . ' /></div>',
    );

    comment_form( array(
        'fields'        => $fields,
        'comment_field' => '<div class="comment-form-comment"><textarea id="comment" name="comment" cols="45" rows="5" placeholder="' . esc_attr__( 'Escribe tu comentario aquí...', 'datogedon-reader' ) . '" aria-required="true"></textarea></div>',
        'class_submit'  => 'submit',
        'title_reply'   => __( 'Deja una respuesta', 'datogedon-reader' ),
        'label_submit'  => __( 'Publicar comentario', 'datogedon-reader' ),
    ) );
    ?>

</div><!-- #comments -->
