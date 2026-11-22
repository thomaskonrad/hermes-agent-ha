# Rotating the upstream-sync App key

The daily upstream sync opens pull requests with a GitHub App token. The App is
installed on this repository only, with two permissions: contents write and
pull requests write. Its private key is stored as the repository secret
`UPSTREAM_SYNC_APP_PRIVATE_KEY`, and its App ID as the repository variable
`UPSTREAM_SYNC_APP_ID`.

## Policy

- **Scheduled:** rotate the private key **every 12 months**.
- **Immediately** if the key may have leaked: pasted into a chat, committed,
  shown in a log, or left on a shared or lost machine.

## Rotate the key

1. Open the App's settings: GitHub → Settings → Developer settings → GitHub Apps
   → the upstream-sync App → **Private keys**.
2. Select **Generate a private key**. GitHub downloads a `.pem` file.
3. In the repository: Settings → Secrets and variables → Actions → **Secrets**,
   and replace `UPSTREAM_SYNC_APP_PRIVATE_KEY` with the full contents of the
   `.pem` file, including the `BEGIN` and `END` lines.
4. Run the sync once by hand to check the new key works:
   Actions → **Upstream sync** → **Run workflow**. On a day with no new
   upstream release, the `detect` job reports `up-to-date` and the job
   finishes without opening a pull request. A failure in the token step means
   the key or the App ID is wrong.
5. Back under the App's **Private keys**, **delete the old key**. Until you
   do, a leaked old key still works.
6. Delete the local `.pem` file. Do not keep it in the repository, in a
   backup folder, or in a chat.
7. Record the rotation date in the table below.

If the key may have leaked, do steps 1–3 and 5 at once, and check the App's
recent activity for unexpected use. Then review any pull requests the App
opened in the same period.

## Rotation log

| Date rotated | By | Reason |
|---|---|---|
| _not yet rotated_ | | initial key |

## Notes

- The private key only ever belongs in the repository secret. It must not
  appear in workflow logs, in a commit, or in an issue.
- The token the workflow uses is minted for this repository only, and it expires
  when the job ends. Rotating the private key does not change that.
