/**
 * @param {string} pathname
 * @returns {boolean}
 */
export function isAuthPath(pathname) {
  const normalized = pathname === '/' ? pathname : pathname.replace(/\/+$/, '');
  return normalized === '/login' || normalized === '/register';
}
