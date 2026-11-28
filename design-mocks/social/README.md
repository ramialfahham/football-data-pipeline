# Pre-match social image

Run this from the repository root, with the repository's Python environment, a Google Cloud login and Microsoft Edge:

```
python design-mocks/social/prematch.py <fixture_slug>
```

The image is `design-mocks/social/out/<fixture_slug>/<fixture_slug>_linkedin.png`, 1080x1350. Git ignores `out/`.

The run stops with `REFUSED:` and a reason when it cannot state every value on the image.

**Frozen:** `assets/` holds the template's own copies of the CSS, the Inter font with its licence, and the logo. A site change does not change the image. The design, the labels and the metric order change only on request.
