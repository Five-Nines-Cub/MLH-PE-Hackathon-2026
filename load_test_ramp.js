import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'http://64.23.146.45:8080';

export let options = {
  stages: [
    { duration: '20s', target: 500 },   // ramp up
    { duration: '30s', target: 1500 },  // push to peak
    { duration: '10s', target: 0 },     // ramp down
  ],
  thresholds: {
    'http_req_failed': ['rate<0.10'],
    'http_req_duration': ['p(95)<3000'],
  },
};

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
