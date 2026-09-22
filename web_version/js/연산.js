// 신경망 추론에 필요한 수치 연산 (외부 라이브러리 없음)
// 모든 배열은 Float32Array 이고 배치 순서는 PyTorch 와 같은 [채널][높이][너비] 입니다.
// 입력은 바꾸지 않고 항상 새 배열을 돌려줍니다.

/**
 * 3x3 합성곱 (패딩 1, 보폭 1 → 출력 크기 = 입력 크기)
 * 가중치 배치: [출력채널][입력채널][3][3]
 */
export function 합성곱3x3(입력, 입력채널, 높이, 너비, 가중치, 편향, 출력채널) {
  const 면적 = 높이 * 너비;
  const 출력 = new Float32Array(출력채널 * 면적);
  for (let 출 = 0; 출 < 출력채널; 출++) {
    const 출력기준 = 출 * 면적;
    출력.fill(편향[출], 출력기준, 출력기준 + 면적);
    for (let 입 = 0; 입 < 입력채널; 입++) {
      const 입력기준 = 입 * 면적;
      const 커널기준 = (출 * 입력채널 + 입) * 9;
      for (let ky = 0; ky < 3; ky++) {
        const dy = ky - 1;
        // 입력 좌표 (y+dy) 가 범위 안에 드는 y 만 계산 (바깥은 0 패딩)
        const y시작 = Math.max(0, -dy);
        const y끝 = Math.min(높이, 높이 - dy);
        for (let kx = 0; kx < 3; kx++) {
          const dx = kx - 1;
          const 값 = 가중치[커널기준 + ky * 3 + kx];
          if (값 === 0) continue;
          const x시작 = Math.max(0, -dx);
          const x끝 = Math.min(너비, 너비 - dx);
          for (let y = y시작; y < y끝; y++) {
            const 입력행 = 입력기준 + (y + dy) * 너비 + dx;
            const 출력행 = 출력기준 + y * 너비;
            for (let x = x시작; x < x끝; x++) {
              출력[출력행 + x] += 값 * 입력[입력행 + x];
            }
          }
        }
      }
    }
  }
  return 출력;
}

/** ReLU: 음수를 0으로 */
export function 렐루(입력) {
  const 출력 = new Float32Array(입력.length);
  for (let 위치 = 0; 위치 < 입력.length; 위치++) {
    출력[위치] = 입력[위치] > 0 ? 입력[위치] : 0;
  }
  return 출력;
}

/** 2x2 최대풀링 (보폭 2) → 크기가 절반이 됩니다 */
export function 최대풀링2x2(입력, 채널, 높이, 너비) {
  const 새높이 = 높이 >> 1;
  const 새너비 = 너비 >> 1;
  const 출력 = new Float32Array(채널 * 새높이 * 새너비);
  for (let 채 = 0; 채 < 채널; 채++) {
    const 입력기준 = 채 * 높이 * 너비;
    const 출력기준 = 채 * 새높이 * 새너비;
    for (let y = 0; y < 새높이; y++) {
      for (let x = 0; x < 새너비; x++) {
        const 왼위 = 입력기준 + 2 * y * 너비 + 2 * x;
        출력[출력기준 + y * 새너비 + x] = Math.max(
          입력[왼위], 입력[왼위 + 1], 입력[왼위 + 너비], 입력[왼위 + 너비 + 1],
        );
      }
    }
  }
  return 출력;
}

/** 완전연결: 출력 = 가중치 · 입력 + 편향, 가중치 배치: [출력][입력] */
export function 완전연결(입력, 가중치, 편향, 출력수) {
  const 입력수 = 입력.length;
  const 출력 = new Float32Array(출력수);
  for (let 출 = 0; 출 < 출력수; 출++) {
    const 행기준 = 출 * 입력수;
    let 합 = 편향[출];
    for (let 입 = 0; 입 < 입력수; 입++) {
      합 += 가중치[행기준 + 입] * 입력[입];
    }
    출력[출] = 합;
  }
  return 출력;
}

/** 소프트맥스: 로짓을 확률로 (가장 큰 값을 빼서 넘침을 막습니다) */
export function 소프트맥스(로짓) {
  let 최대 = -Infinity;
  for (const 값 of 로짓) 최대 = Math.max(최대, 값);
  const 출력 = new Float32Array(로짓.length);
  let 합 = 0;
  for (let 위치 = 0; 위치 < 로짓.length; 위치++) {
    출력[위치] = Math.exp(로짓[위치] - 최대);
    합 += 출력[위치];
  }
  for (let 위치 = 0; 위치 < 출력.length; 위치++) 출력[위치] /= 합;
  return 출력;
}

/** 가장 큰 값의 위치 (같은 값이 여럿이면 앞쪽) */
export function 최댓값_위치(배열) {
  let 최고 = 0;
  for (let 위치 = 1; 위치 < 배열.length; 위치++) {
    if (배열[위치] > 배열[최고]) 최고 = 위치;
  }
  return 최고;
}
