<footer id="colophon" class="site-footer"><div class="container">
<nav aria-label="Información del sitio" class="footer-links">
<?php foreach(array('acerca-de'=>'Acerca de','temas'=>'Temas','politica-editorial'=>'Política editorial','colabora'=>'Colabora','contacto'=>'Contacto') as $slug=>$label): ?><a href="<?php echo esc_url(home_url('/'.$slug.'/')); ?>"><?php echo esc_html($label); ?></a><?php endforeach; ?>
</nav><p>© <?php echo esc_html(wp_date('Y')); ?> DATOGEDON · Desarrollo de software con IA</p>
</div></footer></div><?php wp_footer(); ?></body></html>
