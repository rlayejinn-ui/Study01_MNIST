// 검사 모듈을 불러와 모두 실행하고, 결과를 window.검사결과 에 담습니다.
import { 검사, 모두_실행 } from "./검사도구.js";

// 새 검사 파일을 만들면 여기에 추가합니다.
const 검사_모듈 = ["./연산_검사.js", "./모델_검사.js", "./전처리_검사.js"];

for (const 경로 of 검사_모듈) {
  try {
    await import(경로);
  } catch (오류) {
    // 모듈을 불러오지 못한 것도 실패로 보여 줍니다.
    검사(`${경로} 불러오기`, () => {
      throw 오류;
    });
  }
}

window.검사결과 = await 모두_실행(
  document.getElementById("결과목록"),
  document.getElementById("요약"),
);
