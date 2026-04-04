import http from 'k6/http';
import { check, sleep } from 'k6';

// Allow overriding VUs via the VUS environment variable (e.g. VUS=100)
const DEFAULT_VUS = 50;
const vus = (typeof __ENV !== 'undefined' && __ENV.VUS) ? (parseInt(__ENV.VUS, 10) || DEFAULT_VUS) : DEFAULT_VUS;

export let options = {
  vus: vus,
  duration: '1m',
  thresholds: {
    'http_req_failed': ['rate<0.01'], // fail if >1% errors
    'http_req_duration': ['p(95)<500'] // p95 < 500ms
  }
};

export default function () {
  const url = 'http://nginx:80/users'; // update path as needed
  let res = http.get(url);
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}