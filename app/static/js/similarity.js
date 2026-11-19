(() => {
    const model = JSON.parse(document.getElementById('similarity-data').textContent);
    const svg = document.getElementById('similarity-plot');
    const group = document.getElementById('map-points');
    const panel = document.getElementById('map-selection');
    const colors = ['#00865b', '#3264c8', '#b54c11', '#8850b8', '#bd346b', '#4e7215', '#087f8c', '#775642'];
    const elements = new Map();
    const namespace = 'http://www.w3.org/2000/svg';
    let view = [0, 0, 900, 560];
    let drag = null;
    let moved = false;

    function element(tag, text, parent, className) {
        const node = document.createElement(tag);
        if (text) node.textContent = text;
        if (className) node.className = className;
        parent.appendChild(node);
        return node;
    }

    function profileLink(player, parent, text = player.name) {
        const link = element('a', text, parent);
        link.href = `/players/${encodeURIComponent(player.id)}`;
        return link;
    }

    function select(player) {
        elements.forEach((node, id) => {
            node.setAttribute('aria-pressed', String(id === player.id));
            node.querySelector('circle').setAttribute('r', id === player.id ? '13' : '9');
        });
        panel.replaceChildren();
        if (player.photo && /^https?:\/\//.test(player.photo)) {
            const photo = element('img', '', panel, 'avatar large');
            photo.src = player.photo;
            photo.alt = player.name;
        }
        element('h2', player.name, panel);
        element('p', `${player.position || 'Outfield player'} · Group ${player.cluster}`, panel, 'muted');
        element('p', `${player.minutes} saved minutes · ${player.imputed} features estimated`, panel, 'muted');
        profileLink(player, panel, 'View player profile');
    }

    const xs = model.points.map(player => player.x);
    const ys = model.points.map(player => player.y);
    const xmin = Math.min(...xs), xmax = Math.max(...xs);
    const ymin = Math.min(...ys), ymax = Math.max(...ys);
    model.points.forEach(player => {
        const x = xmax === xmin ? 450 : 75 + (player.x - xmin) / (xmax - xmin) * 750;
        const y = ymax === ymin ? 280 : 475 - (player.y - ymin) / (ymax - ymin) * 390;
        const node = document.createElementNS(namespace, 'g');
        node.setAttribute('transform', `translate(${x},${y})`);
        node.setAttribute('tabindex', '0');
        node.setAttribute('role', 'button');
        node.setAttribute('aria-label', `${player.name}, group ${player.cluster}`);
        node.setAttribute('aria-pressed', 'false');
        const circle = document.createElementNS(namespace, 'circle');
        circle.setAttribute('r', '9');
        circle.setAttribute('fill', colors[player.cluster - 1]);
        circle.setAttribute('stroke', '#fff');
        circle.setAttribute('stroke-width', '2');
        node.appendChild(circle);
        const label = document.createElementNS(namespace, 'text');
        label.setAttribute('y', '-18');
        label.setAttribute('text-anchor', 'middle');
        label.textContent = player.name;
        node.appendChild(label);
        node.addEventListener('click', () => { if (!moved) select(player); });
        node.addEventListener('keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                select(player);
            }
        });
        group.appendChild(node);
        elements.set(player.id, node);
    });
    for (let cluster = 1; cluster <= model.clusters; cluster++) {
        const label = element('span', '', document.getElementById('map-legend'));
        const dot = element('i', '', label, 'dot');
        dot.style.background = colors[cluster - 1];
        label.appendChild(document.createTextNode(`Group ${cluster}`));
    }

    function draw() { svg.setAttribute('viewBox', view.join(' ')); }
    function zoom(factor) {
        const width = Math.max(180, Math.min(3600, view[2] * factor));
        const height = width * 560 / 900;
        view = [view[0] + (view[2] - width) / 2, view[1] + (view[3] - height) / 2, width, height];
        draw();
    }
    document.getElementById('zoom-in').addEventListener('click', () => zoom(0.8));
    document.getElementById('zoom-out').addEventListener('click', () => zoom(1.25));
    document.getElementById('map-reset').addEventListener('click', () => { view = [0, 0, 900, 560]; draw(); });
    svg.addEventListener('wheel', event => { event.preventDefault(); zoom(event.deltaY < 0 ? 0.9 : 1.1); }, {passive: false});
    svg.addEventListener('pointerdown', event => {
        moved = false;
        drag = {x: event.clientX, y: event.clientY, view: [...view], id: event.pointerId};
    });
    svg.addEventListener('pointermove', event => {
        if (!drag) return;
        const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
        if (Math.abs(dx) + Math.abs(dy) > 5) {
            moved = true;
            svg.setPointerCapture(drag.id);
            const box = svg.getBoundingClientRect();
            view[0] = drag.view[0] - dx * view[2] / box.width;
            view[1] = drag.view[1] - dy * view[3] / box.height;
            draw();
        }
    });
    svg.addEventListener('pointerup', () => { drag = null; });
    svg.addEventListener('pointercancel', () => { drag = null; });
    select(model.points[0]);
})();
