/* Read-only GitHub law-text revision check. The bundled law remains usable offline. */
(function (root) {
  'use strict';
  const URL = 'https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/metadata/law_update_manifest.json';
  const RELEASES = 'https://github.com/Sargon17-Green/consumer-law-reader/releases';
  const KEY = 'law-reader-last-confirmed-revision-v1';
  const LAW = 'israel-consumer-protection-law-1981';
  let installed = false, pending = null;
  const document = root.document;

  function isoDate(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const year = Number(value.slice(0, 4)), month = Number(value.slice(5, 7)),
          day = Number(value.slice(8, 10));
    if (year < 1900 || year > 9999 || month < 1 || month > 12 || day < 1) return false;
    const d = new Date(Date.UTC(year, month - 1, day));
    return d.getUTCFullYear() === year && d.getUTCMonth() === month - 1 && d.getUTCDate() === day;
  }

  function validManifest(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value) &&
      value.schema_version === 1 && value.law_id === LAW &&
      value.revision_status === 'editor_approved' &&
      Number.isSafeInteger(value.current_revision_sequence) &&
      value.current_revision_sequence >= 1 && value.current_revision_sequence <= 1000000 &&
      Number.isSafeInteger(value.published_revision_sequence) &&
      value.published_revision_sequence >= 1 &&
      value.published_revision_sequence <= value.current_revision_sequence &&
      isoDate(value.law_text_last_amended_on) &&
      isoDate(value.law_text_last_verified_on) &&
      (value.next_scheduled_change_on === null || isoDate(value.next_scheduled_change_on));
  }

  function localRevision() {
    try {
      const status = JSON.parse(document.getElementById('law-editorial-status')?.textContent || '{}');
      return status.law_id === LAW && Number.isSafeInteger(status.law_revision_sequence) &&
        status.law_revision_sequence >= 1 && status.law_revision_sequence <= 1000000
        ? status.law_revision_sequence : null;
    } catch (_) { return null; }
  }

  function remembered() {
    try {
      const raw = root.localStorage.getItem(KEY);
      if (!raw) return null;
      const data = JSON.parse(raw);
      return validManifest(data) ? data : null;
    } catch (_) { return null; }
  }

  function remember(data) {
    try { root.localStorage.setItem(KEY, JSON.stringify(data)); } catch (_) {
      // Storage may be disabled; keep the current launch's warning anyway.
    }
  }

  function drawNotice(remote, local) {
    const banner = document.getElementById('law-update-banner');
    if (!banner || local === null || !validManifest(remote) ||
        remote.current_revision_sequence <= local) return false;
    const detail = document.getElementById('law-update-detail');
    const link = document.getElementById('law-update-releases');
    if (detail) {
      detail.textContent = remote.published_revision_sequence >= remote.current_revision_sequence
        ? 'נמצא נוסח חוק מעודכן יותר מזה שמותקן כאן. כדי להסתמך על הנוסח העדכני, יש להתקין מהדורה חדשה.'
        : 'נמצא שינוי בנוסח החוק, אך מהדורה תואמת טרם פורסמה. אין להסתמך על הנוסח המותקן כנוסח עדכני.';
    }
    if (link) {
      link.href = RELEASES; // Never trust an executable/download URL from remote JSON.
      link.textContent = 'בדיקת מהדורות מעודכנות ב־GitHub';
    }
    banner.hidden = false;
    return true;
  }

  async function check() {
    if (pending) return pending;
    const local = localRevision();
    if (local === null || typeof root.fetch !== 'function') return false;
    const cached = remembered();
    if (cached) drawNotice(cached, local);
    pending = (async () => {
      const abort = new AbortController();
      const timer = root.setTimeout(() => abort.abort(), 6000);
      try {
        const response = await root.fetch(URL + '?_t=' + Date.now(), {
          method: 'GET', mode: 'cors', credentials: 'omit', cache: 'no-store',
          referrerPolicy: 'no-referrer', signal: abort.signal
        });
        if (!response.ok) return false;
        const raw = await response.text();
        if (raw.length > 4096) return false;
        const remote = JSON.parse(raw);
        if (!validManifest(remote)) return false;
        // A previously confirmed newer revision must not be suppressed by a
        // transient stale CDN response or an offline/erroneous rollback.
        const newest = cached && cached.current_revision_sequence > remote.current_revision_sequence
          ? cached : remote;
        remember(newest);
        return drawNotice(newest, local);
      } catch (_) {
        // Never prevent offline reading or claim that a failed query is current.
        return false;
      } finally {
        root.clearTimeout(timer);
      }
    })();
    try { return await pending; } finally { pending = null; }
  }

  function install() {
    if (installed) return;
    installed = true;
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') void check();
    });
    root.addEventListener('pageshow', event => {
      if (event.persisted) void check();
    });
    void check();
  }

  root.LawUpdate = { install, check, validManifest, localRevision };
})(window);
