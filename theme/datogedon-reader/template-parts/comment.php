<?php
/** Called by the native walker; WordPress closes the list item after its replies. */
$parent=$comment->comment_parent ? get_comment($comment->comment_parent) : null;
$is_author=$comment->user_id && (int)$comment->user_id===(int)get_post_field('post_author',$comment->comment_post_ID);
$is_owner=$comment->user_id && (int)$comment->user_id===(int)get_option('datogedon_owner_user_id');
?>
<li <?php comment_class('', $comment); ?> id="comment-<?php echo (int)$comment->comment_ID; ?>">
    <article id="div-comment-<?php echo (int)$comment->comment_ID; ?>" class="comment-body">
        <header class="comment-meta">
            <div class="comment-person">
                <?php echo get_avatar($comment,40,'','',array('loading'=>'lazy','extra_attr'=>'aria-hidden="true"')); ?>
                <div class="comment-person-details">
                    <div class="comment-author"><span class="fn"><?php echo get_comment_author_link($comment); ?></span><?php if($is_author || $is_owner): ?><span class="comment-author-badge"><?php echo $is_author?'Autor':'Equipo'; ?></span><?php endif; ?></div>
                    <a class="comment-permalink" href="<?php echo esc_url(get_comment_link($comment,$args)); ?>"><time datetime="<?php echo esc_attr(get_comment_date('c',$comment)); ?>"><?php echo esc_html(get_comment_date('j M Y',$comment)); ?> · <?php echo esc_html(get_comment_time('H:i',false,true,$comment)); ?></time></a>
                </div>
            </div>
        </header>
        <?php if($parent): ?><p class="comment-parent-reference">En respuesta a <?php if((string)$parent->comment_approved==='1'): ?><a href="#comment-<?php echo (int)$parent->comment_ID; ?>"><?php echo esc_html(get_comment_author($parent)); ?></a><?php else: ?>otro comentario<?php endif; ?></p><?php endif; ?>
        <?php if((string)$comment->comment_approved==='0'): ?><p class="comment-awaiting-moderation" role="status">Tu comentario está pendiente de moderación.</p><?php endif; ?>
        <div class="comment-content"><?php comment_text($comment,array_merge($args,array('add_below'=>'div-comment'))); ?></div>
        <footer class="comment-actions">
            <?php
            if(in_array(get_comment_type($comment),array('','comment'),true)) comment_reply_link(array_merge($args,array('add_below'=>'div-comment','depth'=>$depth,'max_depth'=>$args['max_depth'],'reply_text'=>'Responder','reply_to_text'=>'Responder a %s')),$comment);
            edit_comment_link('Editar comentario');
            ?>
        </footer>
    </article>
