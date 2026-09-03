# GitHub App for private source access

Use one narrowly scoped GitHub App to let the public website repository read
the two private source repositories named by `sources.lock.yml`:

- `pyeuvics/euvics`
- `pyeuvics/pyEUVICS`

Store the App credentials in `pyeuvics/pyeuvics.github.io`. The App replaces
source deploy keys; it does not grant deployment or website-repository write
access.

This procedure applies while `sources.lock.yml` names the repositories above.
If an authoritative source moves, review and update the lock separately before
changing the App installation. Repository presence or copying alone does not
authorize a source-location change.

## 1. Create the GitHub App

While signed in as an owner of the `pyeuvics` organization:

1. Open **Profile picture → Settings**.
2. Select **Developer settings → GitHub Apps**.
3. Select **New GitHub App**.
4. Configure:
   - **GitHub App name:** for example `EUVICS Documentation Reader`
   - **Homepage URL:** `https://pyeuvics.github.io/`
   - **Webhook:** clear **Active**
   - **Repository permissions → Contents:** **Read-only**
   - Leave every other repository and organization permission at **No access**
   - **Where can this GitHub App be installed?** Select **Only on this account**
5. Select **Create GitHub App**.

Create the App under the `pyeuvics` organization, not a personal account, so it
can be installed on both locked organization repositories.

## 2. Record the Client ID

On the App's **General** page, record the **Client ID**. Store this non-secret
identifier as a repository Actions variable:

```text
EUVICS_DOCS_APP_CLIENT_ID
```

## 3. Generate the private key

On the same App configuration page:

1. Scroll to **Private keys**.
2. Select **Generate a private key**.
3. GitHub downloads a `.pem` file.
4. Keep the file private and never add it to a repository or build artifact.

The secret must contain the complete downloaded file, including its `BEGIN`
and `END` lines. Do not print the key in a terminal, workflow log, or generated
page.

## 4. Install the App on the two private sources

From the App configuration page:

1. Select **Install App**.
2. Select **Install** beside the `pyeuvics` organization.
3. Choose **Only select repositories**.
4. Select only:
   - `pyeuvics/euvics`
   - `pyeuvics/pyEUVICS`
5. Complete the installation.

Do not install the App on every repository. Read-only Contents access to these
two sources is sufficient.

## 5. Add the website repository variable and secret

Open:

**pyeuvics/pyeuvics.github.io → Settings → Secrets and variables → Actions**

Create the Client ID under **Actions variables** and the private key under
**Actions secrets**:

| Name | Value |
| --- | --- |
| `EUVICS_DOCS_APP_CLIENT_ID` | GitHub App Client ID (repository variable) |
| `EUVICS_DOCS_APP_PRIVATE_KEY` | Complete downloaded `.pem` file (repository secret) |

Use repository-level configuration rather than `github-pages` environment
configuration because the Pages build and source-update validation jobs need
source read access. Pull-request validation deliberately receives no secret.
GitHub will not display the secret value again.

Verify only their presence, without revealing values:

```bash
gh variable list --repo pyeuvics/pyeuvics.github.io
gh secret list --repo pyeuvics/pyeuvics.github.io
```

The output should list:

```text
EUVICS_DOCS_APP_CLIENT_ID
EUVICS_DOCS_APP_PRIVATE_KEY
```

## 6. Workflow installation-token checkout

The trusted source-reading jobs in these workflows mint a short-lived
installation token before checking out either private source:

- `.github/workflows/pages.yml`
- `.github/workflows/source-update.yml`

They use this bounded token step:

```yaml
- name: Create source-read installation token
  id: source_token
  uses: actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1 # v3
  with:
    client-id: ${{ vars.EUVICS_DOCS_APP_CLIENT_ID }}
    private-key: ${{ secrets.EUVICS_DOCS_APP_PRIVATE_KEY }}
    owner: pyeuvics
    repositories: |
      euvics
      pyEUVICS
    permission-contents: read
```

Every EUVICS and pyEUVICS checkout in that job must:

- use `token: ${{ steps.source_token.outputs.token }}`;
- retain `persist-credentials: false`;
- retain the repository, exact locked `ref`, path, and fetch-depth settings;
- keep the post-checkout credential scan; and
- do not print the token or persist it in artifacts.

The workflow's `GITHUB_TOKEN` permissions do not provide cross-repository
private-source access. The short-lived App installation token supplies only the
separately granted read access.

Workflow-structure tests enforce this configuration.

## 7. Verify in GitHub Actions

After the reviewed workflow conversion is committed and pushed:

1. Confirm pull-request validation contains no secret or App-token step.
2. Confirm the trusted source-token step succeeds without exposing credentials.
3. Confirm both exact locked source checkouts succeed.
4. Confirm the runner credential scan succeeds.
5. Confirm **Site validation / Validate public artifact** passes.
6. Confirm **Deploy GitHub Pages** builds and deploys the validated artifact.
7. Confirm the signed-out site at <https://pyeuvics.github.io/> shows the
   expected MkDocs site.

Remove any superseded deploy-key secrets and source-repository deploy keys only
after all App-token workflows pass. Secret and key removal is a separate
authorized administrator action; do not remove the last working credential
during cutover.
