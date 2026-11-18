# DonXDon Clothing

A Baltimore streetwear site with an initially empty product catalog. This is a product showcase; checkout, payments, and customer accounts are not enabled.

## Owner: add products

1. Sign in to GitHub and open [Manage product catalog](https://github.com/dipsetdon/donxdon/actions/workflows/catalog.yml).
2. Select **Run workflow**, leave the branch on `main`, and choose `add_or_update`.
3. Enter a stable product ID, name, category, and USD price. The description and photo are optional. To upload a photo, first add the JPEG, PNG, or WebP to the [media folder](https://github.com/dipsetdon/donxdon/tree/main/media), then enter its filename. The maximum photo file size is 5 MB.
4. Run the workflow. Use the same ID and re-enter the complete listing to update it. Select `remove` and enter its ID to remove it from the next site build. Select `check` to validate without changing anything.

Only users with write access to the repository can run the workflow. The repository and catalog are public. Do not add private information, draft products, or photos you do not want to publish. Removing a listing does not erase Git history.

## Build and launch

Run `python3 scripts/catalog.py build` from the repository root. Serve the generated `_site/` directory with `python3 -m http.server 8000 --directory _site` for local testing. For hosting, connect this repo's `main` branch and set the build command to `python3 scripts/catalog.py build` and the output directory to `_site`. Configure the custom domain `donxdonclo.com` at the selected host after it is registered.

The catalog workflow uses GitHub's repository token to save changes. After connecting hosting, set `CATALOG_DEPLOY_HOOK` as a GitHub Actions repository secret to the host's private HTTPS deployment-hook URL. The workflow will request a fresh build after a catalog change. If no hook is configured and your host does not auto-build, trigger a fresh build from the host's dashboard.

Run `python3 -m unittest scripts.test_catalog` to check the catalog editor.
