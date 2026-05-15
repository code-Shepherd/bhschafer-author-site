(function () {
	'use strict';

	function createTextElement(tagName, className, text) {
		var element = document.createElement(tagName);
		if (className) {
			element.className = className;
		}
		element.textContent = text || '';
		return element;
	}

	function createPostCard(post) {
		var article = document.createElement('article');
		article.className = 'blog-preview';

		var content = document.createElement('div');
		content.className = 'blog-preview-content';

		var heading = document.createElement('h3');
		var headingLink = document.createElement('a');
		headingLink.href = post.url;
		headingLink.textContent = post.title;
		heading.appendChild(headingLink);

		content.appendChild(heading);
		content.appendChild(createTextElement('p', 'blog-date', post.displayDate));
		content.appendChild(createTextElement('p', 'blog-description', post.description));
		content.appendChild(createTextElement('p', 'blog-category', post.category));

		var action = document.createElement('div');
		action.className = 'blog-preview-action';

		var readLink = document.createElement('a');
		readLink.href = post.url;
		readLink.className = 'button';
		readLink.innerHTML = 'Read &rarr;';
		action.appendChild(readLink);

		article.appendChild(content);
		article.appendChild(action);

		return article;
	}

	function normalize(value) {
		return String(value || '').toLowerCase();
	}

	document.addEventListener('DOMContentLoaded', function () {
		var list = document.getElementById('blog-list');
		var search = document.getElementById('blog-search');
		var categoryFilter = document.getElementById('category-filter');
		var sortPosts = document.getElementById('sort-posts');
		var emptyState = document.getElementById('blog-empty-state');

		if (!list || !search || !categoryFilter || !sortPosts || !emptyState) {
			return;
		}

		var allPosts = [];

		function populateCategories(posts) {
			var categories = posts
				.map(function (post) { return post.category; })
				.filter(function (category, index, array) {
					return category && array.indexOf(category) === index;
				})
				.sort(function (a, b) { return a.localeCompare(b); });

			categories.forEach(function (category) {
				var option = document.createElement('option');
				option.value = category;
				option.textContent = category;
				categoryFilter.appendChild(option);
			});
		}

		function filteredAndSortedPosts() {
			var query = normalize(search.value).trim();
			var selectedCategory = categoryFilter.value;
			var sortDirection = sortPosts.value;

			return allPosts
				.filter(function (post) {
					var matchesTitle = !query || normalize(post.title).indexOf(query) !== -1;
					var matchesCategory = selectedCategory === 'all' || post.category === selectedCategory;
					return matchesTitle && matchesCategory;
				})
				.sort(function (a, b) {
					var aTime = Date.parse(a.date);
					var bTime = Date.parse(b.date);
					return sortDirection === 'oldest' ? aTime - bTime : bTime - aTime;
				});
		}

		function renderPosts() {
			var posts = filteredAndSortedPosts();
			list.replaceChildren();

			posts.forEach(function (post) {
				list.appendChild(createPostCard(post));
			});

			emptyState.hidden = posts.length > 0;
		}

		fetch('../data/blog-posts.json')
			.then(function (response) {
				if (!response.ok) {
					throw new Error('Unable to load blog post data.');
				}
				return response.json();
			})
			.then(function (posts) {
				if (!Array.isArray(posts)) {
					throw new Error('Blog post data is not an array.');
				}

				allPosts = posts;
				populateCategories(allPosts);
				renderPosts();

				search.addEventListener('input', renderPosts);
				categoryFilter.addEventListener('change', renderPosts);
				sortPosts.addEventListener('change', renderPosts);
			})
			.catch(function (error) {
				console.warn(error.message);
			});
	});
}());
