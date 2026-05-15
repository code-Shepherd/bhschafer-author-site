Dimension by HTML5 UP
html5up.net | @ajlkn
Free for personal and commercial use under the CCA 3.0 license (html5up.net/license)


This is Dimension, a fun little one-pager with modal-ized (is that a word?) "pages"
and a cool depth effect (click on a menu item to see what I mean). Simple, fully
responsive, and kitted out with all the usual pre-styled elements you'd expect.
Hope you dig it :)

Demo images* courtesy of Unsplash, a radtastic collection of CC0 (public domain) images
you can use for pretty much whatever.

(* = not included)

AJ
aj@lkn.io | @ajlkn


Credits:

	Demo Images:
		Unsplash (unsplash.com)

	Icons:
		Font Awesome (fontawesome.io)

	Other:
		jQuery (jquery.com)
		Responsive Tools (github.com/ajlkn/responsive-tools)

Markdown blog workflow
----------------------

This static site can generate blog posts from Markdown without adding a backend,
database, or JavaScript framework.

1. Put Markdown posts in `content/blog/`.
2. Include YAML frontmatter with these fields:

   ```yaml
   ---
   title: Example Post
   slug: example-post
   date: 2026-05-15
   updated:
   description: A short archive and meta description.
   author: B. H. Schafer
   category: Essay
   tags:
     - example
   cover_image:
   cover_alt:
   canonical_url:
   ---
   ```

3. Install the lightweight local build dependencies:

   ```sh
   pip install python-frontmatter markdown
   ```

4. Build the static blog output:

   ```sh
   python scripts/build_blog.py
   ```

5. Preview locally:

   ```sh
   python -m http.server 8000
   ```

6. Open `http://localhost:8000/blog/`.
7. Commit and push the Markdown source plus generated `blog/` and `data/` changes.

The Markdown files in `content/blog/` are the source of truth. Generated post
pages are written to `blog/{slug}/index.html`, archive data is written to
`data/blog-posts.json`, and generated page folders are tracked in
`data/generated-blog-pages.json` so removed Markdown posts can be safely removed
from the generated output on the next build.
