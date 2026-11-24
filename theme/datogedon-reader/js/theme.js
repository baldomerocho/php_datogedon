document.addEventListener('DOMContentLoaded', function() {
    // === Dark Mode Toggle ===
    const themeToggleBtn = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;

    // Retrieve saved theme or check system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        htmlElement.setAttribute('data-theme', 'dark');
    } else {
        htmlElement.setAttribute('data-theme', 'light');
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const currentTheme = htmlElement.getAttribute('data-theme');
            let newTheme = 'light';
            
            if (currentTheme === 'light') {
                newTheme = 'dark';
            }
            
            htmlElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    // === Mobile Menu Toggle ===
    const menuToggleBtn = document.getElementById('menu-toggle');
    const mainNav = document.getElementById('main-nav');

    if (menuToggleBtn && mainNav) {
        menuToggleBtn.addEventListener('click', function() {
            mainNav.classList.toggle('active');
            const expanded = menuToggleBtn.getAttribute('aria-expanded') === 'true' || false;
            menuToggleBtn.setAttribute('aria-expanded', !expanded);
        });
    }

    function closeMenu(restoreFocus) {
        if(!mainNav || !menuToggleBtn) return;
        mainNav.classList.remove('active');
        menuToggleBtn.setAttribute('aria-expanded','false');
        if(restoreFocus) menuToggleBtn.focus();
    }
    document.addEventListener('keydown', function(e) {
        if(e.key==='Escape' && mainNav && mainNav.classList.contains('active')) closeMenu(true);
    });
    if(mainNav) mainNav.addEventListener('click', e=>{if(e.target.closest('a')) closeMenu(false);});
    window.addEventListener('resize', ()=>{if(window.innerWidth>960)closeMenu(false);});

    // === Submenu Accessibility Toggles ===
    const parentMenuItems = document.querySelectorAll('.menu-item-has-children, .page_item_has_children');
    parentMenuItems.forEach(function(item) {
        const link = item.querySelector('a');
        if (link) {
            const setExpanded = (expanded) => {
                link.setAttribute('aria-expanded', expanded);
            };
            item.addEventListener('mouseenter', () => setExpanded('true'));
            item.addEventListener('mouseleave', () => setExpanded('false'));
            item.addEventListener('focusin', () => setExpanded('true'));
            item.addEventListener('focusout', (e) => {
                if (!item.contains(e.relatedTarget)) {
                    setExpanded('false');
                }
            });
        }
    });

    // === Header Search Toggle ===
    const searchToggleBtn = document.getElementById('search-toggle');
    const headerSearchContainer = document.getElementById('header-search-container');

    if (searchToggleBtn && headerSearchContainer) {
        const searchField = headerSearchContainer.querySelector('.search-field');
        searchToggleBtn.addEventListener('click', function() {
            headerSearchContainer.classList.toggle('active');
            const isActive = headerSearchContainer.classList.contains('active');
            searchToggleBtn.setAttribute('aria-expanded', isActive);
            if (isActive && searchField) {
                searchField.focus();
            }
        });

        // Close search on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && headerSearchContainer.classList.contains('active')) {
                headerSearchContainer.classList.remove('active');
                searchToggleBtn.setAttribute('aria-expanded', false);
                searchToggleBtn.focus();
            }
        });
    }

    // === Reading Progress Bar ===
    const progressBar = document.getElementById('reading-progress');
    
    if (progressBar) {
        // Only run progress bar logic if we are on a single page that has scrollable content
        const updateProgressBar = () => {
            const scrollTop = window.scrollY || document.documentElement.scrollTop;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            
            if (docHeight > 0) {
                const scrollPercent = (scrollTop / docHeight) * 100;
                progressBar.style.width = scrollPercent + '%';
            }
        };

        window.addEventListener('scroll', updateProgressBar);
        window.addEventListener('resize', updateProgressBar);
        updateProgressBar(); // Initial call
    }

    // === Search Autocomplete ===
    const searchForms = document.querySelectorAll('.search-form');
    searchForms.forEach(form => {
        const input = form.querySelector('.search-field');
        if (!input) return;

        // Create results container
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'search-autocomplete-results';
        resultsContainer.setAttribute('role', 'listbox');
        resultsContainer.setAttribute('aria-label', 'Sugerencias de búsqueda');
        form.appendChild(resultsContainer);

        let debounceTimeout = null;
        let selectedIndex = -1;
        let items = [];

        const updateSelection = (newIndex) => {
            items.forEach((item, idx) => {
                if (idx === newIndex) {
                    item.classList.add('selected');
                    item.setAttribute('aria-selected', 'true');
                    item.scrollIntoView({ block: 'nearest' });
                } else {
                    item.classList.remove('selected');
                    item.setAttribute('aria-selected', 'false');
                }
            });
            selectedIndex = newIndex;
        };

        const closeDropdown = () => {
            resultsContainer.classList.remove('active');
            resultsContainer.innerHTML = '';
            selectedIndex = -1;
            items = [];
        };

        const fetchResults = (query) => {
            if (query.trim().length < 2) {
                closeDropdown();
                return;
            }

            resultsContainer.innerHTML = '<div class="autocomplete-loading" role="status" aria-live="polite">Buscando...</div>';
            resultsContainer.classList.add('active');

            const apiUrl = `/wp-json/datogedon-reader/v1/search?q=${encodeURIComponent(query)}`;

            fetch(apiUrl)
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    resultsContainer.innerHTML = '';
                    if (data.length === 0) {
                        resultsContainer.innerHTML = `<div class="autocomplete-no-results">No se encontraron resultados para "${escapeHTML(query)}"</div>`;
                        items = [];
                        selectedIndex = -1;
                        return;
                    }

                    data.forEach((post, index) => {
                        const itemLink = document.createElement('a');
                        itemLink.href = post.permalink;
                        itemLink.className = 'autocomplete-item';
                        itemLink.setAttribute('role', 'option');
                        itemLink.setAttribute('id', `autocomplete-option-${index}`);
                        itemLink.setAttribute('aria-selected', 'false');

                        // Thumbnail
                        if (post.thumbnail) {
                            const img = document.createElement('img');
                            img.className = 'autocomplete-thumb';
                            img.src = post.thumbnail;
                            img.alt = '';
                            img.loading = 'lazy';
                            itemLink.appendChild(img);
                        }

                        // Info container
                        const info = document.createElement('div');
                        info.className = 'autocomplete-info';

                        const title = document.createElement('span');
                        title.className = 'autocomplete-title';
                        title.textContent = post.title;
                        info.appendChild(title);

                        const date = document.createElement('span');
                        date.className = 'autocomplete-meta';
                        date.textContent = post.date;
                        info.appendChild(date);

                        itemLink.appendChild(info);
                        resultsContainer.appendChild(itemLink);
                    });

                    items = Array.from(resultsContainer.querySelectorAll('.autocomplete-item'));
                    selectedIndex = -1;
                })
                .catch(error => {
                    console.error('Error fetching search autocomplete results:', error);
                    resultsContainer.innerHTML = '<div class="autocomplete-no-results">Error al buscar. Intente de nuevo.</div>';
                });
        };

        // Event listener for inputs with debounce
        input.addEventListener('input', function() {
            clearTimeout(debounceTimeout);
            const query = this.value;
            debounceTimeout = setTimeout(() => {
                fetchResults(query);
            }, 200);
        });

        // Focus event
        input.addEventListener('focus', function() {
            const query = this.value;
            if (query.trim().length >= 2) {
                fetchResults(query);
            }
        });

        // Keydown keyboard navigation
        input.addEventListener('keydown', function(e) {
            if (!resultsContainer.classList.contains('active') || items.length === 0) {
                return;
            }

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                let nextIndex = selectedIndex + 1;
                if (nextIndex >= items.length) nextIndex = 0;
                updateSelection(nextIndex);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                let prevIndex = selectedIndex - 1;
                if (prevIndex < 0) prevIndex = items.length - 1;
                updateSelection(prevIndex);
            } else if (e.key === 'Enter') {
                if (selectedIndex >= 0 && selectedIndex < items.length) {
                    e.preventDefault();
                    items[selectedIndex].click();
                }
            } else if (e.key === 'Escape') {
                e.preventDefault();
                closeDropdown();
            }
        });

        // Prevent closing when clicking inside autocomplete dropdown
        resultsContainer.addEventListener('mousedown', function(e) {
            e.preventDefault();
        });

        // Close on clicking outside
        document.addEventListener('click', function(e) {
            if (!form.contains(e.target)) {
                closeDropdown();
            }
        });
    });

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }
});
