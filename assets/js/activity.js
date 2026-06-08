document.addEventListener('DOMContentLoaded', function() {
	const body = document.body;
	const tab = document.querySelector('.activity-tab');
	const panel = document.getElementById('activity-panel');
	const backdrop = document.querySelector('.activity-backdrop');
	const sourceTabs = Array.prototype.slice.call(document.querySelectorAll('.activity-source-tab'));
	const activityList = document.querySelector('.activity-list');
	const cache = {};
	let activeSource = 'substack';

	if (!body || !tab || !panel || !activityList || !sourceTabs.length) {
		return;
	}

	function closeTracker() {
		const trackerTab = document.querySelector('.tracker-tab');
		const trackerPanel = document.getElementById('tracker-panel');

		body.classList.remove('tracker-open');

		if (trackerTab) {
			trackerTab.setAttribute('aria-expanded', 'false');
		}

		if (trackerPanel) {
			trackerPanel.setAttribute('aria-hidden', 'true');
		}
	}

	function openActivity() {
		closeTracker();
		body.classList.add('activity-open');
		tab.setAttribute('aria-expanded', 'true');
		panel.setAttribute('aria-hidden', 'false');
		loadSource(activeSource);
	}

	function closeActivity() {
		body.classList.remove('activity-open');
		tab.setAttribute('aria-expanded', 'false');
		panel.setAttribute('aria-hidden', 'true');
	}

	function setStatus(message) {
		const status = document.createElement('p');
		status.className = 'activity-status';
		status.textContent = message;
		activityList.replaceChildren(status);
	}

	function stripHtml(value) {
		const scratch = document.createElement('div');
		scratch.innerHTML = value || '';
		return scratch.textContent || scratch.innerText || '';
	}

	function truncate(value, limit) {
		const text = (value || '').replace(/\s+/g, ' ').trim();

		if (text.length <= limit) {
			return text;
		}

		return text.slice(0, limit).replace(/\s+\S*$/, '').trim() + '…';
	}

	function formatDate(value) {
		if (!value) {
			return '';
		}

		const parsed = new Date(value);

		if (Number.isNaN(parsed.getTime())) {
			return value;
		}

		return parsed.toLocaleDateString(undefined, {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	function normalizeSubstackItem(item) {
		return {
			title: item.title || 'Untitled',
			link: item.link || 'https://bhschafer.substack.com/',
			date: item.pubDate || '',
			source: 'Substack',
			excerpt: truncate(stripHtml(item.description || item.content || ''), 180),
			external: true
		};
	}

	function normalizeBlogPost(post) {
		return {
			title: post.title || 'Untitled',
			link: post.url || '/blog/',
			date: post.displayDate || post.date || '',
			source: post.category || 'Blog',
			excerpt: truncate(post.description || '', 180),
			external: false
		};
	}

	function getSourceLabel(source) {
		return source === 'blog' ? 'Blog' : 'Substack';
	}

	function fetchSubstack() {
		const feedUrl = encodeURIComponent('https://bhschafer.substack.com/feed');
		const apiUrl = `https://api.rss2json.com/v1/api.json?rss_url=${feedUrl}`;

		return fetch(apiUrl)
			.then(function(response) {
				if (!response.ok) {
					throw new Error('Substack request failed');
				}

				return response.json();
			})
			.then(function(data) {
				return (data.items || []).slice(0, 5).map(normalizeSubstackItem);
			});
	}

	function fetchBlog() {
		return fetch('/data/blog-posts.json')
			.then(function(response) {
				if (!response.ok) {
					throw new Error('Blog request failed');
				}

				return response.json();
			})
			.then(function(posts) {
				return (Array.isArray(posts) ? posts : []).slice(0, 5).map(normalizeBlogPost);
			});
	}

	function renderCards(items) {
		if (!items.length) {
			setStatus('No recent activity found.');
			return;
		}

		const fragment = document.createDocumentFragment();

		items.forEach(function(item) {
			const card = document.createElement('article');
			const title = document.createElement('h3');
			const meta = document.createElement('p');
			const excerpt = document.createElement('p');
			const link = document.createElement('a');
			const parts = [item.source, formatDate(item.date)].filter(Boolean);

			card.className = 'activity-card';
			meta.className = 'activity-card-meta';
			excerpt.className = 'activity-card-excerpt';
			link.className = 'activity-card-link';

			title.textContent = item.title;
			meta.textContent = parts.join(' · ');
			excerpt.textContent = item.excerpt;
			link.href = item.link;
			link.textContent = 'Read →';

			if (item.external) {
				link.target = '_blank';
				link.rel = 'noopener noreferrer';
			}

			card.appendChild(title);
			card.appendChild(meta);

			if (item.excerpt) {
				card.appendChild(excerpt);
			}

			card.appendChild(link);
			fragment.appendChild(card);
		});

		activityList.replaceChildren(fragment);
	}

	function loadSource(source) {
		const label = getSourceLabel(source);

		if (cache[source]) {
			renderCards(cache[source]);
			return;
		}

		setStatus('Loading ' + label + ' activity...');

		(source === 'blog' ? fetchBlog() : fetchSubstack())
			.then(function(items) {
				cache[source] = items;
				renderCards(items);
			})
			.catch(function() {
				setStatus('Could not load ' + label + ' activity right now.');
			});
	}

	function setActiveSource(source) {
		activeSource = source;

		sourceTabs.forEach(function(sourceTab) {
			const isActive = sourceTab.getAttribute('data-activity-source') === source;
			sourceTab.classList.toggle('is-active', isActive);
			sourceTab.setAttribute('aria-pressed', isActive ? 'true' : 'false');
		});

		loadSource(source);
	}

	tab.addEventListener('click', function() {
		if (body.classList.contains('activity-open')) {
			closeActivity();
		} else {
			openActivity();
		}
	});

	if (backdrop) {
		backdrop.addEventListener('click', closeActivity);
	}

	sourceTabs.forEach(function(sourceTab) {
		sourceTab.addEventListener('click', function() {
			setActiveSource(sourceTab.getAttribute('data-activity-source') || 'substack');
		});
	});

	document.addEventListener('keydown', function(event) {
		if (event.key === 'Escape' && body.classList.contains('activity-open')) {
			closeActivity();
		}
	});
});
