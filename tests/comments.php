<?php
/** Exercise the real editorial ability through draft/update/schedule, with synthetic data. */
wp_set_current_user(1);
$ability=wp_get_ability('datogedon/save-post');
if(!$ability)throw new RuntimeException('Editorial ability was not registered.');
$original=get_option('default_comment_status');$ids=array();$media=0;
function verify_comments($result,$expected) {
    if(is_wp_error($result))throw new RuntimeException($result->get_error_message());
    if(get_post_field('comment_status',$result['id'])!==$expected)throw new RuntimeException('Editorial save changed the comment policy.');
    return $result['id'];
}
try {
    update_option('default_comment_status','open');
    $payload=array('editorial_id'=>'ci-comment-policy','title'=>'Synthetic discussion test','content'=>'<p>Synthetic content.</p>','status'=>'draft');
    $first=$ability->execute($payload);$id=verify_comments($first,'open');$ids[]=$id;
    verify_comments($ability->execute($payload),'open');
    $upload=wp_upload_bits('editorial-comment-fixture.png',null,base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='));
    if($upload['error'])throw new RuntimeException('Cannot create test image.');
    $media=wp_insert_attachment(array('post_title'=>'Synthetic fixture','post_mime_type'=>'image/png','post_status'=>'inherit'),$upload['file']);
    require_once ABSPATH.'wp-admin/includes/image.php';
    wp_update_attachment_metadata($media,wp_generate_attachment_metadata($media,$upload['file']));
    $payload['status']='future';$payload['date']=wp_date('Y-m-d H:i:s',time()+86400);$payload['featured_media']=$media;
    verify_comments($ability->execute($payload),'open');
    // A deliberate per-post closure must survive later editorial updates.
    wp_update_post(array('ID'=>$id,'comment_status'=>'closed'));
    verify_comments($ability->execute($payload),'closed');
    // Changing the site default must not override an existing post's choice.
    wp_update_post(array('ID'=>$id,'comment_status'=>'open'));update_option('default_comment_status','closed');
    verify_comments($ability->execute($payload),'open');
    $second=$ability->execute(array('editorial_id'=>'ci-comments-default-closed','title'=>'Synthetic closed default','content'=>'<p>Fixture.</p>','status'=>'draft'));
    $ids[]=verify_comments($second,'closed');
    WP_CLI::success('Comment policy preserved across draft retries, scheduling and manual/site choices.');
} finally {
    update_option('default_comment_status',$original);
    foreach($ids as $id)wp_delete_post($id,true);
    if($media)wp_delete_attachment($media,true);
}
