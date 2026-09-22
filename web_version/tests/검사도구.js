// 외부 라이브러리 없이 쓰는 아주 작은 검사 도구

const 등록된_검사 = [];

/** 검사를 등록합니다. 함수가 문자열을 돌려주면 결과 옆에 메모로 표시합니다. */
export function 검사(이름, 함수) {
  등록된_검사.push({ 이름, 함수 });
}

/** 조건이 거짓이면 실패시킵니다. */
export function 확인(조건, 메시지) {
  if (!조건) throw new Error(메시지);
}

/** 두 숫자 배열이 원소마다 허용 오차 안에서 같은지 확인합니다. */
export function 근사같음(실제, 기대, 오차 = 1e-6, 설명 = "") {
  if (실제.length !== 기대.length) {
    throw new Error(`${설명} 길이가 다릅니다: ${실제.length} ≠ ${기대.length}`);
  }
  for (let 위치 = 0; 위치 < 기대.length; 위치++) {
    if (!(Math.abs(실제[위치] - 기대[위치]) <= 오차)) {
      throw new Error(`${설명}[${위치}] 값이 다릅니다: ${실제[위치]} ≠ ${기대[위치]} (허용 오차 ${오차})`);
    }
  }
}

/** 등록된 검사를 차례로 실행하고 결과를 화면에 표시합니다. */
export async function 모두_실행(목록요소, 요약요소) {
  const 결과 = { 통과: 0, 실패: 0, 실패목록: [], 메모: [] };
  for (const { 이름, 함수 } of 등록된_검사) {
    const 항목 = document.createElement("li");
    try {
      const 메모 = await 함수();
      결과.통과++;
      항목.className = "통과";
      항목.textContent = `✅ ${이름}${메모 ? ` — ${메모}` : ""}`;
      if (메모) 결과.메모.push(`${이름}: ${메모}`);
    } catch (오류) {
      결과.실패++;
      결과.실패목록.push(`${이름}: ${오류.message}`);
      항목.className = "실패";
      항목.textContent = `❌ ${이름} — ${오류.message}`;
      console.error(이름, 오류);
    }
    목록요소.appendChild(항목);
  }
  요약요소.textContent = `통과 ${결과.통과}개, 실패 ${결과.실패}개`;
  요약요소.className = 결과.실패 ? "실패" : "통과";
  return 결과;
}
