import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 50,
  duration: '1m',
  thresholds: {
    'http_req_failed': ['rate<0.01'], // fail if >1% errors
    'http_req_duration': ['p(95)<500'] // p95 < 500ms
  }
};

export default function () {
  const url = 'http://web:5000/users'; // update path as needed
  let res = http.get(url);
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}