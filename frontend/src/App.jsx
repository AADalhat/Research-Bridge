import React, { useEffect, useState } from 'react';
import { auth, setToken, setUnauthorizedHandler } from './lib/api';
import { Card, ErrorBox, Field, Notice } from './components/UI';
import SubmissionUpload from './components/SubmissionUpload';

// Preserve the approved shell and CSS. All former simulated processing,
// publication timers, fake receipt creation and sample upload bypasses are gone.
export default function App() {
  const [session, setSession] = useState(null);
  const [view, setView] = useState('submission');
  const [message, setMessage] = useState('');
  const [loggingOut, setLoggingOut] = useState(false);
  const [uploadKey, setUploadKey] = useState(0);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setToken(null);
      setSession(null);
      setView('submission');
      setMessage('Your session expired or was invalidated. Please sign in again.');
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  async function logout() {
    // Capture the bearer token in the outgoing logout request before unmounting
    // the workspace; its cleanup immediately aborts upload/polling requests.
    setLoggingOut(true);
    const request = auth.logout();
    setSession(null);
    setView('submission');
    try {
      await request;
    } catch {
      setMessage('Signed out locally. Server logout could not be confirmed.');
    } finally {
      setToken(null);
      setLoggingOut(false);
    }
  }

  return (
    <>
      <div className="demo">Research Bridge · Basic PDF verification</div>
      <header>
        <div className="brand">
          <div className="logo" aria-hidden="true">RB</div>
          <div>
            <b>Research Bridge</b>
            <small>AHMADU BELLO UNIVERSITY, ZARIA<br />Research Submission &amp; Review Portal</small>
          </div>
        </div>
        {session && (
          <div className="topactions">
            <button className="small" onClick={() => setView('notifications')}>Notifications</button>
            <button className="small" onClick={() => setView('profile')}>Profile</button>
            <div className="identity">
              <strong>{session.full_name}</strong>
              <small>{session.registration_number} · {session.role}</small>
            </div>
            <button className="small" onClick={logout} disabled={loggingOut}>
              {loggingOut ? 'Logging out…' : 'Log out'}
            </button>
          </div>
        )}
      </header>

      {!session ? (
        <Login
          message={message}
          disabled={loggingOut}
          onLogin={(user) => {
            setSession(user);
            setMessage('');
            setView('submission');
          }}
        />
      ) : (
        <div className="layout">
          <aside>
            <div className="sidetitle">
              {session.role === 'student' ? 'Project Submission' : 'Project Review'}
            </div>
            <div className="sidebody">
              <div className="caps">
                {session.role === 'student' ? 'YOUR WORKSPACE' : 'REVIEWER WORKSPACE'}
              </div>
              <div className="stack">
                <button
                  className={view === 'submission' ? 'step active' : 'step'}
                  onClick={() => setView('submission')}
                >
                  {session.role === 'student' ? 'My submission' : 'Submission queue'}
                </button>
              </div>

              {/* Restore the student submission-progress indicator. */}
              {session.role === 'student' && (
                <>
                  <br />
                  <div className="caps">SUBMISSION PROGRESS</div>
                  {[
                    ['uploaded', 'Document received'],
                    ['processing', 'Processing'],
                    ['completed', 'Ready'],
                    ['failed', 'Needs attention'],
                  ].map(([key, label]) => (
                    <div className="step" key={key}>{label}</div>
                  ))}
                </>
              )}
            </div>
          </aside>

          <main>
            {view === 'profile' && (
              <Card title="Account Information">
                <dl>
                  <dt>Name</dt><dd>{session.full_name}</dd>
                  <dt>Identifier</dt><dd>{session.registration_number}</dd>
                  <dt>Role</dt><dd>{session.role}</dd>
                </dl>
              </Card>
            )}
            {view === 'notifications' && (
              <Card title="Notifications">
                <p>No notification endpoint is connected for this milestone.</p>
              </Card>
            )}
            {session.role === 'student' ? (
              // Keep the upload component mounted during top-bar navigation so
              // its local preview and accepted submission ID are not lost.
              <div hidden={view !== 'submission'}>
                <SubmissionUpload key={session.user_id + ':' + uploadKey} />
                <div className="actions">
                  <button
                    onClick={() => {
                      if (window.confirm('Clear this local view? This stops status checking but does not cancel or delete the backend submission.')) {
                        setUploadKey((value) => value + 1);
                      }
                    }}
                  >
                    Clear local view / choose another PDF
                  </button>
                </div>
              </div>
            ) : (
              view === 'submission' && (
                <Card title="Submission Queue">
                  <Notice>
                    No reviewer queue endpoint was supplied. Real reviewer records are not loaded and no sample records or approvals are generated.
                  </Notice>
                </Card>
              )
            )}
            <footer>Research Bridge · Basic file verification</footer>
          </main>
        </div>
      )}
    </>
  );
}

function Login({ onLogin, message, disabled }) {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');

    try {
      const result = await auth.login(identifier, password);
      const user = await auth.me();
      if (user.user_id !== result.user?.user_id) {
        throw new Error('The authenticated account does not match the login response.');
      }
      if (!['student', 'reviewer'].includes(user.role)) {
        throw new Error('Unsupported account role.');
      }
      onLogin(user);
    } catch (failure) {
      setToken(null);
      setError(
        failure.status === 401
          ? 'Invalid registration number or password.'
          : failure.message,
      );
    } finally {
      setBusy(false);
      setPassword('');
    }
  }

  return (
    <div className="login">
      <Card title="Research Bridge · Sign In">
        <h1>Welcome back</h1>
        <p>Your research. One connected journey.</p>
        <form onSubmit={submit}>
          <Field label="Registration number / Staff ID">
            <input
              required
              autoComplete="username"
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
            />
          </Field>
          <Field label="Password">
            <input
              required
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </Field>
          <ErrorBox>{error || message}</ErrorBox>
          <div className="actions">
            <button className="primary" style={{ width: '100%' }} disabled={busy || disabled}>
              {busy ? 'Signing in…' : 'Sign in'}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
}
