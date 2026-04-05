import http from 'k6/http';
import { check, sleep } from 'k6';

// Allow overriding VUs via the VUS environment variable (e.g. VUS=100)
const DEFAULT_VUS = 50;
const vus = (typeof __ENV !== 'undefined' && __ENV.VUS) ? (parseInt(__ENV.VUS, 10) || DEFAULT_VUS) : DEFAULT_VUS;

export let options = {
  vus: vus,
  duration: '1m',
  thresholds: {
    'http_req_failed': ['rate<0.05'],
    'http_req_duration': ['p(95)<1000']
  }
};

const BASE = 'http://nginx:80';

export function setup() {
  const res = http.get(`${BASE}/urls`);
  const codes = JSON.parse(res.body)
    .filter(u => u.is_active)
    .map(u => u.short_code);
  if (codes.length === 0) throw new Error('No active URLs in seed data');
  return { codes };
}

export default function (data) {
  const code = data.codes[Math.floor(Math.random() * data.codes.length)];
  const res = http.get(`${BASE}/${code}`, { redirects: 0 });
  check(res, { 'status is 301': (r) => r.status === 301 });
  sleep(1);
}
