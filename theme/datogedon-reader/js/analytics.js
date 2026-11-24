/* Extends the existing Matomo tracker; never initializes a second tracker. */
(function () {
    'use strict';
    function ready() {
        if (window.datogedonAnalyticsReady) return;
        window.datogedonAnalyticsReady = true;
        function event(category, action, name, value) {
            if (!window._paq || typeof window._paq.push !== 'function') return;
            const command = ['trackEvent', category, action, name];
            if (Number.isFinite(value)) command.push(value);
            try { window._paq.push(command); } catch (_) { /* Analytics must not interrupt navigation. */ }
        }
        function searchLocation(form) {
            return form.closest('#masthead') ? 'header' : form.closest('.home-hero') ? 'hero' : 'results';
        }
        // Labels are fixed enums or numeric post IDs, never input values or URLs.
        document.addEventListener('click', function (e) {
            if (!(e.target instanceof Element)) return;
            const control = e.target.closest('#theme-toggle, #menu-toggle, #search-toggle');
            if (control) {
                if (control.id === 'theme-toggle') event('Interface', 'theme_change', document.documentElement.getAttribute('data-theme'));
                else if (control.getAttribute('aria-expanded') === 'true') event(control.id === 'menu-toggle' ? 'Navigation' : 'Search', 'open', control.id === 'menu-toggle' ? 'mobile_menu' : 'header');
                return;
            }
            const link = e.target.closest('a[href]');
            if (!link) return;
            const target = new URL(link.href, location.href);
            if (target.origin !== location.origin) return; // Native Matomo tracks outlinks/downloads.
            const path = target.pathname.replace(/\/+$/, '') || '/';
            if (path === '/colabora' || path === '/contacto') {
                event('Collaboration', path === '/colabora' ? 'open' : 'contact_open', link.closest('#masthead') ? 'header' : link.closest('#colophon') ? 'footer' : 'content');
                return;
            }
            const item = link.closest('[data-post-id]');
            const id = item && item.getAttribute('data-post-id');
            if (id && /^\d+$/.test(id) && !target.hash) {
                if (link.closest('.related-posts')) event('Navigation', 'related_open', 'post:' + id);
                else if (link.classList.contains('autocomplete-item')) event('Search', 'autocomplete_select', 'post:' + id);
                else if (link.closest('.post-card, .featured-post-card') && (link.matches('.read-more-link, .card-thumbnail, .featured-post-image') || link.closest('h2'))) event('Navigation', 'article_open', 'post:' + id);
                return;
            }
            if (link.closest('#main-nav, .hero-links')) {
                const sections = {'/': 'home', '/temas': 'topics', '/experiencias-con-ia': 'experiences', '/acerca-de': 'about'};
                if (sections[path]) event('Navigation', 'section_open', sections[path]);
            }
        });
        document.addEventListener('submit', function (e) {
            if (e.target.matches('.search-form') && e.target.querySelector('.search-field').value.trim()) event('Search', 'submit', searchLocation(e.target));
        });
        const results = document.querySelector('[data-search-results]');
        if (results) {
            const count = Number(results.getAttribute('data-search-results'));
            if (Number.isFinite(count)) event('Search', 'results', count > 0 ? 'found' : 'empty', count);
        }

        const article = document.querySelector('body.single-post article[data-post-id] .post-content');
        if (!article) return;
        const id = article.closest('[data-post-id]').getAttribute('data-post-id');
        if (!/^\d+$/.test(id)) return;
        const sent = new Set();
        const milestones = [{percent: 50, seconds: 10}, {percent: 90, seconds: 30}];
        let active = !document.hidden && document.hasFocus();
        let since = performance.now(), elapsed = 0, timer = null, frame = null;
        function activeSeconds() { return (elapsed + (active ? performance.now() - since : 0)) / 1000; }
        function check() {
            frame = null;
            clearTimeout(timer);
            if (!active || sent.size === milestones.length) return;
            const rect = article.getBoundingClientRect();
            // Measure the article body, excluding header, comments, related posts and footer.
            if (rect.top >= innerHeight || rect.height <= 0 || rect.bottom <= 0) return;
            const progress = Math.max(0, Math.min(100, (innerHeight - rect.top) / rect.height * 100));
            let next = Infinity;
            for (const mark of milestones) {
                if (sent.has(mark.percent) || progress < mark.percent) continue;
                const remaining = mark.seconds - activeSeconds();
                if (remaining <= 0) {
                    event('Reading', 'progress_' + mark.percent, 'post:' + id, mark.percent);
                    sent.add(mark.percent);
                } else next = Math.min(next, remaining);
            }
            // One deadline when a milestone is visible; no polling or background timer.
            if (Number.isFinite(next)) timer = setTimeout(check, Math.ceil(next * 1000) + 20);
        }
        function schedule() { if (frame === null) frame = requestAnimationFrame(check); }
        function visibility() {
            if (active) elapsed += performance.now() - since;
            active = !document.hidden && document.hasFocus(); since = performance.now();
            check();
        }
        addEventListener('scroll', schedule, {passive: true});
        addEventListener('resize', schedule);
        addEventListener('focus', visibility);
        addEventListener('blur', visibility);
        document.addEventListener('visibilitychange', visibility);
        check();
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
    else ready();
})();
