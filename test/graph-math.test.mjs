import { test } from "node:test";
import assert from "node:assert/strict";
import { components, bounds, clampBox, rectOverlap } from "../src/runtime/graph-math.ts";

test("components 는 이어진 노드를 같은 번호로, 끊긴 노드를 다른 번호로 묶는다", () => {
  const comp = components(["a", "b", "c", "d", "e"], [["a", "b"], ["b", "c"], ["d", "e"]]);
  assert.equal(comp.get("a"), comp.get("b"));
  assert.equal(comp.get("b"), comp.get("c"));
  assert.equal(comp.get("d"), comp.get("e"));
  assert.notEqual(comp.get("a"), comp.get("d"));
});

test("components 는 링크가 없는 노드를 혼자인 덩어리로 둔다", () => {
  const comp = components(["x", "y"], []);
  assert.notEqual(comp.get("x"), comp.get("y"));
  assert.equal(comp.size, 2);
});

test("components 는 모르는 id 가 든 간선을 무시한다", () => {
  const comp = components(["a"], [["a", "ghost"]]);
  assert.equal(comp.size, 1);
});

test("bounds 는 캔버스 중심 기준으로 scale 배 상자를 준다", () => {
  assert.deepEqual(bounds(800, 400, 2), { minX: -400, maxX: 1200, minY: -200, maxY: 600 });
  assert.deepEqual(bounds(800, 400, 1), { minX: 0, maxX: 800, minY: 0, maxY: 400 });
});

test("clampBox 는 값을 [min, max] 안으로 자른다", () => {
  assert.equal(clampBox(-999, -400, 1200), -400);
  assert.equal(clampBox(5000, -400, 1200), 1200);
  assert.equal(clampBox(10, -400, 1200), 10);
});

test("rectOverlap 은 여백을 포함해 겹친 두 사각형을 작은 겹침 축으로 민다", () => {
  const a = { minX: 0, maxX: 100, minY: 0, maxY: 40 };
  const b = { minX: 90, maxX: 200, minY: 0, maxY: 40 };
  const r = rectOverlap(a, b, 0);
  assert.equal(r.axis, "x");            // x 겹침 10 < y 겹침 40
  assert.equal(r.amount, 10);
  assert.equal(r.sign, -1);             // a 가 왼쪽이면 a 는 -x 로
});

test("rectOverlap 은 떨어져 있으면 null, 여백이 있으면 여백만큼 더 겹친다", () => {
  const a = { minX: 0, maxX: 100, minY: 0, maxY: 40 };
  const b = { minX: 120, maxX: 200, minY: 0, maxY: 40 };
  assert.equal(rectOverlap(a, b, 0), null);
  const r = rectOverlap(a, b, 15);       // 양쪽 여백 15 -> 30 > 틈 20
  assert.equal(r.axis, "x");
  assert.equal(r.amount, 10);
});

test("rectOverlap 은 세로 겹침이 작으면 y 축으로 민다", () => {
  const a = { minX: 0, maxX: 100, minY: 0, maxY: 40 };
  const b = { minX: 0, maxX: 100, minY: 35, maxY: 80 };
  const r = rectOverlap(a, b, 0);
  assert.equal(r.axis, "y"); assert.equal(r.amount, 5); assert.equal(r.sign, -1);
});
