document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initScrollAnimations();
    initCounters();
    initNavbarScroll();
    autoHideToasts();
    initGroceryList();
});

function initTheme() {
    const toggle = document.getElementById('themeToggle');
    const icon = document.getElementById('themeIcon');
    const saved = localStorage.getItem('nutriplan-theme') || 'light';

    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved, icon);

    if (toggle) {
        toggle.addEventListener('click', function() {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('nutriplan-theme', next);
            updateThemeIcon(next, icon);
        });
    }
}

function updateThemeIcon(theme, icon) {
    if (!icon) return;
    icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
}

function initScrollAnimations() {
    const elements = document.querySelectorAll('.scroll-animate');
    if (!elements.length) return;

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    elements.forEach(function(el) { observer.observe(el); });
}

function initCounters() {
    const counters = document.querySelectorAll('.counter[data-target]');
    counters.forEach(function(counter) {
        const target = parseFloat(counter.getAttribute('data-target')) || 0;
        animateCounter(counter, target);
    });

    const statNumbers = document.querySelectorAll('.stat-number[data-count]');
    const statsObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseInt(el.getAttribute('data-count')) || 0;
                animateCounter(el, target);
                el.classList.add('counted');
                statsObserver.unobserve(el);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(function(el) { statsObserver.observe(el); });
}

function animateCounter(element, target) {
    const duration = 1500;
    const start = performance.now();
    const isFloat = target % 1 !== 0;

    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = target * eased;

        element.textContent = isFloat ? current.toFixed(1) : Math.floor(current);

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = isFloat ? target.toFixed(1) : target;
        }
    }

    requestAnimationFrame(update);
}

function initNavbarScroll() {
    const navbar = document.querySelector('.glass-nav');
    if (!navbar) return;

    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
}

function autoHideToasts() {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(function(toast) {
        setTimeout(function() {
            toast.classList.remove('show');
            setTimeout(function() { toast.remove(); }, 300);
        }, 4000);
    });
}

function initGroceryList() {
    const groceryLists = Array.from(document.querySelectorAll('.grocery-list'));
    if (!groceryLists.length) return;

    const root = document.querySelector('.container[data-grocery-key]');
    const storageKey = getGroceryStorageKey(root);
    if (!storageKey) return;

    groceryLists.forEach(function(list) {
        applySavedGroceryRemovals(list, storageKey);
        hideEmptyCategory(list);
    });

    const saveBtn = document.getElementById('save-grocery-btn');
    if (!saveBtn) return;

    saveBtn.addEventListener('click', function() {
        const checkedItems = document.querySelectorAll('.grocery-check:checked');
        if (!checkedItems.length) return;

        const removedKeys = loadRemovedGroceryItems(storageKey);
        checkedItems.forEach(function(cb) {
            const li = cb.closest('.grocery-item');
            if (!li) return;
            const key = li.dataset.itemKey;
            if (key && !removedKeys.includes(key)) {
                removedKeys.push(key);
            }
            li.remove();
            hideEmptyCategory(cb.closest('.grocery-list'));
        });
        localStorage.setItem(storageKey, JSON.stringify(removedKeys));
    });
}

function getGroceryStorageKey(rootEl) {
    if (!rootEl) return null;
    const planId = rootEl.dataset.groceryKey;
    if (!planId) return null;
    return `removed_grocery_items_plan_${planId}`;
}

function loadRemovedGroceryItems(storageKey) {
    if (!storageKey) return [];
    try {
        const raw = localStorage.getItem(storageKey);
        return raw ? JSON.parse(raw) : [];
    } catch (err) {
        return [];
    }
}

function applySavedGroceryRemovals(listEl, storageKey) {
    const removedKeys = loadRemovedGroceryItems(storageKey);
    if (!removedKeys.length) return;
    listEl.querySelectorAll('.grocery-item').forEach(function(li) {
        const key = li.dataset.itemKey;
        if (key && removedKeys.includes(key)) {
            li.remove();
        }
    });
}

function hideEmptyCategory(listEl) {
    if (!listEl) return;
    const categoryCard = listEl.closest('.grocery-category');
    if (!categoryCard) return;
    if (!listEl.querySelector('.grocery-item')) {
        categoryCard.style.display = 'none';
    }
}

document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href.length <= 1) return;
        const target = document.querySelector(href);
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});
