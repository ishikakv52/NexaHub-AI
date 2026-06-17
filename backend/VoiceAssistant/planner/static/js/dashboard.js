document.addEventListener('DOMContentLoaded', function() {
    initWaterRing();
    initMealChecklist();
});

// Cross-tab/page meal sync: BroadcastChannel if available, else localStorage fallback
const mealSyncChannel = ('BroadcastChannel' in window) ? new BroadcastChannel('meal-sync') : null;

function broadcastMealToggle(mealId, isConsumed) {
    const payload = { meal_id: String(mealId), is_consumed: !!isConsumed, ts: Date.now() };
    if (mealSyncChannel) {
        mealSyncChannel.postMessage(payload);
    } else {
        try {
            localStorage.setItem('meal_sync_event', JSON.stringify(payload));
            // storage event will fire in other tabs
        } catch (e) {
            console.warn('meal sync failed', e);
        }
    }
}

function handleMealSyncMessage(payload) {
    if (!payload || !payload.meal_id) return;
    // update checklist checkbox if present
    const chk = document.querySelector(`.checklist-meal[data-meal-id="${payload.meal_id}"]`);
    if (chk) {
        chk.checked = !!payload.is_consumed;
        const label = document.querySelector(`label[for=chk${payload.meal_id}]`);
        if (label) {
            if (payload.is_consumed) label.classList.add('text-decoration-line-through', 'text-muted');
            else label.classList.remove('text-decoration-line-through', 'text-muted');
        }
    }
    // update diet plan checkbox if present
    const planChk = document.getElementById(`planMealCheck${payload.meal_id}`);
    if (planChk) {
        planChk.checked = !!payload.is_consumed;
        const lbl = planChk.closest('form')?.querySelector('label');
        if (lbl) {
            if (payload.is_consumed) lbl.classList.add('text-decoration-line-through', 'text-muted');
            else lbl.classList.remove('text-decoration-line-through', 'text-muted');
        }
    }
    // update progress UI
    updateMealsProgress(payload.meal_id);
}

if (mealSyncChannel) {
    mealSyncChannel.onmessage = (e) => handleMealSyncMessage(e.data);
} else {
    window.addEventListener('storage', (e) => {
        if (e.key === 'meal_sync_event' && e.newValue) {
            try { handleMealSyncMessage(JSON.parse(e.newValue)); } catch (err) { }
        }
    });
}

// expose helper for other scripts
window.broadcastMealToggle = broadcastMealToggle;

function initWaterRing() {
    const ring = document.querySelector('.water-ring');
    if (!ring) return;

    const percent = parseFloat(ring.getAttribute('data-percent')) || 0;
    const circle = ring.querySelector('.water-progress');
    if (!circle) return;

    const circumference = 2 * Math.PI * 52;
    circle.setAttribute('stroke-dasharray', circumference);

    setTimeout(function() {
        const offset = circumference - (percent / 100) * circumference;
        circle.style.strokeDashoffset = offset;
    }, 300);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function initMealChecklist() {
    const checkboxes = document.querySelectorAll('.checklist-meal');
    if (!checkboxes || checkboxes.length === 0) return;

    const csrftoken = getCookie('csrftoken');

    const checklist = document.getElementById('today-checklist') || document.querySelector('.checklist-list');

    // Apply stored order if present
    const todayDate = checklist ? checklist.dataset.date : null;
    if (checklist && todayDate) {
        applyStoredOrder(checklist, todayDate);
    }

    checkboxes.forEach(cb => {
        cb.addEventListener('change', function (e) {
            const mealId = this.dataset.mealId;
            fetch(`/meal/${mealId}/toggle/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            }).then(res => res.json()).then(data => {
                if (data && data.success) {
                    const label = document.querySelector(`label[for=chk${mealId}]`);
                    if (label) {
                        if (data.is_consumed) {
                            label.classList.add('text-decoration-line-through', 'text-muted');
                        } else {
                            label.classList.remove('text-decoration-line-through', 'text-muted');
                        }
                    }
                    // update progress bar
                    updateMealsProgress(data.meal_id || mealId);
                    // broadcast to other open pages/tabs so diet plan and dashboard sync
                    try { broadcastMealToggle(data.meal_id || mealId, data.is_consumed); } catch (err) { }
                } else {
                    // Revert checkbox on error
                    e.target.checked = !e.target.checked;
                }
            }).catch(() => {
                e.target.checked = !e.target.checked;
            });
        });
    });

    // Make checklist reorderable with HTML5 drag/drop and persist order in localStorage
    if (checklist) {
        makeChecklistDraggable(checklist, todayDate);
    }
}

function updateMealsProgress(changedMealId) {
    const list = document.querySelector('.checklist-list');
    if (!list) return;
    const items = list.querySelectorAll('li');
    let total = 0, eaten = 0;
    items.forEach(li => {
        const cb = li.querySelector('.checklist-meal');
        if (cb) {
            total += 1;
            if (cb.checked) eaten += 1;
        }
    });
    const percent = total ? Math.round((eaten / total) * 100) : 0;
    const bar = document.getElementById('meals-progress');
    if (bar) {
        bar.style.width = percent + '%';
        bar.setAttribute('aria-valuenow', percent);
        bar.textContent = percent + '%';
    }
    // update small text values
    const smalls = document.querySelectorAll('.checklist-list + .mb-3 small, .list-group + .mb-3 small');
    // prefer updating explicit smalls in markup; fallback omitted for brevity
}

function applyStoredOrder(listEl, dateKey) {
    const key = `meal_order_${dateKey}`;
    const stored = localStorage.getItem(key);
    if (!stored) return;
    try {
        const order = JSON.parse(stored);
        const idToNode = {};
        listEl.querySelectorAll('li[data-meal-id]').forEach(li => idToNode[li.dataset.mealId] = li);
        order.forEach(id => {
            if (idToNode[id]) listEl.appendChild(idToNode[id]);
        });
    } catch (e) {
        console.error('Invalid stored meal order', e);
    }
}

function makeChecklistDraggable(listEl, dateKey) {
    let dragSrc = null;
    listEl.querySelectorAll('li[draggable=true]').forEach(li => {
        li.addEventListener('dragstart', (e) => {
            dragSrc = li;
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', li.dataset.mealId);
            li.classList.add('dragging');
        });
        li.addEventListener('dragend', () => {
            li.classList.remove('dragging');
            saveCurrentOrder(listEl, dateKey);
        });
        li.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            const target = e.currentTarget;
            if (target && target !== dragSrc) {
                const rect = target.getBoundingClientRect();
                const next = (e.clientY - rect.top) > (rect.height / 2);
                listEl.insertBefore(dragSrc, next ? target.nextSibling : target);
            }
        });
    });
}

function saveCurrentOrder(listEl, dateKey) {
    if (!dateKey) return;
    const key = `meal_order_${dateKey}`;
    const ids = Array.from(listEl.querySelectorAll('li[data-meal-id]')).map(li => li.dataset.mealId);
    localStorage.setItem(key, JSON.stringify(ids));
}
