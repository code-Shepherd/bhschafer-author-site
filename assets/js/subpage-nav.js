document.addEventListener('DOMContentLoaded', function () {
	const topbar = document.querySelector('.subpage-topbar');

	if (!topbar) return;

	function updateTopbarState() {
		document.body.classList.toggle('subpage-scrolled', window.scrollY > 24);
	}

	updateTopbarState();
	window.addEventListener('scroll', updateTopbarState, { passive: true });
});
