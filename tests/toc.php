<?php
/** Real WordPress/TOC+ compatibility, render isolation and deployment recovery. */
function toc_assert($condition,$message){if(!$condition)throw new RuntimeException($message);}
function toc_ids($html){$ids=array();$p=new WP_HTML_Tag_Processor($html);while($p->next_tag())if(is_string($id=$p->get_attribute('id')))$ids[]=$id;return $ids;}
$original=get_option('toc-options',null);
try {
    $settings=array('lowercase'=>false,'hyphenate'=>false,'fragment_prefix'=>'i','heading_levels'=>array(1,2,3,4,5,6),'start'=>1,'exclude'=>'');
    update_option('toc-options',$settings);
    $legacy=null;
    foreach($GLOBALS['wp_filter']['the_content']->callbacks as $callbacks)foreach($callbacks as $filter){$fn=$filter['function'];if(is_array($fn)&&is_object($fn[0])&&method_exists($fn[0],'extract_headings'))$legacy=$fn[0];}
    toc_assert($legacy!==null,'The actual previous plugin must be available for compatibility testing.');
    $legacy->set_option($settings);
    $html='<h2>Cómo usar <code>cargo check</code></h2><h3>A &amp; B</h3><h2>Repetido</h2><h2>Repetido</h2><h4>Notas</h4><h2>你好</h2>';
    $find=array();$replace=array();$legacy->extract_headings($find,$replace,$html);
    $expected=toc_ids(implode('',$replace));$output=datogedon_reader_toc_build($html);
    foreach($expected as $id)toc_assert(in_array($id,toc_ids($output),true),'Lost legacy fragment: '.$id);
    // Respect manually authored IDs, including anchors nested in headings.
    $content='<h2 id="custom">Cómo probar</h2><h3><span id="nested">Datos</span></h3><h2>Datos</h2><h3>Datos-2</h3><h2>Datos</h2>';
    $output=datogedon_reader_toc_build($content);$ids=toc_ids($output);
    toc_assert(in_array('custom',$ids,true)&&in_array('Como_probar',$ids,true)&&in_array('nested',$ids,true),'Custom IDs or aliases changed.');
    toc_assert(count($ids)===count(array_unique($ids)),'Duplicate generated IDs.');
    $literal='<pre><h2>Example heading</h2></pre><script>const x="<h2>Script example</h2>";</script><!-- <h2>Comment</h2> -->';
    $output=datogedon_reader_toc_build($literal.$html);
    toc_assert(strpos($output,$literal)!==false,'Literal examples or scripts were rewritten.');
    toc_assert(strpos(datogedon_reader_toc_build($html),'data-datogedon-toc')===false,'Short article should not have an automatic index.');
    $structured='<h2>Paso 1</h2><h2>Paso 2</h2><h3>Detalle</h3><h2>Paso 3</h2><h2>Paso 4</h2><h2>Paso 5</h2>';
    toc_assert(strpos(datogedon_reader_toc_build($structured),'data-datogedon-toc')!==false,'Structured tutorials need an index even when code outweighs prose.');
    $long='<p>'.str_repeat('Un ejemplo legible para verificar el índice. ',85).'</p>'.$html;
    $output=datogedon_reader_toc_build($long);
    toc_assert(substr_count($output,'data-datogedon-toc')===1,'Long article must have exactly one index.');
    toc_assert(datogedon_reader_toc_build($output)===$output,'Rendering must be idempotent.');
    $disabled=datogedon_reader_toc_build('<!--datogedon-no-toc-->'.$long);
    toc_assert(strpos($disabled,'data-datogedon-toc')===false,'Explicit opt-out ignored.');
    toc_assert(in_array('Repetido-2',toc_ids($disabled),true),'Opt-out must preserve anchor navigation.');
    $marker='<!--datogedon-toc:'.base64_encode(wp_json_encode(array('label'=>'Índice <script>bad</script>','start'=>2))).'-->';
    $output=datogedon_reader_toc_build('<p>Inicio</p>'.$marker.'<p>Antes</p>'.$html);
    toc_assert(substr_count($output,'data-datogedon-toc')===1&&strpos($output,'<details')<strpos($output,'<p>Antes</p>'),'Explicit index placement not respected.');
    toc_assert(strpos($output,'<summary><span>Índice</span>' )!==false&&strpos($output,'<script>bad')===false,'Shortcode label must be text only.');
    $money=datogedon_reader_toc_build($marker.'<h2>$1 y $2</h2><h2>Otro dato</h2>');
    toc_assert(strpos($money,'$1 y $2</a>')!==false,'Dollar signs in headings must not be replacement backreferences.');
    $reserved=toc_ids(datogedon_reader_toc_build('<h2>comments</h2><h2>respond</h2>'));
    toc_assert(in_array('comments-2',$reserved,true)&&in_array('respond-2',$reserved,true),'Generated headings must not shadow theme navigation IDs.');
    $list=datogedon_reader_toc_list(array(array('id'=>'one','text'=>'Uno','level'=>3),array('id'=>'two','text'=>'Dos','level'=>3),array('id'=>'three','text'=>'Tres','level'=>2),array('id'=>'four','text'=>'Cuatro','level'=>3)));
    toc_assert(substr_count($list,'<ol>')===2,'Orphan H3s must be siblings, not artificial nested sections.');
    // Migration refuses live widget dependencies instead of silently removing them.
    $sidebars=get_option('sidebars_widgets');update_option('sidebars_widgets',array('sidebar-1'=>array('toc-widget-2')));
    toc_assert(is_wp_error(datogedon_reader_toc_migrate()),'Active legacy widget should block migration.');
    update_option('sidebars_widgets',$sidebars);
    // Journal a real active plugin, deactivate it, then exercise rollback in this DB.
    $journal=tempnam(sys_get_temp_dir(),'toc-journal-');$args=array('save',$journal,1);include dirname(__DIR__).'/scripts/config-journal.php';
    toc_assert(datogedon_reader_toc_migrate()===true,'Migration failed without legacy dependencies.');
    toc_assert(!in_array('table-of-contents-plus/toc.php',(array)get_option('active_plugins'),true),'Previous plugin remains active.');
    $args=array('restore',$journal,1);include dirname(__DIR__).'/scripts/config-journal.php';unlink($journal);
    toc_assert(in_array('table-of-contents-plus/toc.php',(array)get_option('active_plugins'),true),'Rollback lost the previous plugin state.');
    WP_CLI::success('TOC+: fragments, custom anchors, collisions, code examples, opt-outs, hierarchy and migration rollback passed.');
} finally {
    if($original===null)delete_option('toc-options');else update_option('toc-options',$original);
}
