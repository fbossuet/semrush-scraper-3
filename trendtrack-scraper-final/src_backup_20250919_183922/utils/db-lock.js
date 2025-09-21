import fs from 'fs';
import path from 'path';

/**
 * Module de gestion de lock fichier pour accès concurrent à une base SQLite.
 * Usage :
 *   await acquireLock(lockFilePath)
 *   ... accès à la base ...
 *   await releaseLock(lockFilePath)
 */

/**
 * Acquiert le lock (attend si déjà pris). Timeout configurable.
 * @param {string} lockFilePath - Chemin du fichier de lock
 * @param {object} [options]
 * @param {number} [options.retryDelay=500] - Délai ms entre tentatives
 * @param {number} [options.maxRetries=40] - Nombre max de tentatives (par défaut 20s)
 * @throws {Error} si timeout
 */
export async function acquireLock(lockFilePath, options = {}) {
  const retryDelay = options.retryDelay || 500;
  const maxRetries = options.maxRetries || 40;
  let retries = 0;
  while (fs.existsSync(lockFilePath)) {
    if (retries++ > maxRetries) {
      const err = new Error('Timeout: lock file still present');
      err.code = 'LOCK_UNAVAILABLE';
      throw err;
    }
    await new Promise(res => setTimeout(res, retryDelay));
  }
  fs.writeFileSync(lockFilePath, String(process.pid));
}

/**
 * Libère le lock (supprime le fichier de lock)
 * @param {string} lockFilePath
 */
export async function releaseLock(lockFilePath) {
  if (fs.existsSync(lockFilePath)) {
    try {
      fs.unlinkSync(lockFilePath);
    } catch (e) {
      // Peut déjà être supprimé
    }
  }
} 