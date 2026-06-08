document.addEventListener('DOMContentLoaded', function() {
	const trackers = [
		{
			title: "Gods, Monsters, and a Fuzzytail Book I",
			type: "Novel",
			stage: "Re-written",
			progress: 5,
			note: "Chapter 1 re-written"
		},
		{
			title: "Youtube Channel Launch",
			type: "Platform",
			stage: "Writing",
			progress: 10,
			note: "planning essays 3 and 4"
		},
		{
			title: "Sea Beast",
			type: "Short Story",
			stage: "Drafting",
			progress: 30,
			note: "Tentative title. About 30% through the rough draft."
		}
	];

	const body = document.body;
	const tab = document.querySelector('.tracker-tab');
	const panel = document.getElementById('tracker-panel');
	const closeButton = document.querySelector('.tracker-close');
	const backdrop = document.querySelector('.tracker-backdrop');
	const trackerList = document.querySelector('.tracker-list');

	if (!body || !tab || !panel || !trackerList) {
		return;
	}

	function clampProgress(progress) {
		return Math.max(0, Math.min(100, Number(progress) || 0));
	}

	function renderTrackers() {
		const fragment = document.createDocumentFragment();

		trackers.forEach(function(tracker) {
			const progress = clampProgress(tracker.progress);
			const card = document.createElement('article');
			const cardTop = document.createElement('div');
			const title = document.createElement('h3');
			const percent = document.createElement('span');
			const meta = document.createElement('p');
			const progressBar = document.createElement('div');
			const progressFill = document.createElement('span');
			const note = document.createElement('p');

			card.className = 'tracker-card';
			cardTop.className = 'tracker-card-top';
			percent.className = 'tracker-percent';
			meta.className = 'tracker-meta';
			progressBar.className = 'tracker-progress';
			note.className = 'tracker-note';

			title.textContent = tracker.title;
			percent.textContent = progress + '%';
			meta.textContent = tracker.type + ' · ' + tracker.stage;
			progressBar.setAttribute('aria-label', progress + '% complete');
			progressFill.style.width = progress + '%';
			note.textContent = '• ' + tracker.note;

			cardTop.appendChild(title);
			cardTop.appendChild(percent);
			progressBar.appendChild(progressFill);
			card.appendChild(cardTop);
			card.appendChild(meta);
			card.appendChild(progressBar);
			card.appendChild(note);
			fragment.appendChild(card);
		});

		trackerList.replaceChildren(fragment);
	}

	function openTracker() {
		body.classList.add('tracker-open');
		tab.setAttribute('aria-expanded', 'true');
		panel.setAttribute('aria-hidden', 'false');
	}

	function closeTracker() {
		body.classList.remove('tracker-open');
		tab.setAttribute('aria-expanded', 'false');
		panel.setAttribute('aria-hidden', 'true');
	}

	renderTrackers();

	tab.addEventListener('click', function() {
		if (body.classList.contains('tracker-open')) {
			closeTracker();
		} else {
			openTracker();
		}
	});

	if (closeButton) {
		closeButton.addEventListener('click', closeTracker);
	}

	if (backdrop) {
		backdrop.addEventListener('click', closeTracker);
	}

	document.addEventListener('keydown', function(event) {
		if (event.key === 'Escape' && body.classList.contains('tracker-open')) {
			closeTracker();
		}
	});
});
