/**
 * CacheService — encapsulates the in-memory cache as an instance.
 * Replaces the former module-level globalCache mutable variable.
 */
class CacheService {
  constructor() {
    this._store = {};
  }

  set(key, value) {
    this._store[key] = value;
  }

  get(key) {
    return this._store[key];
  }

  has(key) {
    return Object.prototype.hasOwnProperty.call(this._store, key);
  }
}

// Export a singleton instance — controlled lifetime, not a naked module global
module.exports = new CacheService();
