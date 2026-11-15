# Rendered pages — phone widths

Tool: the Browser pane on the site_v2 dev server (sample data), the viewport emulated at 375px and
280px, read through the page's DOM and computed geometry (`getBoundingClientRect`); the
accessibility tree and geometry work in the pane, screenshots do not.

observed:
  - **Teams page, 375px:** the trail shows "Home" alone as a link 44px tall and 49px wide, the nav is 50px tall, and the page does not scroll sideways. Before the Home rule the nav was an empty 6px box.
  - **Teams page, 280px:** the same: "Home" as a 44px link, no sideways scroll.
  - **Competitions, Players and Matches pages (two levels):** read from the served markup, not measured at a width: the trail marks Home as shown and the page as far, the same condition as the Teams page, so under 700px each shows "Home" and hides the page's own name.
  - **Team page (three levels):** Home is far and hidden, "Teams" is shown, the page's own name is far and hidden: the narrow form is unchanged for trails of three or more levels.
