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
      value.published_revision_sequence_by_platform !== null &&
      typeof value.published_revision_sequence_by_platform === 'object' &&
      !Array.isArray(value.published_revision_sequence_by_platform) &&
      ['android', 'ios', 'web'].every(platform => {
        const available = value.published_revision_sequence_by_platform[platform];
        return Number.isSafeInteger(available) && available >= 0 &&
               available <= value.current_revision_sequence;
      }) &&
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

  function platform() {
    // iOS supplies both the WK message bridge and a NativeLaw compatibility
    // bridge. Test the WK identity first so it is not mistaken for Android.
    if (root.webkit?.messageHandlers?.lawReader) return 'ios';
    if (root.NativeLaw) return 'android';
    return 'web';
  }

  function drawNotice(remote, local) {
    const banner = document.getElementById('law-update-banner');
    if (!banner || local === null || !validManifest(remote) ||
        remote.current_revision_sequence <= local) return false;
    const detail = document.getElementById('law-update-detail');
    const link = document.getElementById('law-update-releases');
    const channel = platform();
    const available = remote.published_revision_sequence_by_platform[channel] >=
                      remote.current_revision_sequence;
    if (detail) {
      const iso = remote.law_text_last_amended_on;
      const date = iso.slice(8, 10) + '.' + iso.slice(5, 7) + '.' + iso.slice(0, 4);
      const revision = ' מהדורת הנוסח המקומית: ' + local +
                       '; המהדורה הנדרשת: ' + remote.current_revision_sequence +
                       '; מועד השינוי: ' + date + '.';
      detail.textContent = (available
        ? 'נמצא נוסח חוק מעודכן יותר מזה שמותקן כאן. חובה לעדכן כדי להסתמך על הנוסח העדכני.'
        : 'נמצא שינוי בנוסח החוק, אך מהדורה תואמת למכשיר זה טרם פורסמה. אין להסתמך על הנוסח המותקן כנוסח עדכני.') + revision;
    }
    if (link) {
      // Remote JSON can never select a link or an executable download.
      link.href = channel === 'web'
        ? 'https://sargon17-green.github.io/consumer-law-reader/reader/' : RELEASES;
      link.textContent = channel === 'web'
        ? 'בדיקת מהדורה מעודכנת באתר' : 'בדיקת מהדורות מעודכנות ב־GitHub';
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
