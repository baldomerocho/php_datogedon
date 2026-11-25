<?php
/** Native WordPress discussion, rendered as readable threads. */
if (post_password_required()) return;
$count=(int)get_comments_number();
$commenter=wp_get_current_commenter();
$required=(bool)get_option('require_name_email');
$attributes=$required?' required aria-required="true"':'';
$asterisk=$required?' <span aria-hidden="true">*</span>':'';
?>
<section id="comments" class="comments-area" aria-labelledby="comments-heading">
    <header class="comments-heading">
        <div>
            <h2 id="comments-heading">Comentarios <span class="comments-count"><?php echo esc_html(number_format_i18n($count)); ?></span></h2>
        </div>
        <?php if(comments_open()): ?><a class="comment-jump" href="#respond">Comentar <span aria-hidden="true">↗</span></a><?php endif; ?>
    </header>
    <?php if(comments_open()): ?>
    <div class="discussion-invitation"><span class="discussion-eyebrow">Tu experiencia también cuenta</span><p><?php echo esc_html(datogedon_discussion_question(get_the_ID())); ?></p></div>
    <?php endif; ?>
    <?php $featured=datogedon_featured_comment(get_the_ID()); if($featured): ?>
    <aside class="discussion-featured" aria-labelledby="featured-comment-heading">
        <h3 id="featured-comment-heading">Una aportación para la conversación</h3>
        <blockquote><?php echo esc_html(wp_trim_words(wp_strip_all_tags($featured->comment_content),55,'…')); ?></blockquote>
        <p><?php echo esc_html(get_comment_author($featured)); ?> <span aria-hidden="true">·</span> <a href="<?php echo esc_url(get_comment_link($featured)); ?>">Leer y responder <span aria-hidden="true">→</span></a></p>
    </aside>
    <?php endif; ?>
    <?php
    $fields=array(
        'author'=>'<p class="comment-form-author"><label for="author">Nombre'.$asterisk.'</label><input id="author" name="author" type="text" autocomplete="name" value="'.esc_attr($commenter['comment_author']).'" maxlength="245"'.$attributes.' /></p>',
        'email'=>'<p class="comment-form-email"><label for="email">Correo electrónico'.$asterisk.'</label><input id="email" name="email" type="email" autocomplete="email" value="'.esc_attr($commenter['comment_author_email']).'" maxlength="100"'.$attributes.' /></p>',
    );
    if(get_option('show_comments_cookies_opt_in')) $fields['cookies']='<p class="comment-form-cookies-consent"><input id="wp-comment-cookies-consent" name="wp-comment-cookies-consent" type="checkbox" value="yes"'.checked(!empty($commenter['comment_author_email']),true,false).' /><label for="wp-comment-cookies-consent">Guardar mi nombre y correo en este navegador para la próxima vez.</label></p>';
    comment_form(array(
        'fields'=>$fields,
        'comment_field'=>'<p class="comment-form-comment"><label for="comment">Comentario <span aria-hidden="true">*</span></label><textarea id="comment" name="comment" rows="5" required aria-required="true" placeholder="Escribe tu comentario…"></textarea></p>',
        'comment_notes_before'=>'<p class="comment-welcome">Puedes discrepar, preguntar o compartir tu experiencia. Cuidemos el trato entre personas.</p><p class="comment-notes">Tu correo no se publica.'.($required?' Los campos con * son obligatorios.':'').'</p>',
        'class_submit'=>'submit comment-submit',
        'title_reply'=>'Comparte tu experiencia',
        'title_reply_to'=>'Responder a %s',
        'cancel_reply_link'=>'Cancelar respuesta',
        'label_submit'=>'Enviar comentario',
    ));
    ?>
    <?php if(have_comments()): ?>
        <ul class="comment-list" role="list">
            <?php wp_list_comments(array('style'=>'ul','format'=>'html5','short_ping'=>true,'avatar_size'=>40,'callback'=>'datogedon_reader_comment')); ?>
        </ul>
        <?php the_comments_navigation(array('prev_text'=>'← Comentarios anteriores','next_text'=>'Comentarios siguientes →')); ?>
        <?php if(!comments_open()): ?><p class="no-comments">Los comentarios están cerrados.</p><?php endif; ?>
    <?php endif; ?>
</section>
