<?php
/** Isolated WordPress integration: publication, attribution, citations, internal candidates. */
if(wp_parse_url(home_url(),PHP_URL_HOST)!=='127.0.0.1')WP_CLI::error('Isolated CI only.');
wp_set_current_user(1);$save=wp_get_ability('datogedon/save-post');$find=wp_get_ability('datogedon/find-related-posts');$ids=[];$image=0;$created_user=false;
function editorial_ok($result){if(is_wp_error($result))throw new RuntimeException($result->get_error_message());return $result;}
function editorial_error($result,$code){if(!is_wp_error($result)||$result->get_error_code()!==$code)throw new RuntimeException('Expected '.$code);}
try{
    if(!get_user_by('id',135)){
        global $wpdb;
        $wpdb->insert($wpdb->users,['ID'=>135,'user_login'=>'ci-news-author','user_pass'=>wp_hash_password(wp_generate_password()),'user_nicename'=>'ci-news-author','user_email'=>'ci-news@example.invalid','display_name'=>'Synthetic editorial author','user_registered'=>current_time('mysql')]);
        (new WP_User(135))->set_role('editor');$created_user=true;
    }
    $gd=imagecreatetruecolor(1200,630);ob_start();imagewebp($gd,null,70);$bytes=ob_get_clean();imagedestroy($gd);
    $upload=wp_upload_bits('ci-editorial.webp',null,$bytes);if($upload['error'])throw new RuntimeException('Fixture upload failed');
    $image=wp_insert_attachment(['post_title'=>'CI editorial','post_mime_type'=>'image/webp','post_status'=>'inherit'],$upload['file']);
    require_once ABSPATH.'wp-admin/includes/image.php';wp_update_attachment_metadata($image,wp_generate_attachment_metadata($image,$upload['file']));update_post_meta($image,'_wp_attachment_image_alt','Synthetic editorial diagram');
    $category=(int)get_option('default_category');
    $payload=['editorial_id'=>'ci-news-cycle','kind'=>'news','author'=>135,'title'=>'Synthetic Quasar compiler release','content'=>'<p>Context for a compiler update. <a href="https://example.invalid/release">Release</a> and <a href="https://independent.invalid/analysis">Independent analysis</a>.</p>','status'=>'draft','excerpt'=>'Synthetic news','categories'=>[$category],'featured_media'=>$image,'source_urls'=>['https://example.invalid/release','https://independent.invalid/analysis']];
    $first=editorial_ok($save->execute($payload));$ids[]=$first['id'];
    if((int)get_post_field('post_author',$first['id'])!==135)throw new RuntimeException('News attribution missing');
    $bad=$payload;$bad['status']='publish';$bad['source_urls']=['https://example.invalid/one','https://example.invalid/two'];editorial_error($save->execute($bad),'missing_sources');
    $bad['source_urls']=['https://example.invalid/release','https://other.invalid/uncited'];editorial_error($save->execute($bad),'uncited_source');
    $payload['status']='publish';$published=editorial_ok($save->execute($payload));if($published['status']!=='publish')throw new RuntimeException('Immediate publication failed');
    $copy=$payload;$copy['content']='Must not overwrite published news';$retry=editorial_ok($save->execute($copy));
    if(empty($retry['immutable'])||get_post_field('post_content',$published['id'])===$copy['content'])throw new RuntimeException('Published content was overwritten');
    $candidates=editorial_ok($find->execute(['query'=>'Quasar compiler']));if(!in_array($first['id'],array_column($candidates['candidates'],'id'),true))throw new RuntimeException('Published candidate missing');
    update_post_meta($first['id'],'rank_math_robots',['noindex']);
    $candidates=editorial_ok($find->execute(['query'=>'Quasar compiler']));if(in_array($first['id'],array_column($candidates['candidates'],'id'),true))throw new RuntimeException('Noindex candidate leaked');
    $draft=['editorial_id'=>'ci-experience-cycle','title'=>'Synthetic experience','content'=>'<p>Experience.</p>','status'=>'draft'];
    $result=editorial_ok($save->execute($draft));$ids[]=$result['id'];
    $draft['status']='publish';$draft['excerpt']='Summary';$draft['categories']=[$category];$draft['featured_media']=$image;$draft['content']='<a href="'.get_permalink($first['id']).'">A noindex destination</a>';
    editorial_error($save->execute($draft),'invalid_internal_link');
    WP_CLI::success('Immediate publication, reserved news author, cited sources, immutable retries and indexable internal candidates verified.');
}finally{
    foreach($ids as $id)wp_delete_post($id,true);
    if($image)wp_delete_attachment($image,true);
    if($created_user){require_once ABSPATH.'wp-admin/includes/user.php';wp_delete_user(135);}
}
