# Browser acceptance checks

## Primary student / reviewer flow

1. Run npm install, npm test and npm run build; address any local toolchain issues before deployment.
2. Run npm run dev and open the printed address.
3. Choose Interactive frontend demo → Student.
4. Verify one Author's name field with the requested helper text, language and dependent faculty/department options.
5. Select Use fictional sample document → Submit document.
6. Confirm immediate Processing with no staged screen, countdown or advance-clock button.
7. After the simulated processing animation, edit abstract/title if desired; check the confirmation box and confirm.
8. Switch to reviewer; locate the same reference in the queue.
9. Click title, author, abstract and certification: sample page/evidence changes.
10. Save review notes; verify they persist on refresh.
11. Request correction; try Other without text (blocked), then enter text and select Abstract too. Send.
12. Switch to student: selections and comments must display exactly.
13. Upload a corrected PDF or use the fictional sample; write a response; resubmit.
14. Confirm processing happens again, file version increments, previous confirmation is invalidated, and new metadata needs confirmation.
15. Confirm and switch to reviewer. The student response is visible; approve the exact current version.
16. Switch to student: Reviewer approved, NOT Submitted.
17. Return to reviewer; Submit to repository with Simulate failure checked.
18. Student must show publication needs attention, never successful submission.
19. Reviewer enters investigation notes and retries with failure unchecked.
20. Student now shows Submitted with a clearly simulated item identifier and printable receipt.

## Real local PDF

1. Reset demo records. Choose a non-confidential PDF rather than the sample.
2. Verify local preview and filename/size; submit and wait for simulated processing.
3. Title/abstract must be blank rather than copied from fictional sample metadata.
4. Enter metadata manually and confirm; reviewer PDF must be the chosen document.
5. Switch fields: the UI must state source coordinates are unavailable, not claim AI-backed source highlights.
6. Refresh; confirm metadata persists and PDF reloads from IndexedDB.
7. Download original and compare to chosen file.
8. DOCX should be downloadable and explicitly not previewable.
9. Empty file, wrong extension or over-50 MB file must show an error.

## Follow-up after publication

1. Request follow-up adjustment on a Submitted record.
2. Check the old publication remains in history.
3. Complete student resubmission and reviewer approval.
4. Publication must remain blocked until reviewer records manual deletion confirmation and reference.
5. Publish again; check earlier and new publication versions are both retained.

## Navigation, persistence and accessibility

- Filter queue by search, faculty, department, date range and status; these are not permission restrictions.
- View notifications for each role; mark read; open associated submission.
- View history; export JSON; print success receipt.
- Open a second tab at the SAME URL, choose the other demo role and confirm updates appear after mutations.
- Keyboard Tab/Shift+Tab should stay inside open modals; Escape should close them and restore focus.
- At narrow mobile widths, verify no essential controls disappear and panels stack.
- Test blocked browser storage and unavailable files: error messages should be actionable.
- Log out; only local demo records should remain, never API passwords or bearer tokens.
- Reset warning must clearly disclose that file blobs require browser site-data clearing.

## API authentication checkpoint

- Implement/enable the provided development auth backend and configure its CORS origin.
- Select API authentication mode, enter the development credentials.
- Expect login then /auth/me network requests, a checkpoint screen, and no silent demo fallback.
- Wrong credentials should show a backend error. Missing server/CORS should show a network error.
- Log out should call /auth/logout and clear local in-memory token.
- Verify frontend demo role switching is not available in API mode.

Not yet automated: JSX/build verification, rendered component tests, browser tests, network integration tests and accessibility audit. Workflow tests alone are not full application verification.
