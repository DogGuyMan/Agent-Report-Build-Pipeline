// <include file="docs/codegraph/comments.xml" path="//term[@id='VerdictFooter.tsx']"/>
// 수용 판정 기입란 조각이 있는 파일. 값은 사람이 채운다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// <include file="docs/codegraph/comments.xml" path="//term[@id='VerdictFooter']"/>
// 수용 판정 기입란. 승인 · 보류 · 번복 세 칸과 사유 줄이 있다.
// 쓰는 것: 없음 · 쓰이는 곳: 없음
// src/components/VerdictFooter.tsx
// 수용 판정 푸터 — 이 블록의 값은 AI 가 채우지 않는다. 사용자 기입 전용.
export function VerdictFooter({ note }: { note?: string }) {
  return (
    <div className="verdict-footer">
      <div className="choices">
        <span className="choice"><span className="box" />승인</span>
        <span className="choice"><span className="box" />보류</span>
        <span className="choice"><span className="box" />번복</span>
      </div>
      <div className="reason-line">사유 —</div>
      <div className="owner-note">
        {note ?? "이 칸은 사용자가 직접 채운다. 에이전트가 판정을 대신 기입하지 않는다."}
      </div>
    </div>
  );
}
