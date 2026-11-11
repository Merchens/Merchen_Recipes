# Merchen Family Recipes

A recipe website for the family, published free with GitHub Pages:
**https://merchens.github.io/Merchen_Recipes/**

Family members add recipes through a Google Form (no accounts needed).
Every 3 hours, an automation copies new form responses into the site.

## One-time setup

### 1. Turn on GitHub Pages
Repo **Settings → Pages → Build and deployment → Source: GitHub Actions**.

### 2. Make the Google Form
Create a form at [forms.google.com](https://forms.google.com) with these questions.
The wording just needs to *contain* the words in bold:

| Question | Type | Required |
| --- | --- | --- |
| **Recipe name** | Short answer | Yes |
| **Your name** | Short answer | Yes |
| **Category** | Multiple choice: Breakfast, Main Dish, Side Dish, Soup & Salad, Dessert, Baking & Bread, Drinks, Snacks & Appetizers, Other | Yes |
| **Serves** | Short answer | No |
| **Prep time** | Short answer | No |
| **Cook time** | Short answer | No |
| **Ingredients** (one per line) | Paragraph | Yes |
| **Instructions** (one step per line) | Paragraph | Yes |
| **Notes** or family story | Paragraph | No |
| **Photo link** (Google Drive / Photos share link, set to "Anyone with the link") | Short answer | No |

Use a *Photo link* question rather than Google's "File upload" question —
file upload forces people to sign in to Google.

In the form's **Settings → Responses**, make sure "Collect email addresses" is off
and "Limit to 1 response" is off, so nobody needs to sign in.

### 3. Connect the form's responses to the site
1. In the form, **Responses → Link to Sheets** to create a response spreadsheet.
2. In that sheet, **File → Share → Publish to web**, pick the responses tab,
   choose **Comma-separated values (.csv)**, and click **Publish**. Copy the link.
3. In this repo: **Settings → Secrets and variables → Actions → Variables tab →
   New repository variable**. Name: `FORM_CSV_URL`, value: the link.

> The published CSV can be read by anyone who has the link. Recipes end up on the
> public site anyway, but don't add form questions for private info (emails, phone numbers).

### 4. Add the form link to the site
In the form, click **Send → link icon**, copy the link, and paste it into
`_config.yml` as `google_form_url`. The site then shows an **+ Add a recipe** button.

## Day to day

- New recipes appear within ~3 hours. To publish right away: **Actions →
  Import recipes and publish site → Run workflow**.
- To fix a recipe, edit its file in `_recipes/` on GitHub (pencil icon).
- To remove one, delete its file. It won't be re-imported.
- Delete `_recipes/sample-chocolate-chip-cookies.md` once real recipes are in.

## How it's built

- [Jekyll](https://jekyllrb.com/) static site; each recipe is a Markdown file in `_recipes/`.
- `scripts/import_form.py` turns form responses into recipe files;
  `scripts/imported.txt` remembers which responses were already imported.
- `.github/workflows/site.yml` runs the import, commits new recipes, and deploys the site.
