<?php
/** Private journal; execute through WP-CLI, never serve over HTTP. */
$mode=$args[0];$file=$args[1];$owner=(int)$args[2];
$keys=array('rank_math_registration_skip','rank-math-options-titles','rank-math-options-general','datogedon_owner_user_id','datogedon_category_redirects','blogdescription');
$slugs=array('acerca-de','experiencias-con-ia','temas','politica-editorial','colabora');
if($mode==='save') {
    $data=array('options'=>array(),'pages'=>array(),'owner'=>array(),'stylesheet'=>get_option('stylesheet'),'toc_plugin_position'=>array_search('table-of-contents-plus/toc.php',(array)get_option('active_plugins',array()),true),'toc_plugin_active'=>in_array('table-of-contents-plus/toc.php',(array)get_option('active_plugins',array()),true));
    foreach($keys as $key)$data['options'][$key]=array('exists'=>get_option($key,null)!==null,'value'=>get_option($key));
    foreach($slugs as $slug){$post=get_page_by_path($slug);$data['pages'][$slug]=$post?array('ID'=>$post->ID,'post_title'=>$post->post_title,'post_content'=>$post->post_content,'post_status'=>$post->post_status):null;}
    $user=get_user_by('id',$owner);if($user)$data['owner']=array('ID'=>$owner,'display_name'=>$user->display_name,'description'=>get_user_meta($owner,'description',true));
    file_put_contents($file,wp_json_encode($data));chmod($file,0600);WP_CLI::success('Private configuration journal saved.');
} elseif($mode==='restore') {
    $data=json_decode(file_get_contents($file),true);
    if(array_key_exists('toc_plugin_active',$data)) {
        // Restore only this plugin's membership; preserve unrelated plugin changes.
        $plugins=(array)get_option('active_plugins',array());$toc='table-of-contents-plus/toc.php';
        $plugins=array_values(array_diff($plugins,array($toc)));
        if($data['toc_plugin_active'])array_splice($plugins,(int)($data['toc_plugin_position']??count($plugins)),0,array($toc));
        update_option('active_plugins',$plugins);
    }
    foreach($data['options'] as $key=>$entry){if($entry['exists'])update_option($key,$entry['value']);else delete_option($key);}
    foreach($data['pages'] as $slug=>$post){if($post)wp_update_post($post);else{$new=get_page_by_path($slug);if($new)wp_delete_post($new->ID,true);}}
    if($data['owner'])wp_update_user($data['owner']);
    flush_rewrite_rules(false);WP_CLI::success('Configuration restored; unrelated posts preserved.');
} else WP_CLI::error('Unknown journal mode.');
